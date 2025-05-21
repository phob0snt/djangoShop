from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from catalog.models import Battery, BatteryType, UserRole, Shipment

class ShipmentTest(TestCase):
    def setUp(self):
        """Подготовка тестовых данных"""
        # Создаем пользователей с разными ролями
        self.admin = User.objects.create_user(username='admin', password='admin123')
        self.sales_manager1 = User.objects.create_user(username='sales_manager1', password='sales123')
        self.sales_manager2 = User.objects.create_user(username='sales_manager2', password='sales123')
        self.merchandiser = User.objects.create_user(username='merchandiser', password='merch123')
        
        # Создаем роли для пользователей
        UserRole.objects.create(user=self.admin, role='admin')
        UserRole.objects.create(user=self.sales_manager1, role='sales_manager')
        UserRole.objects.create(user=self.sales_manager2, role='sales_manager')
        UserRole.objects.create(user=self.merchandiser, role='merchandiser')
        
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
            small_wholesale_price=90,
            small_wholesale_quantity=5,
            large_wholesale_price=80,
            large_wholesale_quantity=10,
            stock=20,
            description="Тестовая батарейка"
        )
        
        self.client = Client()

    def test_create_shipment(self):
        """Тест создания партии товара"""
        self.client.login(username='sales_manager1', password='sales123')
        
        # Создаем партию
        response = self.client.post(
            reverse('catalog:create_shipment'),
            {
                'battery': self.battery.id,
                'quantity': 5
            }
        )
        self.assertEqual(response.status_code, 302)  # Редирект на список партий
        
        # Проверяем, что партия создалась
        shipment = Shipment.objects.first()
        self.assertEqual(shipment.battery, self.battery)
        self.assertEqual(shipment.quantity, 5)
        self.assertEqual(shipment.created_by, self.sales_manager1)
        
        # Проверяем, что количество на складе уменьшилось
        self.battery.refresh_from_db()
        self.assertEqual(self.battery.stock, 15)

    def test_create_shipment_insufficient_stock(self):
        """Тест создания партии с недостаточным количеством товара"""
        self.client.login(username='sales_manager1', password='sales123')
        
        # Пытаемся создать партию с количеством больше, чем есть на складе
        response = self.client.post(
            reverse('catalog:create_shipment'),
            {
                'battery': self.battery.id,
                'quantity': 25  # На складе только 20
            }
        )
        self.assertEqual(response.status_code, 200)  # Остаемся на странице создания
        
        # Проверяем, что партия не создалась
        self.assertEqual(Shipment.objects.count(), 0)
        
        # Проверяем, что количество на складе не изменилось
        self.battery.refresh_from_db()
        self.assertEqual(self.battery.stock, 20)

    def test_delete_shipment(self):
        """Тест удаления партии товара"""
        self.client.login(username='sales_manager1', password='sales123')
        
        # Создаем партию
        shipment = Shipment.objects.create(
            battery=self.battery,
            quantity=5,
            created_by=self.sales_manager1
        )
        self.battery.stock -= 5
        self.battery.save()
        
        # Удаляем партию
        response = self.client.post(
            reverse('catalog:delete_shipment', kwargs={'pk': shipment.pk})
        )
        self.assertEqual(response.status_code, 302)  # Редирект на список партий
        
        # Проверяем, что партия удалилась
        self.assertEqual(Shipment.objects.count(), 0)
        
        # Проверяем, что количество на складе вернулось
        self.battery.refresh_from_db()
        self.assertEqual(self.battery.stock, 20)

    def test_delete_other_manager_shipment(self):
        """Тест попытки удаления чужой партии менеджером"""
        self.client.login(username='sales_manager1', password='sales123')
        
        # Создаем партию от имени другого менеджера
        shipment = Shipment.objects.create(
            battery=self.battery,
            quantity=5,
            created_by=self.sales_manager2
        )
        self.battery.stock -= 5
        self.battery.save()
        
        # Пытаемся удалить чужую партию
        response = self.client.post(
            reverse('catalog:delete_shipment', kwargs={'pk': shipment.pk})
        )
        self.assertEqual(response.status_code, 302)  # Редирект на список партий
        
        # Проверяем, что партия не удалилась
        self.assertEqual(Shipment.objects.count(), 1)
        
        # Проверяем, что количество на складе не изменилось
        self.battery.refresh_from_db()
        self.assertEqual(self.battery.stock, 15)

    def test_admin_delete_any_shipment(self):
        """Тест удаления любой партии администратором"""
        self.client.login(username='admin', password='admin123')
        
        # Создаем партию от имени менеджера
        shipment = Shipment.objects.create(
            battery=self.battery,
            quantity=5,
            created_by=self.sales_manager1
        )
        self.battery.stock -= 5
        self.battery.save()
        
        # Администратор удаляет партию
        response = self.client.post(
            reverse('catalog:delete_shipment', kwargs={'pk': shipment.pk})
        )
        self.assertEqual(response.status_code, 302)  # Редирект на список партий
        
        # Проверяем, что партия удалилась
        self.assertEqual(Shipment.objects.count(), 0)
        
        # Проверяем, что количество на складе вернулось
        self.battery.refresh_from_db()
        self.assertEqual(self.battery.stock, 20)

    def test_merchandiser_cannot_create_shipment(self):
        """Тест запрета создания партии товароведом"""
        self.client.login(username='merchandiser', password='merch123')
        
        # Пытаемся создать партию
        response = self.client.post(
            reverse('catalog:create_shipment'),
            {
                'battery': self.battery.id,
                'quantity': 5
            }
        )
        self.assertEqual(response.status_code, 302)  # Редирект на главную
        
        # Проверяем, что партия не создалась
        self.assertEqual(Shipment.objects.count(), 0)
        
        # Проверяем, что количество на складе не изменилось
        self.battery.refresh_from_db()
        self.assertEqual(self.battery.stock, 20)

    def test_shipment_list_view(self):
        """Тест отображения списка партий"""
        self.client.login(username='sales_manager1', password='sales123')
        
        # Создаем несколько партий
        Shipment.objects.create(
            battery=self.battery,
            quantity=5,
            created_by=self.sales_manager1
        )
        Shipment.objects.create(
            battery=self.battery,
            quantity=3,
            created_by=self.sales_manager2
        )
        
        # Проверяем отображение списка партий
        response = self.client.get(reverse('catalog:shipments'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'TestBrand')
        self.assertContains(response, '5 шт.')
        self.assertContains(response, '3 шт.')

    def test_shipment_price_calculation(self):
        """Тест расчета стоимости партии с учетом оптовых цен"""
        # Создаем партию с розничной ценой
        shipment1 = Shipment.objects.create(
            battery=self.battery,
            quantity=3,  # Меньше мелкого опта
            created_by=self.sales_manager1
        )
        self.assertEqual(float(shipment1.total_price), 300)  # 3 * 100
        
        # Создаем партию с мелким оптом
        shipment2 = Shipment.objects.create(
            battery=self.battery,
            quantity=7,  # Больше мелкого опта, но меньше крупного
            created_by=self.sales_manager1
        )
        self.assertEqual(float(shipment2.total_price), 630)  # 7 * 90
        
        # Создаем партию с крупным оптом
        shipment3 = Shipment.objects.create(
            battery=self.battery,
            quantity=12,  # Больше крупного опта
            created_by=self.sales_manager1
        )
        self.assertEqual(float(shipment3.total_price), 960)  # 12 * 80 