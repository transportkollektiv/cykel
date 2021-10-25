import pytest
from django.contrib.auth.models import Permission
from django.utils.timezone import now
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
def another_lock(lock_type_combination):
    return Lock.objects.create(unlock_key="000000", lock_type=lock_type_combination)


@pytest.fixture
def vehicle_type_allow_reservation():
    return VehicleType.objects.create(allow_reservation=True)


@pytest.fixture
def vehicle_type_forbid_reservation():
    return VehicleType.objects.create(allow_reservation=False)


@pytest.fixture
def available_bike(lock):
    return Bike.objects.create(
        availability_status=Bike.Availability.AVAILABLE,
        bike_number="1337",
        lock=lock,
        vehicle_type=vehicle_type_allow_reservation,
    )


@pytest.fixture
def bike_not_allowed_for_reservations(lock):
    return Bike.objects.create(
        availability_status=Bike.Availability.AVAILABLE,
        bike_number="1337",
        lock=lock,
        vehicle_type=vehicle_type_forbid_reservation,
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
def reservation_jane_running(testuser_jane_canrent, vehicle_type_allow_reservation):
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

    station = Station.objects.create(
        station_name="Teststation",
        status=Station.Status.ACTIVE,
    )

    return Reservation.objects.create(
        creator=testuser_jane_canrent,
        vehicle_type=vehicle_type_allow_reservation,
        event=event,
        start_location=station,
    )


@pytest.mark.django_db
def test_get_reservations_logged_in_with_reservation_rights(
    user_client_jane_canrent_logged_in, reservation_jane_running
):
    response = testuser_jane_canrent.get("/api/reservation")
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
