import requests
from django.utils import timezone

from restaurateur.service import fetch_coordinates
from .models import Place

from star_burger.settings import YANDEX_GEOCODER_TOKEN


def get_coordinates_from_address(address):
    try:
        coordinate = fetch_coordinates(YANDEX_GEOCODER_TOKEN, address)
        if coordinate:
            lng, lat = coordinate
        else:
            lng, lat = None, None
        geocoding_failed = False
    except requests.RequestException:
        lng, lat = None, None
        geocoding_failed = True
    return lng, lat, geocoding_failed


def update_places(need_update_places):
    places = []
    for place in need_update_places:
        lng, lat, geocoding_failed = get_coordinates_from_address(place.address)

        places.append(Place(id=place.id, lng=lng, lat=lat, date=timezone.localtime(), geocoding_failed=geocoding_failed))
    Place.objects.bulk_update(places, ['lng', 'lat', 'date', 'geocoding_failed'], batch_size=1000)
    return places


def update_or_create_place(obj):
    lng, lat, geocoding_failed = get_coordinates_from_address(obj.address)
    place, created = Place.objects.get_or_create(
        address=obj.address,
        defaults={
            'lng': lng,
            'lat': lat,
            'geocoding_failed': geocoding_failed,
            'date': timezone.localtime()
        })
    if not created:
        place.lng = lng
        place.lat = lat
        place.date = timezone.localtime()
        place.geocoding_failed = geocoding_failed
        place.save()


def check_errors_geocoding_places(orders):
    addresses = []
    for order in orders:
        addresses.append(order.address)
        for restaurant in order.restaurants:
            addresses.append(restaurant.address)

    places = Place.objects.filter(address__in=addresses)
    need_update_places = places.filter(geocoding_failed=True)

    if need_update_places:
        updated_places = update_places(need_update_places)
        places = list(Place.objects.exclude(address__in=updated_places))
        places.extend(updated_places)

    places = {place.address: (place.lat, place.lng) for place in places}
    return places
