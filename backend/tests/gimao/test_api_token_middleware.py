import json

import pytest
from django.test import RequestFactory

from gimao.middleware import ApiTokenMiddleware
from security.models import ApiToken, create_token
from tests.factories import UtilisateurFactory


@pytest.fixture
def request_factory():
    return RequestFactory()


@pytest.mark.django_db
def test_should_bypass_auth_for_whitelisted_route(request_factory):
    middleware = ApiTokenMiddleware(lambda request: None)
    request = request_factory.get("/api/utilisateurs/login/")

    response = middleware(request)

    assert response is None


@pytest.mark.django_db
def test_should_return_401_when_token_is_missing_for_api_route(request_factory):
    middleware = ApiTokenMiddleware(lambda request: None)
    request = request_factory.get("/api/maintenance/demandes-intervention/")

    response = middleware(request)

    assert response.status_code == 401
    assert json.loads(response.content) == {"error": "Token manquant"}


@pytest.mark.django_db
def test_should_return_401_when_token_is_invalid(request_factory):
    middleware = ApiTokenMiddleware(lambda request: None)
    request = request_factory.get(
        "/api/maintenance/demandes-intervention/",
        HTTP_AUTHORIZATION="Bearer not_a_real_token",
    )

    response = middleware(request)

    assert response.status_code == 401
    assert json.loads(response.content) == {"error": "Token invalide"}


@pytest.mark.django_db
def test_should_return_401_when_token_is_revoked(request_factory):
    user = UtilisateurFactory()
    raw_token = create_token(user)
    token = ApiToken.objects.get(user=user)
    token.is_revoked = True
    token.save(update_fields=["is_revoked"])

    middleware = ApiTokenMiddleware(lambda request: None)
    request = request_factory.get(
        "/api/maintenance/demandes-intervention/",
        HTTP_AUTHORIZATION=f"Bearer {raw_token}",
    )

    response = middleware(request)

    assert response.status_code == 401
    assert json.loads(response.content) == {"error": "Token expiré ou révoqué"}


@pytest.mark.django_db
def test_should_attach_api_user_when_token_is_valid(request_factory):
    user = UtilisateurFactory()
    raw_token = create_token(user)

    def get_response(request):
        return request.api_user.pk

    middleware = ApiTokenMiddleware(get_response)
    request = request_factory.get(
        "/api/maintenance/demandes-intervention/",
        HTTP_AUTHORIZATION=f"Bearer {raw_token}",
    )

    response = middleware(request)

    assert response == user.pk
