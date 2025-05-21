from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from catalog.models import Battery, BatteryType, UserRole, Cart, CartItem

class CartTest(TestCase):
    def setUp(self):
        """Подготовка тестовых данных"""
        # Создаем пользователя
        self.user = User.objects.create_user(username='testuser', password='testpass')
        UserRole.objects.create(user=self.user, role='sales_manager')
        
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
        self.client.login(username='testuser', password='testpass')

    def test_add_to_cart(self):
        """Тест добавления товара в корзину"""
        # Добавляем товар в корзину
        response = self.client.post(
            reverse('catalog:add_to_cart', kwargs={'pk': self.battery.pk}),
            {'quantity': 3}
        )
        self.assertEqual(response.status_code, 302)  # Редирект в корзину
        
        # Проверяем, что товар добавился
        cart = Cart.objects.get(user=self.user, is_active=True)
        self.assertEqual(cart.items.count(), 1)
        cart_item = cart.items.first()
        self.assertEqual(cart_item.quantity, 3)
        self.assertEqual(cart_item.battery, self.battery)

    def test_update_cart_item(self):
        """Тест обновления количества товара в корзине"""
        # Создаем корзину с товаром
        cart = Cart.objects.create(user=self.user)
        cart_item = CartItem.objects.create(cart=cart, battery=self.battery, quantity=2)
        
        # Обновляем количество
        response = self.client.post(
            reverse('catalog:update_cart_item', kwargs={'pk': cart_item.pk}),
            {'quantity': 4}
        )
        self.assertEqual(response.status_code, 302)  # Редирект в корзину
        
        # Проверяем, что количество обновилось
        cart_item.refresh_from_db()
        self.assertEqual(cart_item.quantity, 4)

    def test_remove_from_cart(self):
        """Тест удаления товара из корзины"""
        # Создаем корзину с товаром
        cart = Cart.objects.create(user=self.user)
        cart_item = CartItem.objects.create(cart=cart, battery=self.battery, quantity=2)
        
        # Удаляем товар
        response = self.client.post(
            reverse('catalog:remove_from_cart', kwargs={'pk': cart_item.pk})
        )
        self.assertEqual(response.status_code, 302)  # Редирект в корзину
        
        # Проверяем, что товар удалился
        self.assertEqual(cart.items.count(), 0)

    def test_price_calculation(self):
        """Тест расчета цен с учетом оптовых скидок"""
        # Создаем корзину
        cart = Cart.objects.create(user=self.user)
        
        # Создаем дополнительные товары с разными ценами
        battery2 = Battery.objects.create(
            brand="TestBrand2",
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
            description="Тестовая батарейка 2"
        )
        
        battery3 = Battery.objects.create(
            brand="TestBrand3",
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
            description="Тестовая батарейка 3"
        )
        
        # Тест розничной цены
        cart_item1 = CartItem.objects.create(cart=cart, battery=self.battery, quantity=1)
        self.assertEqual(float(cart_item1.total_price), 100)  # Розничная цена
        
        # Тест мелкого опта
        cart_item2 = CartItem.objects.create(cart=cart, battery=battery2, quantity=5)
        self.assertEqual(float(cart_item2.total_price), 450)  # 5 * 90
        
        # Тест крупного опта
        cart_item3 = CartItem.objects.create(cart=cart, battery=battery3, quantity=10)
        self.assertEqual(float(cart_item3.total_price), 800)  # 10 * 80
        
        # Проверяем общую сумму корзины
        self.assertEqual(float(cart.total_price), 1350)  # 100 + 450 + 800

    def test_stock_validation(self):
        """Тест проверки наличия товара"""
        # Пытаемся добавить больше товара, чем есть на складе
        response = self.client.post(
            reverse('catalog:add_to_cart', kwargs={'pk': self.battery.pk}),
            {'quantity': 25}  # На складе только 20
        )
        self.assertEqual(response.status_code, 302)  # Редирект на страницу товара
        
        # Проверяем, что товар не добавился в корзину
        cart = Cart.objects.filter(user=self.user, is_active=True).first()
        self.assertIsNone(cart)  # Корзина не создалась

    def test_cart_view(self):
        """Тест отображения корзины"""
        # Создаем корзину с товарами
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, battery=self.battery, quantity=2)
        
        # Проверяем отображение корзины
        response = self.client.get(reverse('catalog:cart'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.battery.brand)
        self.assertContains(response, '2')  # Количество
        self.assertContains(response, '200')  # Общая цена (2 * 100) 