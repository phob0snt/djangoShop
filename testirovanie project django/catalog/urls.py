from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.home, name='home'),
    path('battery/<int:pk>/', views.battery_detail, name='battery_detail'),
    path('battery/<int:pk>/edit/', views.edit_battery, name='edit_battery'),
    path('about/', views.about, name='about'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:pk>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:pk>/', views.update_cart_item, name='update_cart_item'),
    path('cart/create-order/', views.create_order, name='create_order'),
    path('register/', views.register, name='register'),
    path('shipments/', views.shipments, name='shipments'),
    path('shipments/create/', views.create_shipment, name='create_shipment'),
    path('shipments/delete/<int:pk>/', views.delete_shipment, name='delete_shipment'),
] 