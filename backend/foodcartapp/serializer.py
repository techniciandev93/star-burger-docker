from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework.fields import ListField
from rest_framework.serializers import ModelSerializer

from foodcartapp.models import Order, OrderItem


class OrderItemSerializer(ModelSerializer):

    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']

    def create(self, validated_data):
        return OrderItem.objects.create(**validated_data)


class OrderSerializer(ModelSerializer):
    products = ListField(child=OrderItemSerializer(), allow_empty=False, write_only=True)
    phonenumber = PhoneNumberField(region="RU")

    class Meta:
        model = Order
        fields = ['id', 'products', 'firstname', 'lastname', 'phonenumber', 'address']

    def create(self, validated_data):
        item_products = validated_data.pop('products')
        instance_order = Order.objects.create(**validated_data)
        participants = [OrderItem(order=instance_order,
                                  price=fields['product'].price,
                                  **fields) for fields in item_products]
        OrderItem.objects.bulk_create(participants)
        return instance_order
