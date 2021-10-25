import pytest
from django.contrib.auth.models import Permission
from django.contrib.gis.geos import Point
from django.utils.timezone import now
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from bikesharing.models import Bike, Location, Lock, LockType, Rent, VehicleType


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
def testuser_mary_canrent(django_user_model):
    mary = django_user_model.objects.create(username="mary", password="canrent")
    can_add_rent_permission = Permission.objects.get(name="Can add rent")
    mary.user_permissions.add(can_add_rent_permission)
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
def user_client_mary_canrent_logged_in(testuser_mary_canrent):
    client = APIClient()
    token, _ = Token.objects.get_or_create(user=testuser_mary_canrent)
    client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
    return client


@pytest.fixture
def lock_type_combination():
    return LockType.objects.create(form_factor=LockType.FormFactor.COMBINATION_LOCK)


@pytest.fixture
def lock(lock_type_combination):
    return Lock.objects.create(unlock_key="000000", lock_type=lock_type_combination)


@pytest.fixture
def another_lock(lock_type_combination):
    return Lock.objects.create(unlock_key="000000", lock_type=lock_type_combination)


@pytest.fixture
def available_bike(lock):
    vehicle_type = VehicleType.objects.create(allow_spontaneous_rent=True)
    return Bike.objects.create(
        availability_status=Bike.Availability.AVAILABLE,
        bike_number="1337",
        lock=lock,
        vehicle_type=vehicle_type,
    )


@pytest.fixture
def bike_not_allowed_for_spontaneous_rents(lock):
    vehicle_type = VehicleType.objects.create(allow_spontaneous_rent=False)
    return Bike.objects.create(
        availability_status=Bike.Availability.AVAILABLE,
        bike_number="1337",
        lock=lock,
        vehicle_type=vehicle_type,
    )


@pytest.fixture
def disabled_bike():
    return Bike.objects.create(
        availability_status=Bike.Availability.DISABLED, bike_number="2342"
    )


@pytest.fixture
def inuse_bike(another_lock):
    return Bike.objects.create(
        availability_status=Bike.Availability.IN_USE,
        bike_number="8080",
        lock=another_lock,
    )


@pytest.fixture
def rent_jane_running(testuser_jane_canrent, inuse_bike):
    return Rent.objects.create(
        rent_start=now(),
        user=testuser_jane_canrent,
        bike=inuse_bike,
    )


@pytest.mark.django_db
def test_get_rents_logged_in_with_renting_rights(
    testuser_jane_canrent, user_client_jane_canrent_logged_in, rent_jane_running
):
    response = user_client_jane_canrent_logged_in.get("/api/rent")
    assert response.status_code == 200, response.content
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == rent_jane_running.id
    assert (
        response.json()[0]["bike"]["bike_number"] == rent_jane_running.bike.bike_number
    )


@pytest.mark.django_db
def test_start_rent_logged_in_without_renting_rights(
    testuser_john_doe, user_client_john_doe_logged_in, available_bike
):
    data = {"bike": available_bike.bike_number}
    response = user_client_john_doe_logged_in.post("/api/rent", data)
    assert response.status_code == 403, response.content
    available_bike.refresh_from_db()
    assert available_bike.availability_status == Bike.Availability.AVAILABLE


@pytest.mark.django_db
def test_start_rent_logged_out(available_bike):
    data = {"bike": available_bike.bike_number}
    client = APIClient()
    response = client.post("/api/rent", data)
    assert response.status_code == 401, response.content
    available_bike.refresh_from_db()
    assert available_bike.availability_status == Bike.Availability.AVAILABLE


@pytest.mark.django_db
def test_start_rent_logged_in_with_renting_rights(
    testuser_jane_canrent, user_client_jane_canrent_logged_in, available_bike
):
    data = {"bike": available_bike.bike_number}
    response = user_client_jane_canrent_logged_in.post("/api/rent", data)
    assert response.status_code == 201, response.content

    available_bike.refresh_from_db()
    assert available_bike.availability_status == Bike.Availability.IN_USE


@pytest.mark.django_db
def test_start_rent_and_unlock_logged_in_with_renting_rights(
    testuser_jane_canrent, user_client_jane_canrent_logged_in, available_bike
):
    data = {"bike": available_bike.bike_number}
    response = user_client_jane_canrent_logged_in.post("/api/rent", data)
    assert response.status_code == 201, response.content

    unlock_url = response.json()["unlock_url"]
    response = user_client_jane_canrent_logged_in.post(unlock_url)
    assert response.status_code == 200, response.content
    assert response.json()["data"]["unlock_key"] == "000000"


@pytest.mark.django_db
def test_start_rent_inuse_bike_logged_in_with_renting_rights(
    testuser_jane_canrent, user_client_jane_canrent_logged_in, inuse_bike
):
    data = {"bike": inuse_bike.bike_number}
    response = user_client_jane_canrent_logged_in.post("/api/rent", data)
    assert response.status_code == 400, response.content


@pytest.mark.django_db
def test_start_rent_other_inuse_bike_logged_in_with_renting_rights(
    testuser_mary_canrent,
    user_client_mary_canrent_logged_in,
    rent_jane_running,
    inuse_bike,
):
    data = {"bike": inuse_bike.bike_number}
    response = user_client_mary_canrent_logged_in.post("/api/rent", data)
    assert response.status_code == 400, response.content


