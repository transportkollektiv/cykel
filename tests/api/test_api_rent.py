import datetime

import pytest
import pytz
from django.contrib.auth.models import Permission
from django.contrib.gis.geos import Point
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from bikesharing.models import Bike, Location, Lock, Rent


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
def lock():
    return Lock.objects.create(unlock_key="000000")


@pytest.fixture
def available_bike(lock):
    return Bike.objects.create(availability_status="AV", bike_number="1337", lock=lock)


@pytest.fixture
def disabled_bike():
    return Bike.objects.create(availability_status="DI", bike_number="2342")


@pytest.fixture
def inuse_bike():
    return Bike.objects.create(availability_status="IU", bike_number="8080")


@pytest.fixture
def rent_jane_running(testuser_jane_canrent, inuse_bike):
    return Rent.objects.create(
        rent_start=datetime.datetime.now(pytz.utc),
        user=testuser_jane_canrent,
        bike=inuse_bike,
    )


@pytest.mark.django_db
def test_start_rent_logged_in_without_renting_rights(
    testuser_john_doe, user_client_john_doe_logged_in, available_bike
):
    data = {"bike_number": "1337"}
    response = user_client_john_doe_logged_in.post("/api/rent/start", data)
    assert response.status_code == 403, response.content
    available_bike.refresh_from_db()
    assert available_bike.availability_status == "AV"


@pytest.mark.django_db
def test_start_rent_logged_out(available_bike):
    data = {"bike_number": "1337"}
    client = APIClient()
    response = client.post("/api/rent/start", data)
    assert response.status_code == 401, response.content
    available_bike.refresh_from_db()
    assert available_bike.availability_status == "AV"


@pytest.mark.django_db
def test_start_rent_logged_in_with_renting_rights(
    testuser_jane_canrent, user_client_jane_canrent_logged_in, available_bike
):
    data = {"bike_number": "1337"}
    response = user_client_jane_canrent_logged_in.post("/api/rent/start", data)
    assert response.status_code == 200, response.content
    assert response.json()["success"] is True
    assert response.json()["unlock_key"] == "000000"

    available_bike.refresh_from_db()
    assert available_bike.availability_status == "IU"


@pytest.mark.django_db
def test_end_rent_logged_in_with_renting_rights(
    testuser_jane_canrent,
    user_client_jane_canrent_logged_in,
    rent_jane_running,
    inuse_bike,
):
    data = {"rent_id": rent_jane_running.id}
    response = user_client_jane_canrent_logged_in.post("/api/rent/finish", data)
    assert response.status_code == 200, response.content
    assert response.json()["success"] is True

    rent_jane_running.refresh_from_db()
    assert rent_jane_running.rent_end is not None

    inuse_bike.refresh_from_db()
    assert inuse_bike.availability_status == "AV"


@pytest.mark.django_db
def test_end_rent_logged_in_with_renting_rights_and_location_from_bike(
    testuser_jane_canrent,
    user_client_jane_canrent_logged_in,
    rent_jane_running,
    inuse_bike,
):
    loc = Location.objects.create(bike=inuse_bike, source="TR")
    loc.geo = Point(-89.99, -99.99, srid=4326)
    loc.reported_at = datetime.datetime.now(pytz.utc)
    loc.save()

    data = {"rent_id": rent_jane_running.id}
    response = user_client_jane_canrent_logged_in.post("/api/rent/finish", data)
    assert response.status_code == 200, response.content
    assert response.json()["success"] is True

    rent_jane_running.refresh_from_db()
    assert rent_jane_running.rent_end is not None
    assert rent_jane_running.end_position.x == -89.99
    assert rent_jane_running.end_position.y == -99.99

    inuse_bike.refresh_from_db()
    assert inuse_bike.availability_status == "AV"
    assert inuse_bike.public_geolocation().source == "TR"
    assert inuse_bike.public_geolocation().geo.x == -89.99
    assert inuse_bike.public_geolocation().geo.y == -99.99


@pytest.mark.django_db
def test_end_rent_logged_in_with_renting_rights_and_location_from_client(
    testuser_jane_canrent,
    user_client_jane_canrent_logged_in,
    rent_jane_running,
    inuse_bike,
):
    data = {"rent_id": rent_jane_running.id, "lat": -99.99, "lng": -89.99}
    response = user_client_jane_canrent_logged_in.post("/api/rent/finish", data)
    assert response.status_code == 200, response.content
    assert response.json()["success"] is True

    rent_jane_running.refresh_from_db()
    assert rent_jane_running.rent_end is not None
    assert rent_jane_running.end_position.x == -89.99
    assert rent_jane_running.end_position.y == -99.99

    inuse_bike.refresh_from_db()
    assert inuse_bike.availability_status == "AV"
    assert inuse_bike.public_geolocation().source == "US"
    assert inuse_bike.public_geolocation().geo.x == -89.99
    assert inuse_bike.public_geolocation().geo.y == -99.99
