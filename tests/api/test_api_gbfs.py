import pytest
from django.contrib.gis.geos import Point
from django.utils import translation
from django.utils.timezone import now
from preferences import preferences
from rest_framework.test import APIClient

from bikesharing.models import Bike, Location, LocationTracker, Station, VehicleType
from gbfs.views import languageCode


@pytest.fixture
def vehicle_type_tandem():
    return VehicleType.objects.create(
        name="Tandem",
        form_factor=VehicleType.FormFactor.BIKE,
        propulsion_type=VehicleType.PropulsionType.HUMAN,
    )


@pytest.fixture
def vehicle_type_ebike():
    return VehicleType.objects.create(
        name="E-Bike",
        form_factor=VehicleType.FormFactor.BIKE,
        propulsion_type=VehicleType.PropulsionType.ELECTRIC_ASSIST,
        max_range_meters=2000,
    )


@pytest.fixture
def available_bike():
    return Bike.objects.create(
        availability_status=Bike.Availability.AVAILABLE,
        bike_number="1337",
        last_reported=now(),
    )


@pytest.fixture
def tracker(available_bike):
    return LocationTracker.objects.create(device_id=42, bike=available_bike)


@pytest.fixture
def location_of_available_bike(available_bike, tracker):
    loc = Location.objects.create(
        bike=available_bike,
        tracker=tracker,
        internal=False,
        source=Location.Source.TRACKER,
        reported_at=now(),
    )
    loc.geo = Point(9.95000, 48.35000, srid=4326)  # point is _not_ near a station
    loc.save()
    return loc


@pytest.fixture
def active_station():
    return Station.objects.create(
        status=Station.Status.ACTIVE,
        station_name="Station McStationface",
        location=Point(9.99024, 48.39662, srid=4326),
        max_bikes=5,
    )


@pytest.mark.django_db
def test_gbfs_overview(active_station):
    client = APIClient()
    response = client.get("/gbfs/gbfs.json")
    assert response.status_code == 200
    assert response.json()["version"] == "2.1"
    lang = languageCode()
    feeds = response.json()["data"][lang]["feeds"]
    assert len(feeds) > 0
    sysinfofeed = [x for x in feeds if x["name"] == "system_information"][0]
    assert len(sysinfofeed["url"]) > 0


@pytest.mark.django_db
def test_gbfs_overview_urls(active_station):
    client = APIClient()
    response = client.get("/gbfs/gbfs.json")
    assert response.status_code == 200
    lang = languageCode()
    feeds = response.json()["data"][lang]["feeds"]
    assert len(feeds) > 0
    for feed in feeds:
        response = client.get(feed["url"])
        assert response.status_code == 200


@pytest.mark.django_db
def test_gbfs_system_information():
    client = APIClient()
    response = client.get("/gbfs/system_information.json")
    assert response.status_code == 200
    assert (
        response.json()["data"]["language"].lower()
        == translation.get_language().lower()
    )
    assert response.json()["data"]["language"] == languageCode()


@pytest.mark.django_db
def test_gbfs_system_information_preferences():
    prefs = preferences.BikeSharePreferences
    prefs.gbfs_system_id = "test"
    prefs.save()

    client = APIClient()
    response = client.get("/gbfs/system_information.json")
    assert response.status_code == 200
    assert response.json()["data"]["system_id"] == prefs.gbfs_system_id


@pytest.mark.django_db
def test_gbfs_station_information(active_station):
    client = APIClient()
    response = client.get("/gbfs/station_information.json")
    assert response.status_code == 200
    assert len(response.json()["data"]["stations"]) == 1
    gbfsstation = response.json()["data"]["stations"][0]
    assert gbfsstation["name"] == active_station.station_name
    assert gbfsstation["capacity"] == active_station.max_bikes
    assert gbfsstation["lat"] == active_station.location.y
    assert gbfsstation["lon"] == active_station.location.x


@pytest.mark.django_db
def test_gbfs_vehicle_types(vehicle_type_tandem):
    client = APIClient()
    response = client.get("/gbfs/vehicle_types.json")
    assert response.status_code == 200
    assert len(response.json()["data"]["vehicle_types"]) == 2
    vtype = next(
        vtype
        for vtype in response.json()["data"]["vehicle_types"]
        if vtype["name"] == vehicle_type_tandem.name
    )
    assert vtype["vehicle_type_id"] == str(vehicle_type_tandem.id)
    assert vtype["form_factor"] == "bicycle"
    assert vtype["propulsion_type"] == "human"
    assert vtype["name"] == vehicle_type_tandem.name
    assert "max_range_meters" not in vtype


@pytest.mark.django_db
def test_gbfs_vehicle_types_non_human(vehicle_type_ebike):
    client = APIClient()
    response = client.get("/gbfs/vehicle_types.json")
    assert response.status_code == 200
    assert len(response.json()["data"]["vehicle_types"]) == 2
    vtype = next(
        vtype
        for vtype in response.json()["data"]["vehicle_types"]
        if vtype["name"] == vehicle_type_ebike.name
    )
    assert vtype["vehicle_type_id"] == str(vehicle_type_ebike.id)
    assert vtype["form_factor"] == "bicycle"
    assert vtype["propulsion_type"] == "electric_assist"
    assert vtype["name"] == vehicle_type_ebike.name
    assert vtype["max_range_meters"] == 2000


@pytest.mark.django_db
def test_gbfs_station_status(active_station):
    client = APIClient()
    response = client.get("/gbfs/station_status.json")
    assert response.status_code == 200
    assert len(response.json()["data"]["stations"]) == 1
    gbfsstation = response.json()["data"]["stations"][0]
    assert gbfsstation["station_id"] == str(active_station.id)
    assert gbfsstation["num_bikes_available"] == 0
    assert gbfsstation["num_docks_available"] == active_station.max_bikes


@pytest.mark.django_db
def test_gbfs_free_bike_status(available_bike, location_of_available_bike):
    client = APIClient()
    response = client.get("/gbfs/free_bike_status.json")
    assert response.status_code == 200
    assert len(response.json()["data"]["bikes"]) == 1
    gbfsbike = response.json()["data"]["bikes"][0]
    assert gbfsbike["bike_id"] == str(available_bike.non_static_bike_uuid)
