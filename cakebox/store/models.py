from django.db import models
from django.contrib.auth.models import AbstractUser
from random import randint

class User(AbstractUser):
    phone=models.CharField(max_length=15,unique=True)
    is_verified=models.BooleanField(default=False)
    otp=models.CharField(max_length=15,null=True)
    
    def generate_otp(self):
        self.otp=str(randint(1000,9999))
        self.save()

class BaseModel(models.Model):

    created_date=models.DateTimeField(auto_now_add=True)

    updated_date=models.DateTimeField(auto_now=True)

    is_active=models.BooleanField(default=True)


class Size(BaseModel):

    name=models.CharField(max_length=70,unique=True)

    def __str__(self):
        
        return self.name
    

class Shape(BaseModel):

    name=models.CharField(max_length=80,unique=True)

    def __str__(self):
        return self.name
    

class Tag(BaseModel):

    name=models.CharField(max_length=100,unique=True)

    def __str__(self):
        return self.name
    
class Cake(BaseModel):

    title=models.CharField(max_length=100)

    description=models.TextField()

    picture=models.ImageField(upload_to="cakeimages",null=True,blank=True)

    tag_objects=models.ManyToManyField(Tag)

    shape_objects=models.ManyToManyField(Shape)

    def __str__(self):
        
        return self.title


class CakeVarient(BaseModel):

    cake_object=models.ForeignKey(Cake,on_delete=models.CASCADE,related_name="varients")

    size_object=models.ForeignKey(Size,on_delete=models.CASCADE)

    price=models.FloatField()

class Cart(BaseModel):

    cake_varient_object=models.ForeignKey(CakeVarient,on_delete=models.Case)

    shape_object=models.ForeignKey(Shape,on_delete=models.CASCADE)

    owner=models.ForeignKey(User,on_delete=models.CASCADE)

    quantity=models.PositiveIntegerField()

    is_order_placed=models.BooleanField(default=False)

    def item_total(self):

        return self.quantity*self.cake_varient_object.price
    
class Order(BaseModel):

    customer=models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")

    address=models.TextField(null=False, blank=False)

    phone=models.CharField(max_length=20, null=False, blank=False)
    
    PAYMENT_OPTIONS=(
        ("COD","COD"),
        ("ONLINE","ONLINE")
    )

    payment_method=models.CharField(max_length=15, choices=PAYMENT_OPTIONS, default="COD")

    rzp_order_id=models.CharField(max_length=100, null=True)

    is_paid=models.BooleanField(default=False)

    def order_total(self):
        total=0
        order_items=self.orderitems.all()
        if order_items:
            total=sum([oi.item_total() for oi in order_items])
        return total
    

class OrderItem(BaseModel):

    order_object=models.ForeignKey(Order,on_delete=models.CASCADE, related_name="orderitems")

    cake_varient_object=models.ForeignKey(CakeVarient, on_delete=models.CASCADE)
    
    quantity=models.PositiveIntegerField(default=1)
    
    shape_object=models.ForeignKey(Shape, on_delete=models.CASCADE)
    
    price=models.FloatField()

    def item_total(self):

        return self.price*self.quantity
    

  



