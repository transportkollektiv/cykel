import pytest
from django.contrib.auth.models import Permission
from django.utils.timezone import now, timedelta
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from schedule.models import Calendar, Event

from bikesharing.models import Bike, Lock, LockType, Station, VehicleType
from reservation.models import Reservation


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
def vehicle_type_reservation_allowed():
    return VehicleType.objects.create(
        allow_reservation=True, reservation_lead_time_minutes=10
    )


@pytest.fixture
def vehicle_type_reservation_forbidden():
    return VehicleType.objects.create(allow_reservation=False)


@pytest.fixture
def vehicle_type_min_spontaneous_rent_vehicle():
    return VehicleType.objects.create(
        allow_reservation=True,
        reservation_lead_time_minutes=10,
        min_spontaneous_rent_vehicles=1,
    )


@pytest.fixture
def available_bike(lock, vehicle_type_reservation_allowed):
    return Bike.objects.create(
        availability_status=Bike.Availability.AVAILABLE,
        bike_number="1337",
        lock=lock,
        vehicle_type=vehicle_type_reservation_allowed,
    )


@pytest.fixture
def disabled_bike():
    return Bike.objects.create(
        availability_status=Bike.Availability.DISABLED, bike_number="2342"
    )


@pytest.fixture
def start_station():
    return Station.objects.create(
        station_name="Teststation",
        status=Station.Status.ACTIVE,
    )


@pytest.fixture
def reservation_jane_running(
    testuser_jane_canrent, vehicle_type_reservation_allowed, start_station
):
    calendar = Calendar.objects.create(
        name="Reservations",
        slug="reservations",
    )

    event = Event.objects.create(
        title="Reservation",
        start=now(),
        end=now(),
        calendar=calendar,
        creator=testuser_jane_canrent,
    )

    return Reservation.objects.create(
        creator=testuser_jane_canrent,
        vehicle_type=vehicle_type_reservation_allowed,
        event=event,
        start_location=start_station,
    )


@pytest.mark.django_db
def test_get_reservations_logged_in_with_reservation_rights(
    user_client_jane_canrent_logged_in, reservation_jane_running
):
    response = user_client_jane_canrent_logged_in.get("/api/reservation")
    assert response.status_code == 200, response.content
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == reservation_jane_running.id
    assert (
        response.json()[0]["vehicle_type"]["name"]
        == reservation_jane_running.vehicle_type.name
    )


@pytest.mark.django_db
def test_start_reservation_logged_in_without_reservation_rights(
    user_client_john_doe_logged_in,
):
    data = {}
    response = user_client_john_doe_logged_in.post("/api/reservation", data)
    assert response.status_code == 403, response.content


@pytest.mark.django_db
def test_start_reservation_logged_out():
    data = {}
    client = APIClient()
    response = client.post("/api/reservation", data)
    assert response.status_code == 401, response.content


@pytest.mark.django_db
def test_start_reservation_logged_in_with_reservation_rights(
    testuser_jane_canrent,
    user_client_jane_canrent_logged_in,
    vehicle_type_reservation_allowed,
    start_station,
    available_bike,
):
    start_date = now()
    start_date_string = start_date.strftime("%Y-%m-%dT%H:%M")
    end_date = start_date + timedelta(days=2)
    end_date_string = end_date.strftime("%Y-%m-%dT%H:%M")
    data = {
        "startDate": start_date_string,
        "endDate": end_date_string,
        "startStationId": start_station.id,
        "vehicleTypeId": vehicle_type_reservation_allowed.id,
    }
    response = user_client_jane_canrent_logged_in.post("/api/reservation", data)
    assert response.status_code == 201, response.content
    assert (
        response.json()["vehicle_type"]["name"] == vehicle_type_reservation_allowed.name
    )
    assert (
        response.json()["event"]["start"] == start_date.isoformat()
    )
    assert response.json()["event"]["end"] == end_date.isoformat()
    assert response.json()["event"]["creator"] == testuser_jane_canrent


