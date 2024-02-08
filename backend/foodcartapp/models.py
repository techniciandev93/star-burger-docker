from collections import defaultdict

from django.db import models
from django.core.validators import MinValueValidator
from django.db.models import Sum, F
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField

from places.service import check_errors_geocoding_places, update_or_create_place
from restaurateur.service import calculate_distance, FetchCoordinatesError


class OrderQuerySet(models.QuerySet):
    def calculate_order_amount(self):
        orders = self.annotate(order_cost=Sum(F('order_items__quantity') * F('order_items__price')))
        return orders

    def can_cook_restaurants(self):
        order_products = Product.objects.filter(order_items__order__in=self)

        product_restaurants = defaultdict(list)
        restaurant_menu_items = RestaurantMenuItem.objects.select_related('product', 'restaurant').filter(
            product__in=order_products, availability=True
        )

        for restaurant_menu_item in restaurant_menu_items:
            product_restaurants[restaurant_menu_item.product].append(restaurant_menu_item.restaurant)

        for order in self:
            order_items = order.order_items.all()
            if order_items:
                order_products = [item.product for item in order_items]
                restaurants = [product_restaurants[product] for product in order_products]
                order.restaurants = set(restaurants[0]).intersection(*restaurants[1:])
            else:
                order.restaurants = set()
        return self

    def calculate_distance_orders(self):
        places = check_errors_geocoding_places(self)
        for order in self:
            order.distances = {}
            for restaurant in order.restaurants:
                try:
                    distance = calculate_distance(places[order.address], places[restaurant.address])
                    order.distances[restaurant.address] = distance
                except FetchCoordinatesError:
                    order.distances[restaurant.address] = 'Ошибка определения координат'
            order.restaurants = sorted(order.restaurants,
                                       key=lambda restaurant_key: order.distances[restaurant_key.address])
        return self


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class Order(models.Model):
    ORDER_STATUSES = (
        ('UN', 'Необработанный'),
        ('AD', 'Принят'),
        ('RE', 'Готовят'),
        ('TC', 'Передан курьеру'),
        ('CO', 'Завершён')
    )
    PAYMENT = (
        ('NS', 'Не указано'),
        ('CA', 'Наличными'),
        ('EL', 'Электронно')
    )
    firstname = models.CharField(verbose_name='Имя', max_length=200)
    lastname = models.CharField(verbose_name='Фамилия', max_length=200)
    phonenumber = PhoneNumberField(verbose_name='Мобильный номер')
    address = models.CharField(verbose_name='Адрес', max_length=200)
    status = models.CharField(verbose_name='Статус', max_length=2, choices=ORDER_STATUSES, default='UN', db_index=True)
    payment_method = models.CharField(verbose_name='Способ оплаты', max_length=2, choices=PAYMENT, default='NS',
                                      db_index=True)
    comment = models.TextField(verbose_name='Комментарий', blank=True)
    registration_date = models.DateTimeField(verbose_name='Дата создания заказа', default=timezone.now, db_index=True)
    call_date = models.DateTimeField(verbose_name='Дата звонка', blank=True, null=True, db_index=True)
    delivery_date = models.DateTimeField(verbose_name='Дата доставки', blank=True, null=True, db_index=True)
    restaurant = models.ForeignKey(Restaurant, related_name='orders', verbose_name="Ресторан",
                                   on_delete=models.CASCADE, null=True, blank=True)
    objects = OrderQuerySet.as_manager()

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return f'{self.lastname} {self.firstname} {self.address}'


class OrderItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE,  verbose_name='Товар', related_name='order_items')
    order = models.ForeignKey(Order, on_delete=models.CASCADE,  verbose_name='Заказ', related_name='order_items')
    quantity = models.IntegerField(verbose_name='Количество', validators=[MinValueValidator(1)])
    price = models.DecimalField(verbose_name='Цена', max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])

    class Meta:
        verbose_name = 'Элемент заказа'
        verbose_name_plural = 'Элементы заказа'
        unique_together = [
            ['product', 'order']
        ]

    def __str__(self):
        return f"{self.product.name} {self.order.firstname} {self.order.lastname} {self.order.address}"


@receiver(post_save, sender=Restaurant)
@receiver(post_save, sender=Order)
def update_place_coordinates(sender, instance, **kwargs):
    update_or_create_place(instance)
