"""
Locust scenarios for the GIMAO backend API.

Environment variables:
- LOCUST_HOST=http://localhost:8000
- LOCUST_WAIT_MIN=1
- LOCUST_WAIT_MAX=3
- LOCUST_REQUEST_TIMEOUT=20
- LOCUST_READ_ONLY=true|false
- LOCUST_USERNAME / LOCUST_PASSWORD (shared fallback for all roles)
- LOCUST_RESPONSABLE_USERNAME / LOCUST_RESPONSABLE_PASSWORD
- LOCUST_TECHNICIEN_USERNAME / LOCUST_TECHNICIEN_PASSWORD
- LOCUST_MAGASINIER_USERNAME / LOCUST_MAGASINIER_PASSWORD
- LOCUST_OPERATEUR_USERNAME / LOCUST_OPERATEUR_PASSWORD
"""

from __future__ import annotations

import logging
import os
import random
import time
from typing import Any

from locust import HttpUser, between, task
from locust.exception import StopUser

LOGGER = logging.getLogger(__name__)


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


WAIT_MIN = env_float("LOCUST_WAIT_MIN", 1.0)
WAIT_MAX = env_float("LOCUST_WAIT_MAX", 3.0)
REQUEST_TIMEOUT = env_float("LOCUST_REQUEST_TIMEOUT", 20.0)
READ_ONLY = env_bool("LOCUST_READ_ONLY", True)
DEFAULT_HOST = os.getenv("LOCUST_HOST")
EQUIPMENT_STATUSES = (
    "EN_FONCTIONNEMENT",
    "DEGRADE",
    "A_LARRET",
    "HORS_SERVICE",
)


def get_credentials(username_env: str, password_env: str) -> tuple[str, str]:
    username = os.getenv(username_env, os.getenv("LOCUST_USERNAME", "")).strip()
    password = os.getenv(password_env, os.getenv("LOCUST_PASSWORD", "")).strip()
    return username, password


def role_is_enabled(username_env: str, password_env: str) -> bool:
    username, password = get_credentials(username_env, password_env)
    return bool(username and password)


