from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from .models import Battery, BatteryType, UserRole, Cart, CartItem, Shipment
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login as auth_login
from django.contrib.auth.views import LoginView

def has_role(role):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            try:
                user_role = request.user.role.role
                if user_role == 'admin' or user_role == role:
                    return view_func(request, *args, **kwargs)
                messages.error(request, 'У вас нет прав для выполнения этого действия')
                return redirect('catalog:home')
            except UserRole.DoesNotExist:
                messages.error(request, 'Роль пользователя не определена')
                return redirect('catalog:home')
        return wrapper
    return decorator

def home(request):
    batteries = Battery.objects.select_related('type').all()
    
    battery_types = BatteryType.objects.all()
    
    type_filter = request.GET.get('type')
    rechargeable_filter = request.GET.get('rechargeable')
    search_query = request.GET.get('search')
    sort_by = request.GET.get('sort', 'brand')
    group_by = request.GET.get('group_by')
    
    if type_filter:
        batteries = batteries.filter(type_id=type_filter)
    if rechargeable_filter:
        batteries = batteries.filter(rechargeable=rechargeable_filter == 'true')
    if search_query:
        batteries = batteries.filter(
            Q(brand__icontains=search_query) |
            Q(type__name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    if sort_by == 'price':
        batteries = batteries.order_by('price')
    elif sort_by == 'capacity':
        batteries = batteries.order_by('capacity')
    elif sort_by == 'voltage':
        batteries = batteries.order_by('voltage')
    elif sort_by == 'stock':
        batteries = batteries.order_by('stock')
    else:
        batteries = batteries.order_by('brand')

    if group_by:
        if group_by == 'type':
            batteries = batteries.order_by('type__name', 'brand')
        elif group_by == 'rechargeable':
            batteries = batteries.order_by('rechargeable', 'brand')
        elif group_by == 'voltage':
            batteries = batteries.order_by('voltage', 'brand')
    
    context = {
        'batteries': batteries,
        'battery_types': battery_types,
        'current_type': type_filter,
        'current_rechargeable': rechargeable_filter,
        'search_query': search_query,
        'current_sort': sort_by,
        'current_group': group_by
    }
    return render(request, 'catalog/home.html', context)

def about(request):
    return render(request, 'catalog/about.html')

def battery_detail(request, pk):
    battery = get_object_or_404(Battery, pk=pk)
    context = {
        'battery': battery,
        'can_edit': request.user.role.role in ['admin', 'merchandiser'] if hasattr(request.user, 'role') else False,
        'can_order': request.user.is_authenticated and battery.stock > 0
    }
    return render(request, 'catalog/battery_detail.html', context)

@login_required
@has_role('merchandiser')
def edit_battery(request, pk):
    battery = get_object_or_404(Battery, pk=pk)
    if request.method == 'POST':
        # Обработка формы редактирования
        battery.description = request.POST.get('description', battery.description)
        battery.price = request.POST.get('price', battery.price)
        battery.small_wholesale_price = request.POST.get('small_wholesale_price', battery.small_wholesale_price)
        battery.small_wholesale_quantity = request.POST.get('small_wholesale_quantity', battery.small_wholesale_quantity)
        battery.large_wholesale_price = request.POST.get('large_wholesale_price', battery.large_wholesale_price)
        battery.large_wholesale_quantity = request.POST.get('large_wholesale_quantity', battery.large_wholesale_quantity)
        battery.last_modified_by = request.user
        battery.save()
        messages.success(request, 'Товар успешно обновлен')
        return redirect('catalog:battery_detail', pk=pk)
    return render(request, 'catalog/edit_battery.html', {'battery': battery})

@login_required
def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user, is_active=True)
    context = {
        'cart': cart,
        'can_order': request.user.is_authenticated and cart.items.exists()
    }
    return render(request, 'catalog/cart.html', context)

@login_required
def add_to_cart(request, pk):
    if request.method == 'POST':
        battery = get_object_or_404(Battery, pk=pk)
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity > battery.stock:
            messages.error(request, 'Запрошенное количество превышает доступный запас')
            return redirect('catalog:battery_detail', pk=pk)
        
        cart, created = Cart.objects.get_or_create(user=request.user, is_active=True)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, battery=battery)
        
        if not created:
            cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity
            
        cart_item.save()
        messages.success(request, 'Товар добавлен в корзину')
        return redirect('catalog:cart')
    
    return redirect('catalog:battery_detail', pk=pk)

