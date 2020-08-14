import pytest
from django.contrib.auth.models import Permission
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient


@pytest.fixture
def testuser_john_doe(django_user_model):
    return django_user_model.objects.create(username="john", password="doe")


@pytest.fixture
def testuser_jane_canrent(django_user_model):
    jane = django_user_model.objects.create(username="jane", password="canrent")
    can_add_rent_permission = Permission.objects.get(name="Can add rent")
    jane.user_permissions.add(can_add_rent_permission)
    return jane


@pytest.fixture
def testuser_mary_maintain(django_user_model):
    mary = django_user_model.objects.create(username="mary", password="maintain")
    can_maintain_permission = Permission.objects.get(name="Can use maintainance UI")
    mary.user_permissions.add(can_maintain_permission)
    return mary


@pytest.fixture
def user_client_john_doe_logged_in(testuser_john_doe):
    client = APIClient()
    token, _ = Token.objects.get_or_create(user=testuser_john_doe)
    client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
    return client


@pytest.fixture
def user_client_jane_canrent_logged_in(testuser_jane_canrent):
    client = APIClient()
    token, _ = Token.objects.get_or_create(user=testuser_jane_canrent)
    client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
    return client


@pytest.fixture
def user_client_mary_maintain_logged_in(testuser_mary_maintain):
    client = APIClient()
    token, _ = Token.objects.get_or_create(user=testuser_mary_maintain)
    client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
    return client


@pytest.mark.django_db
def test_get_map_no_user():
    client = APIClient()
    response = client.get("/api/maintenance/mapdata")
    assert response.status_code == 401


@pytest.mark.django_db
def test_get_map_logged_in_default_user(user_client_john_doe_logged_in):
    response = user_client_john_doe_logged_in.get("/api/maintenance/mapdata")
    assert response.status_code == 403


@pytest.mark.django_db
def test_get_map_logged_in_default_user_with_renting_rights(
    user_client_jane_canrent_logged_in,
):
    response = user_client_jane_canrent_logged_in.get("/api/maintenance/mapdata")
    assert response.status_code == 403


@pytest.mark.django_db
def test_get_map_logged_in_default_user_with_maintain_rights(
    user_client_mary_maintain_logged_in,
):
    response = user_client_mary_maintain_logged_in.get("/api/maintenance/mapdata")
    assert response.status_code == 200
