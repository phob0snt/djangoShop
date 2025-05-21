from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User

class UserRole(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Администратор'),
        ('merchandiser', 'Товаровед'),
        ('sales_manager', 'Менеджер по продажам'),
        ('guest', 'Гость'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='role')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='guest')
    
    # Разрешения для ролей
    can_view_batteries = models.BooleanField(default=False)  # Гость
    can_edit_battery_description = models.BooleanField(default=False)  # Товаровед
    can_create_shipment = models.BooleanField(default=False)  # Менеджер по продажам
    can_do_everything = models.BooleanField(default=False)  # Администратор
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
    
    def save(self, *args, **kwargs):
        # Автоматически назначаем разрешения в зависимости от роли
        if self.role == 'admin':
            self.can_view_batteries = True
            self.can_edit_battery_description = True
            self.can_create_shipment = True
            self.can_do_everything = True
        elif self.role == 'merchandiser':
            self.can_view_batteries = True
            self.can_edit_battery_description = True
            self.can_create_shipment = False
            self.can_do_everything = False
        elif self.role == 'sales_manager':
            self.can_view_batteries = True
            self.can_edit_battery_description = False
            self.can_create_shipment = True
            self.can_do_everything = False
        elif self.role == 'guest':
            self.can_view_batteries = True
            self.can_edit_battery_description = False
            self.can_create_shipment = False
            self.can_do_everything = False
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "Роль пользователя"
        verbose_name_plural = "Роли пользователей"

class BatteryType(models.Model):
    name = models.CharField(max_length=50, verbose_name="Название типа")
    description = models.TextField(verbose_name="Описание типа", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Тип батарейки"
        verbose_name_plural = "Типы батареек"
        ordering = ['name']

class Battery(models.Model):
    brand = models.CharField(
        max_length=100, 
        verbose_name="Бренд",
        help_text="Название производителя батарейки"
    )
    type = models.ForeignKey(
        BatteryType,
        on_delete=models.CASCADE,
        verbose_name="Тип",
        related_name="batteries"
    )
    capacity = models.PositiveIntegerField(
        verbose_name="Емкость (мАч)",
        validators=[
            MinValueValidator(1, message="Емкость должна быть больше 0"),
            MaxValueValidator(100000, message="Емкость не может быть больше 100000 мАч")
        ]
    )
    rechargeable = models.BooleanField(
        verbose_name="Перезаряжаемая",
        default=False
    )
    voltage = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Напряжение (В)",
        validators=[
            MinValueValidator(0.1, message="Напряжение должно быть больше 0.1В"),
            MaxValueValidator(100, message="Напряжение не может быть больше 100В")
        ]
    )
    description = models.TextField(
        verbose_name="Описание",
        blank=True,
        help_text="Подробное описание батарейки"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Цена за единицу",
        validators=[MinValueValidator(0)]
    )
    small_wholesale_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Цена мелкого опта",
        validators=[MinValueValidator(0)],
        null=True,
        blank=True
    )
    small_wholesale_quantity = models.PositiveIntegerField(
        verbose_name="Количество для мелкого опта",
        null=True,
        blank=True
    )
    large_wholesale_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Цена крупного опта",
        validators=[MinValueValidator(0)],
        null=True,
        blank=True
    )
    large_wholesale_quantity = models.PositiveIntegerField(
        verbose_name="Количество для крупного опта",
        null=True,
        blank=True
    )
    stock = models.PositiveIntegerField(
        verbose_name="Количество на складе",
        default=0
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_modified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Последний редактор",
        related_name="modified_batteries"
    )

    def __str__(self):
        return f"{self.brand} {self.type.name}"

    @property
    def estimated_energy(self):
        if self.voltage:
            return (self.capacity * self.voltage) / 1000
        return None

    class Meta:
        verbose_name = "Батарейка"
        verbose_name_plural = "Батарейки"
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                check=models.Q(capacity__gt=0),
                name="capacity_positive"
            ),
            models.CheckConstraint(
                check=models.Q(voltage__gt=0) | models.Q(voltage__isnull=True),
                name="voltage_positive"
            )
        ]

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Корзина пользователя {self.user.username}"
    
    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())
    
    class Meta:
        verbose_name = "Корзина"
        verbose_name_plural = "Корзины"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    battery = models.ForeignKey(Battery, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.battery} x {self.quantity}"
    
    @property
    def total_price(self):
        # Проверяем крупный опт
        if (self.battery.large_wholesale_quantity is not None and 
            self.battery.large_wholesale_price is not None and 
            self.quantity >= self.battery.large_wholesale_quantity):
            return self.quantity * self.battery.large_wholesale_price
        
        # Проверяем мелкий опт
        if (self.battery.small_wholesale_quantity is not None and 
            self.battery.small_wholesale_price is not None and 
            self.quantity >= self.battery.small_wholesale_quantity):
            return self.quantity * self.battery.small_wholesale_price
        
        # Возвращаем розничную цену
        return self.quantity * self.battery.price
    
    class Meta:
        verbose_name = "Товар в корзине"
        verbose_name_plural = "Товары в корзине"
        unique_together = ['cart', 'battery']

class Shipment(models.Model):
    STATUS_CHOICES = [
        ('created', 'Создана'),
        ('in_progress', 'В обработке'),
        ('completed', 'Завершена'),
        ('cancelled', 'Отменена'),
    ]
    
    battery = models.ForeignKey(Battery, on_delete=models.CASCADE, verbose_name='Товар')
    quantity = models.PositiveIntegerField(verbose_name='Количество')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Создал')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='created', verbose_name='Статус')
    
    def __str__(self):
        return f"Партия {self.battery} - {self.quantity} шт."
    
    @property
    def total_price(self):
        # Проверяем крупный опт
        if (self.battery.large_wholesale_quantity is not None and 
            self.battery.large_wholesale_price is not None and 
            self.quantity >= self.battery.large_wholesale_quantity):
            return self.quantity * self.battery.large_wholesale_price
        
        # Проверяем мелкий опт
        if (self.battery.small_wholesale_quantity is not None and 
            self.battery.small_wholesale_price is not None and 
            self.quantity >= self.battery.small_wholesale_quantity):
            return self.quantity * self.battery.small_wholesale_price
        
        # Возвращаем розничную цену
        return self.quantity * self.battery.price
    
    class Meta:
        verbose_name = 'Партия товара'
        verbose_name_plural = 'Партии товара'
        ordering = ['-created_at']
