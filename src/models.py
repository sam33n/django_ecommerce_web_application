from django.db import models
from django.conf import settings
from django.shortcuts import reverse
from django_countries.fields import CountryField



CATEGORY_CHOICES = (
    ('S', 'Shirt'),
    ('SW', 'Sport wear'),
    ('OW', 'Out wear')

)

LABEL_CHOICES = (
    ('P', 'primary'),
    ('S', 'secondary'),
    ('D', 'danger')

)


class Item(models.Model):
    title = models.CharField(max_length=30)
    price = models.FloatField()
    discount = models.FloatField(blank=True, null=True)
    category = models.CharField(choices=CATEGORY_CHOICES, max_length=2)
    label = models.CharField(choices=LABEL_CHOICES, max_length=1)
    slug  = models.SlugField()
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(blank=True, null=True)
    

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('src:product', kwargs={
            'slug' : self.slug
        })

    def get_add_to_cart_url(self):
        return reverse('src:add-to-cart' ,kwargs={
            'slug' : self.slug
        })

    def get_remove_from_cart_url(self):
        return reverse('src:remove-from-cart' ,kwargs={
            'slug' : self.slug
        })




class OrderItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    ordered = models.BooleanField(default=False)


    def __str__(self):
        return f'{self.quantity} item of {self.item.title}'

    def get_total_amount(self):
        return self.quantity * self.item.price
        
    def get_discount_price(self):
        return self.quantity * self.item.discount

    def get_amount_save(self):
        return self.get_total_amount() - self.get_discount_price()

    def get_final_total(self):
        if self.item.discount:
            return self.get_discount_price()
        return self.get_total_amount()



class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ordered = models.BooleanField(default=False)
    item = models.ManyToManyField(OrderItem)
    start_date = models.DateTimeField(auto_now_add=True)
    ordered_date = models.DateTimeField()
    shipping_address = models.ForeignKey('Address', related_name='shipping_address', on_delete=models.SET_NULL, blank=True, null=True)
    billing_address = models.ForeignKey('Address',related_name='billing_address', on_delete=models.SET_NULL, blank=True, null=True)
    payment = models.ForeignKey('Payment', on_delete=models.SET_NULL, blank=True, null=True)
    coupon = models.ForeignKey('Coupon', on_delete=models.SET_NULL, blank=True, null=True)


    def __str__(self):
        return self.user.username

    def get_total(self):
        total = 0
        for order_item in self.item.all():
            total += order_item.get_final_total()
        total -= self.coupon.amount
        return total


ADDRESS_CHOICES = (
    ('B', 'billing'),
    ('S', 'Shipping'),
)


class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    street_address = models.CharField(max_length=120)
    apartment_address = models.CharField(max_length=120)
    country = CountryField(multiple=False)
    zip = models.CharField(max_length=10)
    address_type = models.CharField(choices=ADDRESS_CHOICES, max_length=1)
    default = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name_plural = 'Addresses'



class Payment(models.Model):
    stripe_charge_id = models.CharField(max_length = 50)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    price = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


class Coupon(models.Model):
    code = models.CharField(max_length=50)
    amount = models.FloatField()

    def __str__(self):
        return self.code