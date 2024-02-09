import os
from urllib.parse import urlparse

import django
import requests
from django.core.files.base import ContentFile

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'star_burger.settings')
django.setup()

from foodcartapp.models import Restaurant, Product, ProductCategory, RestaurantMenuItem

test_products = [
    {
        "title": "Стейкхаус",
        "type": "Бургер",
        "price": "269",
        "img": "https://raw.githubusercontent.com/devmanorg/star-burger-products/master/media/steak.jpg",
        "description": "Стейкхаус – это сочетание нашей фирменной, приготовленной на огне 100% говядины с ломтиками "
                       "бекона и соусом «Барбекю», майонезом, листьями свежего салата, помидором и хрустящим луком на "
                       "воздушной булочке, посыпанной кукурузной крошкой."
    },
    {
        "title": "Лонг Чизбургер",
        "type": "Бургер",
        "price": "219",
        "img": "https://raw.githubusercontent.com/devmanorg/star-burger-products/master/media/long_chiz.jpg",
        "description": "Лонг Чизбургер – эталон в коллекции чизбургеров! Два приготовленных на огне бифштекса с двумя "
                       "ломтиками слегка расплавленного сыра, хрустящими огурчиками, рубленым луком, горчицей и "
                       "кетчупом на длинной подрумяненной булочке с кунжутом."
    },
    {
        "title": "Тройной Воппер",
        "type": "Бургер",
        "price": "369",
        "img": "https://raw.githubusercontent.com/devmanorg/star-burger-products/master/media/triple_vopper.jpg",
        "description": "ВОППЕР® — это вкуснейшая приготовленная на огне 100% говядина с сочными помидорами, "
                       "свежим нарезанным листовым салатом, густым майонезом, хрустящими маринованными огурчиками и "
                       "свежим луком на нежной булочке с кунжутом."
    },
    {
        "title": "Беконайзер",
        "type": "Бургер",
        "price": "319",
        "img": "https://raw.githubusercontent.com/devmanorg/star-burger-products/master/media/beconizer.jpg",
        "description": "Встречай самый внушительный бургер в коллекции Бургер Кинг. Много мяса, много бекона и много "
                       "сыра - все, как ты любишь, и ничего лишнего!"
    },
    {
        "title": "Фиш Ролл",
        "type": "Ролл",
        "price": "199",
        "img": "https://raw.githubusercontent.com/devmanorg/star-burger-products/master/media/fish_roll.jpg",
        "description": "Наш новый ролл с аппетитной котлеткой из филе белой рыбы, с фирменным соусом, маринованными "
                       "огурчиками и хрустящим салатом. Легкое рыбное удовольствие!"
    },
    {
        "title": "Шримп Ролл",
        "type": "Ролл",
        "price": "209",
        "img": "https://raw.githubusercontent.com/devmanorg/star-burger-products/master/media/shrimp_roll.jpg",
        "description": "Легкий ролл с нежными королевскими креветками в хрустящей панировке, свежий салат Айсберг и "
                       "ломтик сыра в пшеничной лепешке под фирменным соусом «Кинг». Внимание! Блюдо содержит "
                       "аллергены – морепродукты."
    }
]

test_restaurants = [
    {
        "title": "Star Burger Арбат",
        "address": "Москва, ул. Новый Арбат, 15",
        "contact_phone": "+7 (967) 157-44-13"
    },
    {
        "title": "Star Burger Цветной",
        "address": "Москва, Цветной бульвар, 11с2",
        "contact_phone": "+7 (929) 949-55-36"
    },
    {
        "title": "Star Burger Европейский",
        "address": "Москва, пл. Киевского Вокзала, 2",
        "contact_phone": "+7 (929) 680-47-58"
    }
]


def create_restaurants():
    for restaurant in test_restaurants:
        Restaurant.objects.get_or_create(
            name=restaurant['title'],
            address=restaurant['address'],
            contact_phone=restaurant['contact_phone']
        )


def create_products():
    for product in test_products:
        response = requests.get(product['img'])
        response.raise_for_status()
        file_name = os.path.basename(urlparse(response.url).path)
        img_file = ContentFile(response.content, name=file_name)
        obj_product_category, created = ProductCategory.objects.get_or_create(name=product['type'])
        Product.objects.get_or_create(
            name=product['title'],
            category=obj_product_category,
            price=product['price'],
            image=img_file,
            description=product['description']
        )


def gen_restaurant():
    restaurants = Restaurant.objects.all()
    while True:
        for restaurant in restaurants.iterator():
            yield restaurant


def create_restaurant_menu():
    restaurant = gen_restaurant()
    burger_products = Product.objects.all()
    for product in burger_products.iterator():
        RestaurantMenuItem.objects.get_or_create(
            product=product,
            restaurant=next(restaurant)
        )


if __name__ == '__main__':
    create_restaurants()
    create_products()
    create_restaurant_menu()
