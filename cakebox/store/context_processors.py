from store.models import Cart
def greetings_context(request):
    return {'greetings':'welcome'}

def cart_context(request):
    cart_item_count=0
    if request.user.is_authenticated:
        cart_item_count=Cart.objects.filter(owner=request.user,is_order_placed=False).count()

    return {'cart_item_count':cart_item_count}