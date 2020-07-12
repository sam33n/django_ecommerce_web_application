from django.contrib import admin
from .models import Item, Order, OrderItem, Address, Payment, Coupon


class OrderAdmin(admin.ModelAdmin):
    list_display = [ 'user', 'ordered']




class AddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'street_address', 'apartment_address', 'address_type', 'default']


admin.site.register(Item)
admin.site.register(OrderItem)
admin.site.register(Order, OrderAdmin)
admin.site.register(Address, AddressAdmin)
admin.site.register(Payment)
admin.site.register(Coupon)