@login_required
def remove_from_cart(request, pk):
    cart_item = get_object_or_404(CartItem, pk=pk, cart__user=request.user)
    cart_item.delete()
    messages.success(request, 'Товар удален из корзины')
    return redirect('catalog:cart')

@login_required
def update_cart_item(request, pk):
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, pk=pk, cart__user=request.user)
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity > cart_item.battery.stock:
            messages.error(request, 'Запрошенное количество превышает доступный запас')
            return redirect('catalog:cart')
        
        cart_item.quantity = quantity
        cart_item.save()
        messages.success(request, 'Количество товара обновлено')
    
    return redirect('catalog:cart')

@login_required
@has_role('sales_manager')
def create_order(request):
    cart = get_object_or_404(Cart, user=request.user, is_active=True)
    
    if not cart.items.exists():
        messages.error(request, 'Корзина пуста')
        return redirect('catalog:cart')
    
    # Здесь можно добавить логику создания заказа
    # Например, создание модели Order и OrderItem
    
    cart.is_active = False
    cart.save()
    messages.success(request, 'Заказ успешно создан')
    return redirect('catalog:home')

@login_required
@has_role('sales_manager')
def create_shipment(request):
    if request.method == 'POST':
        battery = request.POST.get('battery')
        quantity = request.POST.get('quantity')
        
        if battery and quantity:
            battery = get_object_or_404(Battery, pk=battery)
            quantity = int(quantity)
            
            if quantity <= battery.stock:
                # Создаем партию
                shipment = Shipment.objects.create(
                    battery=battery,
                    quantity=quantity,
                    created_by=request.user
                )
                # Уменьшаем количество на складе
                battery.stock -= quantity
                battery.save()
                
                messages.success(request, f'Партия товара {battery} в количестве {quantity} шт. успешно создана')
                return redirect('catalog:shipments')
            else:
                messages.error(request, 'Запрашиваемое количество превышает остаток на складе')
    
    batteries = Battery.objects.filter(stock__gt=0)
    return render(request, 'catalog/create_shipment.html', {'batteries': batteries})

@login_required
@has_role('sales_manager')
def shipments(request):
    shipments = Shipment.objects.select_related('battery', 'created_by').all()
    return render(request, 'catalog/shipments.html', {'shipments': shipments})

@login_required
@has_role('sales_manager')
def delete_shipment(request, pk):
    shipment = get_object_or_404(Shipment, pk=pk)
    
    # Проверяем, что пользователь создал эту партию
    if shipment.created_by != request.user and not request.user.role.role == 'admin':
        messages.error(request, 'Вы можете удалять только свои партии')
        return redirect('catalog:shipments')
    
    # Возвращаем товар на склад
    battery = shipment.battery
    battery.stock += shipment.quantity
    battery.save()
    
    # Удаляем партию
    shipment.delete()
    messages.success(request, 'Партия успешно удалена')
    return redirect('catalog:shipments')

class CustomLoginView(LoginView):
    def form_valid(self, form):
        response = super().form_valid(form)
        # Создаем UserRole для пользователя, если её нет
        UserRole.objects.get_or_create(user=self.request.user, defaults={'role': 'guest'})
        return response

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Создаем UserRole для нового пользователя с ролью 'guest'
            UserRole.objects.create(user=user, role='guest')
            auth_login(request, user)
            return redirect('catalog:home')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})
