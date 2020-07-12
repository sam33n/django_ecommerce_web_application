from django import forms
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget

PAYMENT_CHOICE = (      
    ('S', 'Stripe'),
    ('P', 'Paypal')
)


class CheckoutForm(forms.Form):
    street_address = forms.CharField(widget=forms.TextInput(attrs={
        'placeholder' : '1234 Main St'
    }))
    apartment_address = forms.CharField(required=False , widget=forms.TextInput(attrs={
        'placeholder' : 'Apartment or suite'
    }))
    country = CountryField(blank_label= '(select country)').formfield(widget=CountrySelectWidget(attrs={
        'class' : 'custom-select d-block w-100'
    }))
    zip = forms.CharField()
    same_billing_address = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={
        'class' : 'custom-control-input'
    }))
    save_info = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={
        'class' : 'custom-control-input'
    }))
    payment_option = forms.ChoiceField(widget=forms.RadioSelect, choices=PAYMENT_CHOICE)



class CouponForm(forms.Form):
    code = forms.CharField(widget=forms.TextInput(attrs={
        'class' : 'form-control',
        'placeholder' : 'Promo code',
        'aria-label' : 'Recipient username',
        'aria-label' : 'basic-addon2'
    }))
