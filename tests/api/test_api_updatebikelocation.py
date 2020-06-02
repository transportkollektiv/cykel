import pytest
from django.contrib.gis.geos import Point
from preferences import preferences
from rest_framework.test import APIClient
from rest_framework_api_key.models import APIKey

from bikesharing.models import Bike, LocationTracker, Station


# TODO: move into conftest.py
@pytest.fixture
def tracker_client_with_apikey():
    client = APIClient()
    api_key, key = APIKey.objects.create_key(name="test-tracker")
    client.credentials(HTTP_AUTHORIZATION="Api-Key " + key)
    return client


@pytest.fixture
def available_bike():
    return Bike.objects.create(availability_status="AV", bike_number="1337")


@pytest.fixture
def active_station():
    return Station.objects.create(
        status="AC",
        station_name="Station McStationface",
        location=Point(9.99024, 48.39662, srid=4326),
    )


@pytest.fixture
def tracker(available_bike):
    return LocationTracker.objects.create(device_id=42, bike=available_bike)


@pytest.fixture
def internal_tracker():
    return LocationTracker.objects.create(device_id=23, internal=True)


@pytest.mark.django_db
def test_tracker_updatebikelocation_without_apikey(tracker):
    client = APIClient()
    data = {"device_id": tracker.device_id, "lat": 13.2455, "lng": 35.345}
    response = client.post("/api/bike/updatelocation", data=data)
    assert response.status_code == 401


@pytest.mark.django_db
def test_tracker_updatebikelocation_without_device_id(
    tracker, tracker_client_with_apikey
):
    response = tracker_client_with_apikey.post("/api/bike/updatelocation")
    assert response.status_code == 400, response.content
    assert response.json()["error"] == "device_id missing"


@pytest.mark.django_db
def test_tracker_updatebikelocation_updates_last_reported(
    tracker, tracker_client_with_apikey
):
    assert tracker.last_reported is None
    data = {"device_id": tracker.device_id}
    response = tracker_client_with_apikey.post("/api/bike/updatelocation", data=data)
    assert response.status_code == 200, response.content
    tracker.refresh_from_db()
    assert tracker.last_reported is not None


@pytest.mark.django_db
def test_tracker_updatebikelocation_updates_battery_voltage(
    tracker, tracker_client_with_apikey
):
    assert tracker.battery_voltage is None
    data = {"device_id": tracker.device_id, "battery_voltage": 3.45}
    response = tracker_client_with_apikey.post("/api/bike/updatelocation", data=data)
    assert response.status_code == 200, response.content
    tracker.refresh_from_db()
    assert tracker.battery_voltage == 3.45


@pytest.mark.django_db
def test_tracker_updatebikelocation_wants_both_parts_of_a_coordinate(
    tracker, tracker_client_with_apikey
):
    data = {"device_id": tracker.device_id, "lat": 1}
    response = tracker_client_with_apikey.post("/api/bike/updatelocation", data=data)
    assert response.status_code == 400, response.content


@pytest.mark.django_db
def test_tracker_updatebikelocation_check_current_geolocation(
    tracker, tracker_client_with_apikey
):
    data = {"device_id": tracker.device_id, "lat": -99, "lng": -89}
    response = tracker_client_with_apikey.post("/api/bike/updatelocation", data=data)
    assert response.status_code == 200, response.content
    tracker.refresh_from_db()
    assert tracker.current_geolocation().geo.y == -99
    assert tracker.current_geolocation().geo.x == -89


@pytest.mark.django_db
def test_tracker_updatebikelocation_check_public_tracker_location(
    tracker, tracker_client_with_apikey
):
    data = {"device_id": tracker.device_id, "lat": -99.9, "lng": -89.9}
    response = tracker_client_with_apikey.post("/api/bike/updatelocation", data=data)
    assert response.status_code == 200, response.content
    tracker.refresh_from_db()
    assert tracker.current_geolocation().internal is False


@pytest.mark.django_db
def test_tracker_updatebikelocation_check_internal_tracker_location(
    internal_tracker, tracker_client_with_apikey
):
    data = {"device_id": internal_tracker.device_id, "lat": -99.99, "lng": -89.99}
    response = tracker_client_with_apikey.post("/api/bike/updatelocation", data=data)
    assert response.status_code == 200, response.content
    internal_tracker.refresh_from_db()
    assert internal_tracker.current_geolocation().internal is True


@pytest.mark.django_db
def test_tracker_updatebikelocation_check_accuracy_on_location(
    tracker, tracker_client_with_apikey
):
    data = {
        "device_id": tracker.device_id,
        "lat": -99.997,
        "lng": -89.9911,
        "accuracy": 10.765,
    }
    response = tracker_client_with_apikey.post("/api/bike/updatelocation", data=data)
    assert response.status_code == 200, response.content
    tracker.refresh_from_db()
    assert tracker.current_geolocation().accuracy == 10.765


@pytest.mark.django_db
def test_tracker_updatebikelocation_check_automatic_station_assignment_under_20m(
    tracker, available_bike, active_station, tracker_client_with_apikey
):
    assert available_bike.current_station is None
    assert preferences.BikeSharePreferences.station_match_max_distance == 20
    data = {"device_id": tracker.device_id, "lat": 48.39662, "lng": 9.99026}
    response = tracker_client_with_apikey.post("/api/bike/updatelocation", data=data)
    assert response.status_code == 200, response.content
    available_bike.refresh_from_db()
    print(dir(available_bike.current_station))
    assert available_bike.current_station == active_station


@pytest.mark.django_db
def test_tracker_updatebikelocation_check_automatic_station_assignment_under_80m(
    tracker, available_bike, active_station, tracker_client_with_apikey
):
    assert available_bike.current_station is None
    prefs = preferences.BikeSharePreferences
    prefs.station_match_max_distance = 80
    prefs.save()
    assert preferences.BikeSharePreferences.station_match_max_distance == 80
    data = {"device_id": tracker.device_id, "lat": 48.39679, "lng": 9.99034}
    response = tracker_client_with_apikey.post("/api/bike/updatelocation", data=data)
    assert response.status_code == 200, response.content
    available_bike.refresh_from_db()
    assert available_bike.current_station is not None
    assert available_bike.current_station == active_station


@pytest.mark.django_db
def test_tracker_updatebikelocation_check_automatic_station_assignment_over_20m(
    tracker, available_bike, active_station, tracker_client_with_apikey
):
    assert available_bike.current_station is None
    assert preferences.BikeSharePreferences.station_match_max_distance == 20
    data = {"device_id": tracker.device_id, "lat": 48.39679, "lng": 9.99034}
    response = tracker_client_with_apikey.post("/api/bike/updatelocation", data=data)
    assert response.status_code == 200, response.content
    available_bike.refresh_from_db()
    assert available_bike.current_station is None
