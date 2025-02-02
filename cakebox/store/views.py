from django.shortcuts import render,redirect
from django.views.generic import View
from store.forms import SignUpForm,OtpVerifyForm,SignInForm,OrderForm
from twilio.rest import Client
from store.models import User,Cake,CakeVarient,Cart,Shape,OrderItem,Order
from django.contrib.auth import authenticate,login,logout
import razorpay
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from store.decorators import signin_required
from decouple import config



TWILIO_ACCOUNT_SID=config('TWILIO_ACCOUNT_SID')
TWILIO_ACCOUNT_SECRET='d6997c1c330ea7b668c76b147761d621'
TWILIO_PHONE_NUMBER='+12186338258'

RZP_KEY_ID=config('RZP_KEY_ID')

RZP_KEY_SECRET="Re19uw61IIpBZesNeTxsyImd"

def send_otp_phone(user_object):

    user_object.generate_otp()
    account_sid = 'account_sid'
    auth_token = "d6997c1c330ea7b668c76b147761d621"
    client = Client(account_sid, auth_token)

    message= client.messages.create(
      from_="+12186338258",
      body=user_object.otp,
      to="+917736609861",
      
    )

    print(message.sid)
class SignUpView(View):
    template_name='register.html'
    form_class=SignUpForm
    def get(self,request,*args,**kwargs):
        form_instance=self.form_class()
        return render(request,self.template_name,{'form':form_instance})
    def post(self,request,*args,**kwargs):
        form_instance=self.form_class(request.POST)
        if form_instance.is_valid():
            user_instance=form_instance.save(commit=False)
            user_instance.is_active=False
            user_instance.save()
            send_otp_phone(user_instance)
            return redirect('verify-otp')
        else:
            return render(request,self.template_name,{'form':form_instance})
        

#verify otp
class OtpVerifyView(View):
    template_name='otp_verify.html'
    form_class=OtpVerifyForm
    def get(self,request,*args,**kwargs):
        form_instance=self.form_class
        return render(request,self.template_name,{'form':form_instance})
    def post(self,request,*args,**kwargs):
        otp=request.POST.get('otp')
        try:
            user_object=User.objects.get(otp=otp)
            user_object.is_active=True
            user_object.is_verified=True
            user_object.otp=None
            user_object.save()
            return redirect('signin')
        except:
            print('failed otp')
            return redirect('verify-otp')
        
class SignInview(View):
    template_name='signin.html'
    form_class=SignInForm
    def get(self,request,*args,**kwargs):
        form_instance=self.form_class
        return render(request,self.template_name,{'form':form_instance})
    def post(self,request,*args,**kwargs):
        form_instance=self.form_class(request.POST)
        if form_instance.is_valid():
            uname=form_instance.cleaned_data.get('username')
            pwd=form_instance.cleaned_data.get('password')
            user_object=authenticate(request,username=uname,password=pwd)
            if user_object:
                login(request,user_object)
                return redirect('index')
            
        return render(request,self.template_name,{'form':form_instance})

@method_decorator(signin_required,name='dispatch')   
class IndexView(View):
    template_name='index.html'
    def get(self,request,*args,**kwargs):
        qs=Cake.objects.all()

        return render(request,self.template_name,{'cakes':qs})

@method_decorator(signin_required,name='dispatch')    
class SignOutView(View):
    def get(self,request,*args,**kwargs):
        logout(request)
        return redirect('signin')

@method_decorator(signin_required,name='dispatch')    
class ProductDetailView(View):
    template_name='product_detail.html'
    def get(self,request,*args,**kwargs):
        id=kwargs.get('pk')
        qs=Cake.objects.get(id=id)
        return render(request,self.template_name,{'cakes':qs})

@method_decorator(signin_required,name='dispatch')   
class AddToCartView(View):
    def post(self,request,*args,**kwargs):
        cake_varient_id=request.POST.get('varient')
        cake_varient_instance=CakeVarient.objects.get(id=cake_varient_id)
        shape_id=request.POST.get('shape')
        shape_instance=Shape.objects.get(id=shape_id)
        qty=request.POST.get('quantity')

        Cart.objects.create(cake_varient_object=cake_varient_instance,shape_object=shape_instance,quantity=qty,owner=request.user)
        return redirect('index')

@method_decorator(signin_required,name='dispatch')     
class CartSummaryView(View):
    template_name='cart_summary.html'
    def get(self,request,*args,**kwargs):
        qs=Cart.objects.filter(owner=request.user,is_order_placed=False)
        basket_total=sum([c.item_total() for c in qs])
        return render(request,self.template_name,{'data':qs,'basket_total':basket_total})

@method_decorator(signin_required,name='dispatch')     
class CartItemDeleteView(View):
    def get(self,request,*args,**kwargs):
        id=kwargs.get("pk")
        Cart.objects.get(id=id).delete()
        return redirect('cart-summary')

@method_decorator(signin_required,name='dispatch')    
class PlaceOrderView(View):
    template_name='place_order.html'
    form_class=OrderForm
    def get(self,request,*args,**kwargs):
        form_instance=self.form_class()
        qs=Cart.objects.filter(owner=request.user,is_order_placed=False)
        basket_total=sum([c.item_total() for c in qs])
        return render(request,self.template_name,{'form':form_instance,'cartitems':qs,'total':basket_total})
    def post(self,request,*args,**kwargs):
        form_instance=self.form_class(request.POST)
        if form_instance.is_valid():
            form_instance.instance.customer=request.user
            order_object=form_instance.save()
            cart_items=Cart.objects.filter(owner=request.user,is_order_placed=False)
            for ci in cart_items:
                OrderItem.objects.create(
                    order_object=order_object,
                    cake_varient_object=ci.cake_varient_object,
                    quantity=ci.quantity,
                    shape_object=ci.shape_object,
                    price=ci.cake_varient_object.price,
                )
                ci.is_order_placed=True
                ci.save()
            payment_method=request.POST.get('payment_method') #ONLINE , COD

            if payment_method=='ONLINE':
                client = razorpay.Client(auth=(RZP_KEY_ID, RZP_KEY_SECRET))

                data = { "amount": order_object.order_total()*100, "currency": "INR", "receipt": "order_rcptid_11" }
                payment = client.order.create(data=data)
                print("============>",payment,"<============")
                rzp_id=payment.get('id')
                order_object.rzp_order_id=rzp_id
                order_object.save()
                context={
                    'key_id':RZP_KEY_ID,
                    'amount':order_object.order_total()*100,
                    'order_id':order_object.rzp_order_id,

                }
                return render(request,'payment.html',context)

            return redirect('index')

@method_decorator(signin_required,name='dispatch') 
class OrderSummaryView(View):
    template_name='order_summary.html'
    def get(self,request,*args,**kwargs):
        qs=Order.objects.filter(customer=request.user).order_by('-created_date')
        return render(request,self.template_name,{'order':qs})
    
@method_decorator(signin_required,name='dispatch') 
@method_decorator(csrf_exempt,name='dispatch')
class PaymentVerificationView(View):
    def post(self,request,*args,**kwargs):
        print(request.POST,">>>>>>>>>>>")
        client = razorpay.Client(auth=(RZP_KEY_ID, RZP_KEY_SECRET))
        try:
            client.utility.verify_payment_signature(request.POST)
            rzp_order_id=request.POST.get('razorpay_order_id')
            Order.objects.filter(rzp_order_id=rzp_order_id).update(is_paid=True)
        except:
            print('payment failed')

        return redirect('order-summary')