class AuthenticatedApiUser(HttpUser):
    abstract = True
    host = DEFAULT_HOST
    wait_time = between(WAIT_MIN, WAIT_MAX)

    role_label = "generic"
    username_env = ""
    password_env = ""

    def on_start(self) -> None:
        self.random = random.Random(f"{time.time()}-{self.role_label}-{id(self)}")
        self.token: str | None = None
        self.user_id: int | None = None
        self.username, self.password = get_credentials(self.username_env, self.password_env)
        self.cache: dict[str, list[int]] = {
            "equipements": [],
            "demandes": [],
            "demandes_pending": [],
            "bons": [],
            "consommables": [],
            "magasins": [],
            "utilisateurs": [],
            "roles": [],
        }

        if not self.username or not self.password:
            raise StopUser()

        self.login()

    def auth_headers(self) -> dict[str, str]:
        if not self.token:
            return {}
        return {"Authorization": f"Bearer {self.token}"}

    def metric_name(self, name: str) -> str:
        role_prefix = self.role_label.replace("_", " ").title()
        return f"{role_prefix} | {name}"

    def api_request(
        self,
        method: str,
        path: str,
        *,
        name: str,
        expected_status: tuple[int, ...] = (200,),
        authenticated: bool = True,
        **kwargs: Any,
    ) -> tuple[Any, Any]:
        headers = dict(kwargs.pop("headers", {}))
        if authenticated:
            headers.update(self.auth_headers())

        with self.client.request(
            method,
            path,
            name=self.metric_name(name),
            headers=headers,
            catch_response=True,
            timeout=REQUEST_TIMEOUT,
            **kwargs,
        ) as response:
            if response.status_code not in expected_status:
                response.failure(
                    f"{name} returned {response.status_code}, expected {expected_status}"
                )
                return response, None

            payload = None
            if response.text:
                try:
                    payload = response.json()
                except ValueError:
                    response.failure(f"{name} returned a non-JSON response")
                    return response, None

            return response, payload

    def login(self) -> None:
        _, payload = self.api_request(
            "POST",
            "/api/utilisateurs/login/",
            name="Auth/Login",
            authenticated=False,
            expected_status=(200,),
            json={
                "nomUtilisateur": self.username,
                "motDePasse": self.password,
            },
        )
        if not isinstance(payload, dict):
            raise StopUser()

        token = payload.get("token")
        user = payload.get("utilisateur") or {}
        user_id = user.get("id")
        if not token or not user_id:
            LOGGER.warning(
                "Locust login for '%s' did not return a token and user payload.",
                self.role_label,
            )
            raise StopUser()

        self.token = str(token)
        self.user_id = int(user_id)

    @staticmethod
    def extract_items(payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if isinstance(payload, dict):
            results = payload.get("results")
            if isinstance(results, list):
                return [item for item in results if isinstance(item, dict)]
            data = payload.get("data")
            if isinstance(data, list):
                return [item for item in data if isinstance(item, dict)]
        return []

    def remember_ids(self, key: str, items: list[dict[str, Any]]) -> list[int]:
        ids = [int(item["id"]) for item in items if item.get("id") is not None]
        if ids:
            self.cache[key] = ids
        return ids

    def remember_demandes(self, items: list[dict[str, Any]]) -> list[int]:
        ids = self.remember_ids("demandes", items)
        pending_ids = [
            int(item["id"])
            for item in items
            if item.get("id") is not None and item.get("statut") == "EN_ATTENTE"
        ]
        if pending_ids:
            self.cache["demandes_pending"] = pending_ids
        return ids

    def pick_cached_id(self, key: str) -> int | None:
        ids = self.cache.get(key) or []
        if not ids:
            return None
        return int(self.random.choice(ids))

    def list_equipements(
        self,
        *,
        params: dict[str, Any] | None = None,
        name: str = "Equipement/List",
    ) -> list[dict[str, Any]]:
        _, payload = self.api_request("GET", "/api/equipements/", name=name, params=params)
        items = self.extract_items(payload)
        self.remember_ids("equipements", items)
        return items

    def list_demandes(
        self,
        *,
        path: str = "/api/demandes-intervention/",
        params: dict[str, Any] | None = None,
        name: str = "DI/List",
    ) -> list[dict[str, Any]]:
        _, payload = self.api_request("GET", path, name=name, params=params)
        items = self.extract_items(payload)
        self.remember_demandes(items)
        return items

    def list_bons_travail(
        self,
        *,
        params: dict[str, Any] | None = None,
        name: str = "BT/List",
    ) -> list[dict[str, Any]]:
        _, payload = self.api_request("GET", "/api/bons-travail/", name=name, params=params)
        items = self.extract_items(payload)
        self.remember_ids("bons", items)
        return items

    def list_consumables(
        self,
        *,
        params: dict[str, Any] | None = None,
        name: str = "Stock/Consommable List",
    ) -> list[dict[str, Any]]:
        _, payload = self.api_request("GET", "/api/consommables/", name=name, params=params)
        items = self.extract_items(payload)
        self.remember_ids("consommables", items)
        return items

    def list_magasins(
        self,
        *,
        params: dict[str, Any] | None = None,
        name: str = "Stock/Magasin List",
    ) -> list[dict[str, Any]]:
        _, payload = self.api_request("GET", "/api/magasins/", name=name, params=params)
        items = self.extract_items(payload)
        self.remember_ids("magasins", items)
        return items

    def list_utilisateurs(self, *, name: str = "User/List") -> list[dict[str, Any]]:
        _, payload = self.api_request("GET", "/api/utilisateurs/", name=name)
        items = self.extract_items(payload)
        self.remember_ids("utilisateurs", items)
        return items

    def list_roles(self, *, name: str = "User/Role List") -> list[dict[str, Any]]:
        _, payload = self.api_request("GET", "/api/roles/", name=name)
        items = self.extract_items(payload)
        self.remember_ids("roles", items)
        return items

    def get_equipment_id(self) -> int | None:
        equipment_id = self.pick_cached_id("equipements")
        if equipment_id:
            return equipment_id
        items = self.list_equipements()
        if not items:
            return None
        return self.pick_cached_id("equipements")

    def get_demande_id(self) -> int | None:
        demande_id = self.pick_cached_id("demandes")
        if demande_id:
            return demande_id
        items = self.list_demandes()
        if not items:
            return None
        return self.pick_cached_id("demandes")

    def get_pending_demande_id(self) -> int | None:
        demande_id = self.pick_cached_id("demandes_pending")
        if demande_id:
            return demande_id
        items = self.list_demandes(
            path="/api/demandes-intervention/en_attente/",
            name="DI/List Pending",
        )
        if not items:
            return None
        return self.pick_cached_id("demandes_pending")

    def get_bon_id(self) -> int | None:
        bon_id = self.pick_cached_id("bons")
        if bon_id:
            return bon_id
        items = self.list_bons_travail()
        if not items:
            return None
        return self.pick_cached_id("bons")

    def get_consumable_id(self) -> int | None:
        consumable_id = self.pick_cached_id("consommables")
        if consumable_id:
            return consumable_id
        items = self.list_consumables()
        if not items:
            return None
        return self.pick_cached_id("consommables")

    def get_magasin_id(self) -> int | None:
        magasin_id = self.pick_cached_id("magasins")
        if magasin_id:
            return magasin_id
        items = self.list_magasins()
        if not items:
            return None
        return self.pick_cached_id("magasins")

    def maybe_create_di(self, *, name: str = "DI/Create") -> int | None:
        if READ_ONLY or self.user_id is None:
            return None

        equipment_id = self.get_equipment_id()
        if equipment_id is None:
            return None

        _, payload = self.api_request(
            "POST",
            "/api/demandes-intervention/",
            name=name,
            expected_status=(201,),
            json={
                "nom": f"Locust DI {self.role_label} {int(time.time() * 1000)}",
                "commentaire": "Generated by Locust for performance benchmarking.",
                "statut_suppose": self.random.choice(EQUIPMENT_STATUSES),
                "utilisateur_id": self.user_id,
                "equipement_id": equipment_id,
            },
        )
        if not isinstance(payload, dict) or payload.get("id") is None:
            return None

        demande_id = int(payload["id"])
        self.cache["demandes"].append(demande_id)
        self.cache["demandes_pending"].append(demande_id)
        return demande_id

    def maybe_traiter_demande(self) -> None:
        if READ_ONLY:
            return
        demande_id = self.get_pending_demande_id()
        if demande_id is None:
            return
        self.api_request(
            "POST",
            f"/api/demandes-intervention/{demande_id}/traiter/",
            name="DI/Traiter",
            expected_status=(200,),
        )

    def maybe_update_demande_status(self) -> None:
        if READ_ONLY:
            return
        demande_id = self.get_pending_demande_id()
        if demande_id is None:
            return
        self.api_request(
            "PATCH",
            f"/api/demandes-intervention/{demande_id}/updateStatus/",
            name="DI/Update Status",
            expected_status=(200,),
            json={"statut": "ACCEPTEE"},
        )

    def maybe_transfer_stock(self) -> None:
        if READ_ONLY:
            return

        consumable_id = self.get_consumable_id()
        if consumable_id is None:
            return

        _, payload = self.api_request(
            "GET",
            f"/api/consommables/{consumable_id}/",
            name="Stock/Consommable Detail",
            expected_status=(200,),
        )
        if not isinstance(payload, dict):
            return

        stocks = payload.get("stocks") or []
        if not isinstance(stocks, list):
            return

        source_candidates = [
            stock
            for stock in stocks
            if isinstance(stock, dict) and int(stock.get("quantite") or 0) > 0
        ]
        if not source_candidates:
            return

        source_stock = self.random.choice(source_candidates)
        source_magasin = source_stock.get("magasin")
        if source_magasin is None:
            return

        self.list_magasins(name="Stock/Magasin List Ordered", params={"ordering": "nom"})
        destination_candidates = [
            magasin_id
            for magasin_id in self.cache.get("magasins", [])
            if magasin_id != int(source_magasin)
        ]
        if not destination_candidates:
            return

        self.api_request(
            "POST",
            f"/api/consommables/{consumable_id}/transfer_stock/",
            name="Stock/Transfer",
            expected_status=(200,),
            json={
                "from_magasin": int(source_magasin),
                "transfers": [
                    {
                        "to_magasin": int(self.random.choice(destination_candidates)),
                        "quantite": 1,
                    }
                ],
            },
        )


class ResponsableGmaoUser(AuthenticatedApiUser):
    abstract = not role_is_enabled(
        "LOCUST_RESPONSABLE_USERNAME",
        "LOCUST_RESPONSABLE_PASSWORD",
    )
    role_label = "responsable"
    username_env = "LOCUST_RESPONSABLE_USERNAME"
    password_env = "LOCUST_RESPONSABLE_PASSWORD"
    weight = 4

    @task(6)
    def dashboard_stats(self) -> None:
        if self.user_id is None:
            return
        self.api_request(
            "GET",
            "/api/stats/",
            name="Dashboard/Stats",
            params={"userId": self.user_id},
        )

    @task(5)
    def demandes_list(self) -> None:
        self.list_demandes()

    @task(3)
    def demandes_pending(self) -> None:
        self.list_demandes(
            path="/api/demandes-intervention/en_attente/",
            name="DI/List Pending",
        )

    @task(2)
    def demandes_traitees(self) -> None:
        self.list_demandes(
            path="/api/demandes-intervention/traitees/",
            name="DI/List Processed",
        )

    @task(3)
    def demandes_by_equipment(self) -> None:
        equipment_id = self.get_equipment_id()
        if equipment_id is None:
            return
        self.list_demandes(
            path="/api/demandes-intervention/par_equipement/",
            name="DI/List By Equipment",
            params={"equipement_id": equipment_id},
        )

    @task(3)
    def demande_detail(self) -> None:
        demande_id = self.get_demande_id()
        if demande_id is None:
            return
        self.api_request(
            "GET",
            f"/api/demandes-intervention/{demande_id}/",
            name="DI/Detail",
        )

    @task(5)
    def bons_travail_list(self) -> None:
        self.list_bons_travail()

    @task(3)
    def bon_travail_detail(self) -> None:
        bon_id = self.get_bon_id()
        if bon_id is None:
            return
        self.api_request(
            "GET",
            f"/api/bons-travail/{bon_id}/",
            name="BT/Detail",
        )

    @task(2)
    def bon_travail_stock_list(self) -> None:
        self.api_request(
            "GET",
            "/api/bons-travail/list_stock/",
            name="BT/List Stock",
        )

    @task(4)
    def equipements_list(self) -> None:
        self.list_equipements()

    @task(2)
    def equipement_display_lite(self) -> None:
        equipment_id = self.get_equipment_id()
        if equipment_id is None:
            return
        self.api_request(
            "GET",
            f"/api/equipement/{equipment_id}/affichage/",
            name="Equipement/Display Detail Lite",
            params={"seuils_lite": "true"},
        )

    @task(2)
    def equipement_display_full(self) -> None:
        equipment_id = self.get_equipment_id()
        if equipment_id is None:
            return
        self.api_request(
            "GET",
            f"/api/equipement/{equipment_id}/affichage/",
            name="Equipement/Display Detail Full",
        )

    @task(2)
    def equipement_form_data(self) -> None:
        self.api_request(
            "GET",
            "/api/equipements/form-data/",
            name="Equipement/Form Data",
        )

    @task(2)
    def user_admin_lists(self) -> None:
        self.list_utilisateurs()
        self.list_roles()
        self.api_request("GET", "/api/permissions/", name="User/Permission List")

    @task(1)
    def create_demande(self) -> None:
        self.maybe_create_di()

    @task(1)
    def traiter_demande(self) -> None:
        self.maybe_traiter_demande()

    @task(1)
    def update_demande_status(self) -> None:
        self.maybe_update_demande_status()


class TechnicienUser(AuthenticatedApiUser):
    abstract = not role_is_enabled(
        "LOCUST_TECHNICIEN_USERNAME",
        "LOCUST_TECHNICIEN_PASSWORD",
    )
    role_label = "technicien"
    username_env = "LOCUST_TECHNICIEN_USERNAME"
    password_env = "LOCUST_TECHNICIEN_PASSWORD"
    weight = 3

    @task(5)
    def dashboard_stats(self) -> None:
        if self.user_id is None:
            return
        self.api_request(
            "GET",
            "/api/stats/",
            name="Dashboard/Stats",
            params={"userId": self.user_id},
        )

    @task(5)
    def bons_travail_list(self) -> None:
        self.list_bons_travail()

    @task(4)
    def bon_travail_detail(self) -> None:
        bon_id = self.get_bon_id()
        if bon_id is None:
            return
        self.api_request(
            "GET",
            f"/api/bons-travail/{bon_id}/",
            name="BT/Detail",
        )

    @task(2)
    def bon_travail_stock_list(self) -> None:
        self.api_request(
            "GET",
            "/api/bons-travail/list_stock/",
            name="BT/List Stock",
        )

    @task(3)
    def mes_demandes(self) -> None:
        if self.user_id is None:
            return
        self.list_demandes(
            path="/api/demandes-intervention/par_utilisateur/",
            name="DI/List By User",
            params={"utilisateur_id": self.user_id},
        )

    @task(4)
    def equipements_list(self) -> None:
        self.list_equipements()

    @task(3)
    def equipement_display_lite(self) -> None:
        equipment_id = self.get_equipment_id()
        if equipment_id is None:
            return
        self.api_request(
            "GET",
            f"/api/equipement/{equipment_id}/affichage/",
            name="Equipement/Display Detail Lite",
            params={"seuils_lite": "true"},
        )

    @task(2)
    def equipement_display_full(self) -> None:
        equipment_id = self.get_equipment_id()
        if equipment_id is None:
            return
        self.api_request(
            "GET",
            f"/api/equipement/{equipment_id}/affichage/",
            name="Equipement/Display Detail Full",
        )


class MagasinierUser(AuthenticatedApiUser):
    abstract = not role_is_enabled(
        "LOCUST_MAGASINIER_USERNAME",
        "LOCUST_MAGASINIER_PASSWORD",
    )
    role_label = "magasinier"
    username_env = "LOCUST_MAGASINIER_USERNAME"
    password_env = "LOCUST_MAGASINIER_PASSWORD"
    weight = 2

    @task(6)
    def consommables_list(self) -> None:
        self.list_consumables()

    @task(4)
    def consommables_search(self) -> None:
        self.list_consumables(
            name="Stock/Consommable Search",
            params={"search": "a", "ordering": "designation"},
        )

    @task(3)
    def consommable_detail(self) -> None:
        consumable_id = self.get_consumable_id()
        if consumable_id is None:
            return
        self.api_request(
            "GET",
            f"/api/consommables/{consumable_id}/",
            name="Stock/Consommable Detail",
        )

    @task(4)
    def magasins_list(self) -> None:
        self.list_magasins(name="Stock/Magasin List Ordered", params={"ordering": "nom"})

    @task(2)
    def transfer_stock(self) -> None:
        self.maybe_transfer_stock()


class OperateurUser(AuthenticatedApiUser):
    abstract = not role_is_enabled(
        "LOCUST_OPERATEUR_USERNAME",
        "LOCUST_OPERATEUR_PASSWORD",
    )
    role_label = "operateur"
    username_env = "LOCUST_OPERATEUR_USERNAME"
    password_env = "LOCUST_OPERATEUR_PASSWORD"
    weight = 2

    @task(4)
    def dashboard_stats(self) -> None:
        if self.user_id is None:
            return
        self.api_request(
            "GET",
            "/api/stats/",
            name="Dashboard/Stats",
            params={"userId": self.user_id},
        )

    @task(5)
    def equipements_list(self) -> None:
        self.list_equipements()

    @task(3)
    def equipement_display_lite(self) -> None:
        equipment_id = self.get_equipment_id()
        if equipment_id is None:
            return
        self.api_request(
            "GET",
            f"/api/equipement/{equipment_id}/affichage/",
            name="Equipement/Display Detail Lite",
            params={"seuils_lite": "true"},
        )

    @task(4)
    def mes_demandes(self) -> None:
        if self.user_id is None:
            return
        self.list_demandes(
            path="/api/demandes-intervention/par_utilisateur/",
            name="DI/List By User",
            params={"utilisateur_id": self.user_id},
        )

    @task(3)
    def demande_detail(self) -> None:
        demande_id = self.get_demande_id()
        if demande_id is None:
            return
        self.api_request(
            "GET",
            f"/api/demandes-intervention/{demande_id}/",
            name="DI/Detail",
        )

    @task(2)
    def create_demande(self) -> None:
        self.maybe_create_di()


ENABLED_ROLES = [
    role_name
    for role_name, enabled in [
        ("responsable", not ResponsableGmaoUser.abstract),
        ("technicien", not TechnicienUser.abstract),
        ("magasinier", not MagasinierUser.abstract),
        ("operateur", not OperateurUser.abstract),
    ]
    if enabled
]

if not ENABLED_ROLES:
    LOGGER.warning(
        "No Locust users enabled. Configure LOCUST_USERNAME/LOCUST_PASSWORD or "
        "role-specific credentials to activate scenarios."
    )
else:
    LOGGER.info("Enabled Locust roles: %s", ", ".join(ENABLED_ROLES))


class ConfigurationErrorUser(HttpUser):
    abstract = bool(ENABLED_ROLES)
    weight = 1
    wait_time = between(1, 1)

    def on_start(self) -> None:
        LOGGER.error(
            "No Locust credentials configured. Set LOCUST_USERNAME/LOCUST_PASSWORD "
            "or role-specific credentials before starting a run."
        )
        runner = getattr(self.environment, "runner", None)
        if runner is not None:
            runner.quit()

    @task
    def noop(self) -> None:
        time.sleep(1)
