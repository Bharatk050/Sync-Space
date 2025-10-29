# Generated on: 2025-10-28 21:35:29

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Customer, Product, Order, OrderItem, Inventory
from .forms import RegistrationForm, LoginForm, ProductForm

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

@login_required
def home(request):
    products = Product.objects.all()
    return render(request, 'home.html', {'products': products})

@login_required
def add_to_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    order, created = Order.objects.get_or_create(customer=request.user, complete=False)
    order_item, created = OrderItem.objects.get_or_create(order=order, product=product)
    if not created:
        order_item.quantity += 1
        order_item.save()
    return redirect('cart')

@login_required
def cart(request):
    order = Order.objects.get(customer=request.user, complete=False)
    order_items = OrderItem.objects.filter(order=order)
    return render(request, 'cart.html', {'order_items': order_items})

@login_required
def checkout(request):
    order = Order.objects.get(customer=request.user, complete=False)
    order_items = OrderItem.objects.filter(order=order)
    total = sum(item.product.price * item.quantity for item in order_items)
    return render(request, 'checkout.html', {'order_items': order_items, 'total': total})