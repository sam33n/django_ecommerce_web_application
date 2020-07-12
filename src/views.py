from django.shortcuts import render , get_object_or_404
from .models import Item , OrderItem, Order , Address, Payment, Coupon
from django.views.generic import ListView, DetailView, View
from django.shortcuts import redirect
from django.utils import timezone
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from .forms import CheckoutForm, CouponForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY




class HomeView(ListView):
    model = Item
    paginate_by = 5
    template_name = 'home.html'



class ItemDetailView(LoginRequiredMixin, DetailView):
    model = Item
    template_name = 'product.html'


class CheckoutView(View):
    def get(self, *args, **kwargs):
        try:
            order= Order.objects.get(user=self.request.user , ordered = False)
            form = CheckoutForm()
            context = {
                'form' : form ,
                'couponform' : CouponForm(),
                'order' : order,
                'DISPLAY_COUPON_CODE' : True,
            }
            return render(self.request, 'checkout.html', context)
        except ObjectDoesNotExist:
            messages.error(self.request, 'You do not have an active order')
            return render('src:checkout')
        
        
        return render(self.request, 'checkout.html', context)

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order= Order.objects.get(user=self.request.user , ordered = False)
            if form.is_valid():
                street_address = form.cleaned_data.get('street_address')
                apartment_address = form.cleaned_data.get('apartment_address')
                country = form.cleaned_data.get('country')
                zip = form.cleaned_data.get('zip')
                payment_option =  form.cleaned_data.get('payment_option')
                billing_address = Address.objects.create(user=self.request.user,
                                                                street_address=street_address,
                                                                apartment_address=apartment_address,
                                                                country=country,
                                                                address_type = 'B',
                                                                zip=zip )
                billing_address.save()
                order.billing_address = billing_address
                order.save()
                if payment_option == 'S':
                    return redirect('src:payment-option', payment_option='stripe')
                elif payment_option == 'P':
                    return redirect('src:payment-option', payment_option='paypal')
                else:
                    messages.warning(self.request, 'Invalid payment choice selected')
                    return redirect('src:checkout')
        except ObjectDoesNotExist:
            messages.error(self.request, 'You do not have an active order')
            return redirect('src:order-summary')
        

class PaymentView(View):
    
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        if order.billing_address:
            context = {
                'order' : order,
                'DISPLAY_COUPON_CODE' : False,
            }
            return render(self.request, 'payment.html', context)
        else:
            messages.warning(self.request, 'You have not filled the billing address')
            return redirect('src:checkout')

    

    def post(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        token = self.request.POST.get('stripeToken')
        amount = int(order.get_total() * 100)
        try:
            charge = stripe.Charge.create(
            amount=amount,
            currency="usd",
            source=token,
            )

             #create the payment
            payment = Payment.objects.create(
                                            stripe_charge_id=charge['id'],
                                            user=self.request.user, 
                                            price = amount,
                                            )

            #assign payment to the order
            order_item = order.item.all()
            print(order_item)
            order_item.update(ordered=True)
            for item in order_item:
                item.save()



            order.payment = payment
            order.ordered =True
            order.save()

            messages.success(self.request, 'Your order is successful')
            return redirect('/')
            
        except stripe.error.CardError as e:   
            messages.error(self.request, f'e.error.message')
            return redirect('/')

        except stripe.error.RateLimitError as e:
            messages.error(self.request, 'Rate limit error')
            return redirect('/')
        

        
        except stripe.error.InvalidRequestError as e:
            messages.error(self.request, 'Invalid request error')
            return redirect('/')
        
        
        except stripe.error.AuthenticationError as e:
            messages.error(self.request, 'Authentication error')
            return redirect('/')
       
        
        except stripe.error.APIConnectionError as e:
            messages.error(self.request, 'Network connection error')
            return redirect('/')
    
        
        except stripe.error.StripeError as e:
            messages.error(self.request, 'Something went wrong, You were not charged')
            return redirect('/')
        
        
        except Exception as e:
            messages.error(self.request, 'A serious error occured, you have been notified')
            return redirect('/')
        
        
        


class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        try:
            order= Order.objects.get(user=self.request.user , ordered = False)
            context = {
                'object' : order
            }
        except ObjectDoesNotExist:
            messages.error(self.request, 'You do not have an active order')
            return render('/')
        

        return render(self.request,'order_summary.html' , context)



@login_required
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item , created= OrderItem.objects.get_or_create(user=request.user,
                                                 item=item,
                                                 ordered=False)
    order_qs = Order.objects.filter(user=request.user,
                                    ordered = False )
    if order_qs.exists():
        order = order_qs[0]
        if order.item.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, 'The item quantity was updated')
            return redirect('src:order-summary')
        else:
            order.item.add(order_item)
            messages.info(request, 'This item was added in your cart')
            return redirect('src:order-summary')
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(user=request.user, ordered_date=ordered_date)
        order.item.add(order_item)
    return redirect('src:order-summary')


@login_required
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user,
                                    ordered = False )
    if order_qs.exists():
        order = order_qs[0]
        if order.item.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(user=request.user,
                                                 item=item,
                                                 ordered=False)[0]                                    
            order.item.remove(order_item)
                
            messages.info(request, 'This item was removed from your cart')
            return redirect('src:order-summary')
        else:
            messages.info(request, 'This item was not in your cart')
            return redirect('src:product', slug=slug)
    else:
        messages.info(request,'You do not have an active order')
        return redirect('src:product', slug=slug)
    return redirect('src:product' , slug=slug)


@login_required
def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user,
                                    ordered = False )
    if order_qs.exists():
        order = order_qs[0]
        if order.item.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(user=request.user,
                                                 item=item,
                                                 ordered=False)[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.item.remove(order_item)
            messages.info(request, 'The item quantity was updated')
            return redirect('src:order-summary')
            
        else:
            messages.info(request, 'This item was not in your cart')
            return redirect('src:order-summary')
    else:
        messages.info(request,'You do not have an active order')
        return redirect('src:order-summary')
    return redirect('src:order-summary')




def get_coupon(request, code):
    try:
        coupon = Coupon.objects.get(code=code)
        return coupon
    except ObjectDoesNotExist:
        messages.warning(request, 'This Coupon does not exist')
        return redirect('src:checkout')




class CouponView(View):

    def post(self, *args, **kwargs):
        try:
            form = CouponForm(self.request.POST or None)
            if form.is_valid():
                code = form.cleaned_data.get('code')
                order = Order.objects.get(user=self.request.user, ordered=False)
                order.coupon = get_coupon(self.request, code)
                order.save()
                messages.success(self.request, 'You have successfully added the Coupon')
                return redirect('src:checkout')
        except ObjectDoesNotExist:
            messages.error(self.request, 'You do not have an active order')
            return render('src:checkout')
        

       