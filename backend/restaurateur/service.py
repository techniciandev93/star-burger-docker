import requests
from geopy import distance


class FetchCoordinatesError(TypeError):
    pass


def fetch_coordinates(apikey, address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": apikey,
        "format": "json",
    })
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lon, lat


def calculate_distance(first_coordinate, second_coordinate):
    if any(x is None for x in [*first_coordinate, *second_coordinate]):
        raise FetchCoordinatesError('Одна из координат или обе координаты не определенны')
    return distance.distance(first_coordinate, second_coordinate).kilometers
