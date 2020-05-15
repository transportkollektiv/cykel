import pytest
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import Permission
from bikesharing.models import Bike, Lock

@pytest.fixture
def testuser_john_doe(django_user_model):
    return django_user_model.objects.create(username="john", password="doe")

@pytest.fixture
def user_client_john_doe_logged_in(testuser_john_doe):
    client = APIClient()
    token, _ = Token.objects.get_or_create(user=testuser_john_doe)
    client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
    return client

@pytest.fixture
def lock():
    return Lock.objects.create(unlock_key='000000')

@pytest.fixture
def available_bike(lock):
    return Bike.objects.create(availability_status='AV', bike_number='1337', lock=lock)

@pytest.fixture
def disabled_bike():
    return Bike.objects.create(availability_status='DI', bike_number='2342')

@pytest.fixture
def inuse_bike():
    return Bike.objects.create(availability_status='IU', bike_number='8080')


@pytest.mark.django_db
def test_start_rent_logged_in_without_renting_rights(testuser_john_doe, user_client_john_doe_logged_in, available_bike):
    data = {
        'bike_number': '1337'
    }
    response = user_client_john_doe_logged_in.post('/api/rent/start', data)
    assert response.status_code == 403, response.content
    available_bike.refresh_from_db()
    assert available_bike.availability_status == 'AV'

@pytest.mark.django_db
def test_start_rent_logged_out(available_bike):
    data = {
        'bike_number': '1337'
    }
    client = APIClient()
    response = client.post('/api/rent/start', data)
    assert response.status_code == 401, response.content
    available_bike.refresh_from_db()
    assert available_bike.availability_status == 'AV'

@pytest.mark.django_db
def test_start_rent_logged_in_with_renting_rights(testuser_john_doe, user_client_john_doe_logged_in, available_bike):
    can_add_rent_permission = Permission.objects.get(name='Can add rent')
    testuser_john_doe.user_permissions.add(can_add_rent_permission)
    data = {
        'bike_number': '1337'
    }
    response = user_client_john_doe_logged_in.post('/api/rent/start', data)
    assert response.status_code == 200, response.content
    assert response.json()['success'] == True
    assert response.json()['unlock_key'] == '000000'

    available_bike.refresh_from_db()
    assert available_bike.availability_status == 'IU'
