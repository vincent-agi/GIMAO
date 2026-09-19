import pytest

from tests.factories import UtilisateurFactory


@pytest.mark.django_db
def test_set_password_stores_hashed_value():
    """
    set_password() ne doit pas stocker le mot de passe en clair.
    """
    user = UtilisateurFactory()
    user.set_password("motdepasse_secret")

    assert user.motDePasse is not None
    assert user.motDePasse != "motdepasse_secret"


@pytest.mark.django_db
def test_check_password_returns_true_for_correct_password():
    """
    check_password() doit retourner True pour le bon mot de passe.
    """
    user = UtilisateurFactory()
    user.set_password("motdepasse_secret")

    assert user.check_password("motdepasse_secret") is True


@pytest.mark.django_db
def test_check_password_returns_false_for_wrong_password():
    """
    check_password() doit retourner False pour un mauvais mot de passe.
    """
    user = UtilisateurFactory()
    user.set_password("motdepasse_secret")

    assert user.check_password("mauvais_mot_de_passe") is False


@pytest.mark.django_db
def test_check_password_returns_false_when_no_password_set():
    """
    check_password() doit retourner False si aucun mot de passe n'est défini.
    """
    user = UtilisateurFactory()
    # motDePasse est null par défaut dans la factory

    assert user.check_password("nimporte_quoi") is False
