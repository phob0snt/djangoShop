from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from catalog.models import Battery, BatteryType, UserRole, Cart, CartItem

class UserRolesTest(TestCase):
    def setUp(self):
        """Подготовка тестовых данных"""
        # Создаем пользователей с разными ролями
        self.admin = User.objects.create_user(username='admin', password='admin123')
        self.merchandiser = User.objects.create_user(username='merchandiser', password='merch123')
        self.sales_manager = User.objects.create_user(username='sales_manager', password='sales123')
        self.guest = User.objects.create_user(username='guest', password='guest123')
        
        # Создаем роли для пользователей
        UserRole.objects.create(user=self.admin, role='admin')
        UserRole.objects.create(user=self.merchandiser, role='merchandiser')
        UserRole.objects.create(user=self.sales_manager, role='sales_manager')
        UserRole.objects.create(user=self.guest, role='guest')
        
        # Создаем тестовый товар
        self.battery_type = BatteryType.objects.create(
            name="AA",
            description="Стандартная пальчиковая батарейка"
        )
        self.battery = Battery.objects.create(
            brand="TestBrand",
            type=self.battery_type,
            capacity=2000,
            rechargeable=True,
            voltage=1.5,
            price=100,
            stock=10,
            description="Тестовая батарейка"
        )
        
        self.client = Client()

    def test_guest_permissions(self):
        """Тест прав гостя"""
        # Гость может просматривать каталог
        response = self.client.get(reverse('catalog:home'))
        self.assertEqual(response.status_code, 200)
        
        # Гость может просматривать детали товара
        response = self.client.get(reverse('catalog:battery_detail', kwargs={'pk': self.battery.pk}))
        self.assertEqual(response.status_code, 200)
        
        # Гость не может добавлять товар в корзину
        response = self.client.post(reverse('catalog:add_to_cart', kwargs={'pk': self.battery.pk}))
        self.assertEqual(response.status_code, 302)  # Редирект на страницу входа
        
        # Гость не может создавать партии
        self.client.login(username='guest', password='guest123')
        response = self.client.get(reverse('catalog:create_shipment'))
        self.assertEqual(response.status_code, 302)  # Редирект на главную

    def test_merchandiser_permissions(self):
        """Тест прав товароведа"""
        self.client.login(username='merchandiser', password='merch123')
        
        # Товаровед может редактировать товар
        response = self.client.get(reverse('catalog:edit_battery', kwargs={'pk': self.battery.pk}))
        self.assertEqual(response.status_code, 200)
        
        # Товаровед может обновлять описание и цены
        response = self.client.post(
            reverse('catalog:edit_battery', kwargs={'pk': self.battery.pk}),
            {
                'description': 'Новое описание',
                'price': '150',
                'small_wholesale_price': '140',
                'small_wholesale_quantity': '5',
                'large_wholesale_price': '130',
                'large_wholesale_quantity': '10'
            }
        )
        self.assertEqual(response.status_code, 302)  # Редирект после успешного обновления
        
        # Проверяем, что изменения сохранились
        updated_battery = Battery.objects.get(pk=self.battery.pk)
        self.assertEqual(updated_battery.description, 'Новое описание')
        self.assertEqual(float(updated_battery.price), 150)
        
        # Товаровед не может создавать заказы
        response = self.client.post(reverse('catalog:create_order'))
        self.assertEqual(response.status_code, 302)  # Редирект на главную

    def test_sales_manager_permissions(self):
        """Тест прав менеджера по продажам"""
        self.client.login(username='sales_manager', password='sales123')
        
        # Менеджер может добавлять товар в корзину
        response = self.client.post(
            reverse('catalog:add_to_cart', kwargs={'pk': self.battery.pk}),
            {'quantity': 2}
        )
        self.assertEqual(response.status_code, 302)  # Редирект в корзину
        
        # Проверяем, что товар добавился в корзину
        cart = Cart.objects.get(user=self.sales_manager, is_active=True)
        self.assertEqual(cart.items.count(), 1)
        self.assertEqual(cart.items.first().quantity, 2)
        
        # Менеджер может создавать заказы
        response = self.client.post(reverse('catalog:create_order'))
        self.assertEqual(response.status_code, 302)  # Редирект на главную
        
        # Проверяем, что корзина стала неактивной после создания заказа
        cart.refresh_from_db()
        self.assertFalse(cart.is_active)
        
        # Менеджер не может редактировать товар
        response = self.client.get(reverse('catalog:edit_battery', kwargs={'pk': self.battery.pk}))
        self.assertEqual(response.status_code, 302)  # Редирект на главную

    def test_admin_permissions(self):
        """Тест прав администратора"""
        self.client.login(username='admin', password='admin123')
        
        # Администратор может редактировать товар
        response = self.client.get(reverse('catalog:edit_battery', kwargs={'pk': self.battery.pk}))
        self.assertEqual(response.status_code, 200)
        
        # Администратор может создавать заказы
        response = self.client.post(
            reverse('catalog:add_to_cart', kwargs={'pk': self.battery.pk}),
            {'quantity': 1}
        )
        self.assertEqual(response.status_code, 302)  # Редирект в корзину
        
        response = self.client.post(reverse('catalog:create_order'))
        self.assertEqual(response.status_code, 302)  # Редирект на главную 