@pytest.mark.django_db
def test_start_multiple_reservations_logged_in_with_reservation_rights(
    user_client_jane_canrent_logged_in,
    vehicle_type_reservation_allowed,
    start_station,
    available_bike,
):
    start_date = now()
    end_date = start_date + timedelta(days=2)
    data = {
        "startDate": start_date.strftime("%Y-%m-%dT%H:%M"),
        "endDate": end_date.strftime("%Y-%m-%dT%H:%M"),
        "startStationId": start_station.id,
        "vehicleTypeId": vehicle_type_reservation_allowed.id,
    }
    response = user_client_jane_canrent_logged_in.post("/api/reservation", data)
    assert response.status_code == 201, response.content

    # overlapping reservation (including lead time) can not be created
    # (only one bike can be reserved)
    start_date_overlapping = end_date
    end_date_overlapping = start_date_overlapping + timedelta(days=1)
    data_overlapping = {
        "startDate": start_date_overlapping.strftime("%Y-%m-%dT%H:%M"),
        "endDate": end_date_overlapping.strftime("%Y-%m-%dT%H:%M"),
        "startStationId": start_station.id,
        "vehicleTypeId": vehicle_type_reservation_allowed.id,
    }
    response = user_client_jane_canrent_logged_in.post(
        "/api/reservation", data_overlapping
    )
    assert response.status_code == 400, response.content

    # not overlapping reservation can be created
    start_date_new = end_date + timedelta(
        minutes=vehicle_type_reservation_allowed.reservation_lead_time_minutes + 1
    )
    end_date_new = start_date_new + timedelta(days=1)
    data_new = {
        "startDate": start_date_new.strftime("%Y-%m-%dT%H:%M"),
        "endDate": end_date_new.strftime("%Y-%m-%dT%H:%M"),
        "startStationId": start_station.id,
        "vehicleTypeId": vehicle_type_reservation_allowed.id,
    }
    response = user_client_jane_canrent_logged_in.post("/api/reservation", data_new)
    assert response.status_code == 201, response.content


@pytest.mark.django_db
def test_start_reservation_min_rent_vehicles_logged_in_with_reservation_rights(
    user_client_jane_canrent_logged_in,
    vehicle_type_min_spontaneous_rent_vehicle,
    start_station,
    available_bike,
):
    start_date = now()
    end_date = start_date + timedelta(days=2)
    data = {
        "startDate": start_date.strftime("%Y-%m-%dT%H:%M"),
        "endDate": end_date.strftime("%Y-%m-%dT%H:%M"),
        "startStationId": start_station.id,
        "vehicleTypeId": vehicle_type_min_spontaneous_rent_vehicle.id,
    }
    response = user_client_jane_canrent_logged_in.post("/api/reservation", data)
    assert response.status_code == 400, response.content


@pytest.mark.django_db
def test_start_reservation_forbidden_logged_in_with_reservation_rights(
    user_client_jane_canrent_logged_in,
    vehicle_type_reservation_forbidden,
    start_station,
    available_bike,
):
    start_date = now()
    end_date = start_date + timedelta(days=2)
    data = {
        "startDate": start_date.strftime("%Y-%m-%dT%H:%M"),
        "endDate": end_date.strftime("%Y-%m-%dT%H:%M"),
        "startStationId": start_station.id,
        "vehicleTypeId": vehicle_type_reservation_forbidden.id,
    }
    response = user_client_jane_canrent_logged_in.post("/api/reservation", data)
    assert response.status_code == 400, response.content


@pytest.mark.django_db
def test_start_reservation_disabled_bike_logged_in_with_reservation_rights(
    user_client_jane_canrent_logged_in,
    vehicle_type_reservation_allowed,
    start_station,
    disabled_bike,
):
    start_date = now()
    end_date = start_date + timedelta(days=2)
    data = {
        "startDate": start_date.strftime("%Y-%m-%dT%H:%M"),
        "endDate": end_date.strftime("%Y-%m-%dT%H:%M"),
        "startStationId": start_station.id,
        "vehicleTypeId": vehicle_type_reservation_allowed.id,
    }
    response = user_client_jane_canrent_logged_in.post("/api/reservation", data)
    assert response.status_code == 400, response.content
