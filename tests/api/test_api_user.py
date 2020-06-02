import pytest
from django.contrib.auth.models import Permission
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient


@pytest.fixture
def testuser_john_doe(django_user_model):
    return django_user_model.objects.create(username="john", password="doe")


@pytest.fixture
def user_client_john_doe_logged_in(testuser_john_doe):
    client = APIClient()
    token, _ = Token.objects.get_or_create(user=testuser_john_doe)
    client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
    return client


@pytest.mark.django_db
def test_userdata_logged_in_without_renting_rights(
    testuser_john_doe, user_client_john_doe_logged_in
):
    response = user_client_john_doe_logged_in.get("/api/user")
    assert response.status_code == 200, response.content
    assert response.json()["username"] == "john"
    assert response.json()["can_rent_bike"] is False


@pytest.mark.django_db
def test_userdata_not_logged_in():
    client = APIClient()
    response = client.get("/api/user")
    assert response.status_code == 401, response.content


@pytest.mark.django_db
def test_userdata_logged_in_with_renting_rights(
    testuser_john_doe, user_client_john_doe_logged_in
):
    can_add_rent_permission = Permission.objects.get(name="Can add rent")
    testuser_john_doe.user_permissions.add(can_add_rent_permission)
    response = user_client_john_doe_logged_in.get("/api/user")
    assert response.status_code == 200, response.content
    assert response.json()["username"] == "john"
    assert response.json()["can_rent_bike"] is True
