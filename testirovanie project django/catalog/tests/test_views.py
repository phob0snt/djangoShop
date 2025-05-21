from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from catalog.models import Battery, BatteryType, UserRole, Cart, CartItem, Shipment
from decimal import Decimal

class ViewsTest(TestCase):
    def setUp(self):
        """Подготовка тестовых данных"""
        self.client = Client()
        
        # Создаем типы батареек
        self.battery_type = BatteryType.objects.create(
            name="AA",
            description="Стандартная пальчиковая батарейка"
        )
        
        # Создаем батарейку с оптовыми ценами
        self.battery = Battery.objects.create(
            brand="TestBrand",
            type=self.battery_type,
            capacity=2000,
            rechargeable=True,
            voltage=1.5,
            price=100,
            stock=10,
            description="Тестовая батарейка",
            small_wholesale_quantity=5,
            small_wholesale_price=90,
            large_wholesale_quantity=10,
            large_wholesale_price=80
        )
        
        # Создаем пользователей с разными ролями
        self.guest = User.objects.create_user(username='guest', password='guest123')
        self.merchandiser = User.objects.create_user(username='merchandiser', password='merch123')
        self.sales_manager1 = User.objects.create_user(username='manager1', password='manager123')
        self.sales_manager2 = User.objects.create_user(username='manager2', password='manager123')
        self.admin = User.objects.create_user(username='admin', password='admin123')
        
        # Создаем роли для пользователей
        UserRole.objects.create(user=self.guest, role='guest')
        UserRole.objects.create(user=self.merchandiser, role='merchandiser')
        UserRole.objects.create(user=self.sales_manager1, role='sales_manager')
        UserRole.objects.create(user=self.sales_manager2, role='sales_manager')
        UserRole.objects.create(user=self.admin, role='admin')

    def test_guest_access(self):
        """Тест доступа гостя"""
        # Гость может просматривать каталог
        response = self.client.get(reverse('catalog:home'))
        self.assertEqual(response.status_code, 200)
        
        # Гость не может добавлять товар в корзину
        response = self.client.post(reverse('catalog:add_to_cart', kwargs={'pk': self.battery.pk}))
        self.assertEqual(response.status_code, 302)  # Редирект на страницу входа
        
        # Гость может просматривать детали товара
        response = self.client.get(reverse('catalog:battery_detail', kwargs={'pk': self.battery.pk}))
        self.assertEqual(response.status_code, 200)
        
        # Гость не может создавать партии
        self.client.login(username='guest', password='guest123')
        response = self.client.get(reverse('catalog:create_shipment'))
        self.assertEqual(response.status_code, 302)  # Редирект на главную

    def test_merchandiser_access(self):
        """Тест доступа мерчендайзера"""
        self.client.login(username='merchandiser', password='merch123')
        
        # Мерчендайзер может редактировать товар
        response = self.client.get(reverse('catalog:edit_battery', kwargs={'pk': self.battery.pk}))
        self.assertEqual(response.status_code, 200)
        
        # Мерчендайзер не может создавать партии
        response = self.client.get(reverse('catalog:create_shipment'))
        self.assertEqual(response.status_code, 302)  # Редирект на главную

    def test_sales_manager_access(self):
        """Тест доступа менеджера по продажам"""
        self.client.login(username='manager1', password='manager123')
        
        # Менеджер может создавать партии
        response = self.client.get(reverse('catalog:create_shipment'))
        self.assertEqual(response.status_code, 200)
        
        # Создаем партию
        response = self.client.post(reverse('catalog:create_shipment'), {
            'battery': self.battery.pk,
            'quantity': 5
        })
        self.assertEqual(response.status_code, 302)  # Редирект на список партий
        
        shipment = Shipment.objects.first()
        
        # Другой менеджер не может удалить чужую партию
        self.client.login(username='manager2', password='manager123')
        response = self.client.post(reverse('catalog:delete_shipment', kwargs={'pk': shipment.pk}))
        self.assertEqual(response.status_code, 302)  # Редирект на главную
        
        # Создатель может удалить свою партию
        self.client.login(username='manager1', password='manager123')
        response = self.client.post(reverse('catalog:delete_shipment', kwargs={'pk': shipment.pk}))
        self.assertEqual(response.status_code, 302)  # Редирект на список партий
        self.assertEqual(Shipment.objects.count(), 0)

    def test_admin_access(self):
        """Тест доступа администратора"""
        self.client.login(username='admin', password='admin123')
        
        # Админ может создавать партии
        response = self.client.get(reverse('catalog:create_shipment'))
        self.assertEqual(response.status_code, 200)
        
        # Создаем партию
        response = self.client.post(reverse('catalog:create_shipment'), {
            'battery': self.battery.pk,
            'quantity': 5
        })
        self.assertEqual(response.status_code, 302)  # Редирект на список партий
        
        shipment = Shipment.objects.first()
        
        # Админ может удалить любую партию
        response = self.client.post(reverse('catalog:delete_shipment', kwargs={'pk': shipment.pk}))
        self.assertEqual(response.status_code, 302)  # Редирект на список партий
        self.assertEqual(Shipment.objects.count(), 0)

    def test_shipment_calculation(self):
        """Тест расчета стоимости партии"""
        self.client.login(username='manager1', password='manager123')
        
        # Создаем партию с мелким оптом
        response = self.client.post(reverse('catalog:create_shipment'), {
            'battery': self.battery.pk,
            'quantity': 5
        })
        self.assertEqual(response.status_code, 302)  # Редирект на список партий
        
        shipment = Shipment.objects.first()
        self.assertEqual(shipment.total_price, 5 * 90)  # 5 шт. * 90 руб.
        
        # Для крупного опта создаём новую батарейку с нужным stock
        battery2 = Battery.objects.create(
            brand="TestBrand2",
            type=self.battery.type,
            capacity=2000,
            rechargeable=True,
            voltage=1.5,
            price=100,
            stock=20,
            description="Тестовая батарейка 2",
            small_wholesale_price=90,
            small_wholesale_quantity=5,
            large_wholesale_price=80,
            large_wholesale_quantity=10
        )
        
        # Создаем партию с крупным оптом
        response = self.client.post(reverse('catalog:create_shipment'), {
            'battery': battery2.pk,
            'quantity': 10
        })
        self.assertEqual(response.status_code, 302)  # Редирект на список партий
        
        # Получаем последнюю партию для battery2
        shipment = Shipment.objects.filter(battery=battery2).order_by('-created_at').first()
        self.assertEqual(shipment.total_price, 10 * 80)  # 10 шт. * 80 руб.

    def test_cart_functionality(self):
        """Тест функциональности корзины"""
        self.client.login(username='guest', password='guest123')
        
        # Добавляем товар в корзину
        response = self.client.post(reverse('catalog:add_to_cart', kwargs={'pk': self.battery.pk}), {
            'quantity': 3
        })
        self.assertEqual(response.status_code, 302)  # Редирект на корзину
        
        # Проверяем корзину
        response = self.client.get(reverse('catalog:cart'))
        self.assertEqual(response.status_code, 200)
        
        cart = Cart.objects.get(user=self.guest)
        self.assertEqual(cart.items.count(), 1)
        self.assertEqual(cart.items.first().quantity, 3)
        self.assertEqual(cart.items.first().total_price, 3 * 100)  # 3 шт. * 100 руб. 