@pytest.mark.django_db
def test_start_rent_unknown_bike_logged_in_with_renting_rights(
    testuser_jane_canrent, user_client_jane_canrent_logged_in
):
    data = {"bike": 404}
    response = user_client_jane_canrent_logged_in.post("/api/rent", data)
    assert response.status_code == 400, response.content


@pytest.mark.django_db
def test_start_rent_no_spontaneous_rents_logged_in_with_renting_rights(
    testuser_jane_canrent,
    user_client_jane_canrent_logged_in,
    bike_not_allowed_for_spontaneous_rents,
):
    data = {"bike": bike_not_allowed_for_spontaneous_rents.bike_number}
    response = user_client_jane_canrent_logged_in.post("/api/rent", data)
    assert response.status_code == 400, response.content

    bike_not_allowed_for_spontaneous_rents.refresh_from_db()
    assert (
        bike_not_allowed_for_spontaneous_rents.availability_status
        == Bike.Availability.AVAILABLE
    )


@pytest.mark.django_db
def test_start_rent_logged_in_with_renting_rights_and_location_from_client(
    testuser_jane_canrent, user_client_jane_canrent_logged_in, available_bike
):
    data = {"bike": available_bike.bike_number, "lat": -99.99, "lng": -89.99}
    response = user_client_jane_canrent_logged_in.post("/api/rent", data)
    assert response.status_code == 201, response.content

    rent_id = response.json()["id"]

    available_bike.refresh_from_db()
    assert available_bike.availability_status == Bike.Availability.IN_USE

    rent = Rent.objects.get(id=rent_id)
    assert rent.start_location is not None
    assert rent.start_location.geo.x == -89.99
    assert rent.start_location.geo.y == -99.99


@pytest.mark.django_db
def test_end_rent_logged_in_with_renting_rights(
    testuser_jane_canrent,
    user_client_jane_canrent_logged_in,
    rent_jane_running,
    inuse_bike,
):
    data = {}
    response = user_client_jane_canrent_logged_in.post(
        "/api/rent/{}/finish".format(rent_jane_running.id), data
    )
    assert response.status_code == 200, response.content
    assert response.json()["success"] is True

    rent_jane_running.refresh_from_db()
    assert rent_jane_running.rent_end is not None

    inuse_bike.refresh_from_db()
    assert inuse_bike.availability_status == Bike.Availability.AVAILABLE


@pytest.mark.django_db
def test_end_rent_logged_in_with_renting_rights_and_location_from_bike(
    testuser_jane_canrent,
    user_client_jane_canrent_logged_in,
    rent_jane_running,
    inuse_bike,
):
    loc = Location.objects.create(
        bike=inuse_bike, source=Location.Source.TRACKER, reported_at=now()
    )
    loc.geo = Point(-89.99, -99.99, srid=4326)
    loc.save()

    data = {}
    response = user_client_jane_canrent_logged_in.post(
        "/api/rent/{}/finish".format(rent_jane_running.id), data
    )
    assert response.status_code == 200, response.content

    rent_jane_running.refresh_from_db()
    assert rent_jane_running.rent_end is not None
    assert rent_jane_running.end_location is not None
    assert rent_jane_running.end_location.geo.x == -89.99
    assert rent_jane_running.end_location.geo.y == -99.99

    inuse_bike.refresh_from_db()
    assert inuse_bike.availability_status == Bike.Availability.AVAILABLE
    assert inuse_bike.public_geolocation().source == Location.Source.TRACKER
    assert inuse_bike.public_geolocation().geo.x == -89.99
    assert inuse_bike.public_geolocation().geo.y == -99.99


@pytest.mark.django_db
def test_end_rent_logged_in_with_renting_rights_and_location_from_client(
    testuser_jane_canrent,
    user_client_jane_canrent_logged_in,
    rent_jane_running,
    inuse_bike,
):
    data = {"lat": -99.99, "lng": -89.99}
    response = user_client_jane_canrent_logged_in.post(
        "/api/rent/{}/finish".format(rent_jane_running.id), data
    )
    assert response.status_code == 200, response.content
    assert response.json()["success"] is True

    rent_jane_running.refresh_from_db()
    assert rent_jane_running.rent_end is not None
    assert rent_jane_running.end_location is not None
    assert rent_jane_running.end_location.geo.x == -89.99
    assert rent_jane_running.end_location.geo.y == -99.99

    inuse_bike.refresh_from_db()
    assert inuse_bike.availability_status == Bike.Availability.AVAILABLE
    assert inuse_bike.public_geolocation().source == Location.Source.USER
    assert inuse_bike.public_geolocation().geo.x == -89.99
    assert inuse_bike.public_geolocation().geo.y == -99.99


@pytest.mark.django_db
def test_end_rent_logged_out(
    rent_jane_running,
    inuse_bike,
):
    client = APIClient()
    data = {}
    response = client.post("/api/rent/{}/finish".format(rent_jane_running.id), data)
    assert response.status_code == 401, response.content

    rent_jane_running.refresh_from_db()
    assert rent_jane_running.rent_end is None

    inuse_bike.refresh_from_db()
    assert inuse_bike.availability_status == Bike.Availability.IN_USE


@pytest.mark.django_db
def test_end_rent_unknown_logged_in_with_renting_rights(
    testuser_jane_canrent,
    user_client_jane_canrent_logged_in,
):
    data = {}
    response = user_client_jane_canrent_logged_in.post(
        "/api/rent/{}/finish".format(99), data
    )
    assert response.status_code == 404, response.content
