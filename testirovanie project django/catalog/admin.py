from django.contrib import admin
from .models import Battery, BatteryType, UserRole, Cart, CartItem

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'can_view_batteries', 'can_edit_battery_description', 'can_create_shipment', 'can_do_everything')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email')
    fields = ('user', 'role', 'can_view_batteries', 'can_edit_battery_description', 'can_create_shipment', 'can_do_everything')

@admin.register(BatteryType)
class BatteryTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)

@admin.register(Battery)
class BatteryAdmin(admin.ModelAdmin):
    list_display = ('brand', 'type', 'capacity', 'rechargeable', 'voltage', 'price', 'stock', 'created_at')
    list_filter = ('type', 'rechargeable', 'created_at')
    search_fields = ('brand', 'type__name', 'description')
    readonly_fields = ('created_at', 'updated_at', 'last_modified_by')
    fieldsets = (
        ('Основная информация', {
            'fields': ('brand', 'type', 'capacity', 'rechargeable')
        }),
        ('Технические характеристики', {
            'fields': ('voltage', 'description')
        }),
        ('Торговая информация', {
            'fields': ('price', 'small_wholesale_price', 'small_wholesale_quantity',
                      'large_wholesale_price', 'large_wholesale_quantity', 'stock')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at', 'last_modified_by'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        obj.last_modified_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'updated_at', 'is_active', 'total_price')
    list_filter = ('is_active', 'created_at')
    search_fields = ('user__username',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'battery', 'quantity', 'total_price')
    list_filter = ('created_at',)
    search_fields = ('battery__brand', 'cart__user__username')
    readonly_fields = ('created_at', 'updated_at')
