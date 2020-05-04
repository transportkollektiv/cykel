import pytest
from rest_framework.test import APIClient
from rest_framework_api_key.models import APIKey
from bikesharing.models import Location, LocationTracker

# TODO: move into conftest.py
@pytest.fixture
def tracker_client_with_apikey():
    client = APIClient()
    api_key, key = APIKey.objects.create_key(name="test-tracker")
    client.credentials(HTTP_AUTHORIZATION='Api-Key ' + key)
    return client

@pytest.fixture
def tracker():
    return LocationTracker.objects.create(device_id=42)

@pytest.mark.django_db
def test_tracker_updatebikelocation_without_device_id(tracker, tracker_client_with_apikey):
    response = tracker_client_with_apikey.post('/api/bike/updatelocation')
    assert response.status_code == 400, response.content
    assert response.json()['error'] == 'device_id missing'

