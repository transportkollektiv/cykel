import pytest
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

@pytest.fixture
def testuser_john_doe(django_user_model):
    return django_user_model.objects.create(username="john", password="doe")

@pytest.fixture
def user_client_john_doe_logged_in(testuser_john_doe):
    client = APIClient()
    token, _ = Token.objects.get_or_create(user=testuser_john_doe)
    client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
    return client

@pytest.mark.django_db
def test_userdata(testuser_john_doe, user_client_john_doe_logged_in):
    response = user_client_john_doe_logged_in.get('/api/user')
    assert response.status_code == 200, response.content
    assert response.json()['username'] == "john"
    assert response.json()['can_rent_bike'] == False