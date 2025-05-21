from django.test import TestCase, Client
from django.urls import reverse
from catalog.models import Battery, BatteryType

class ContentTest(TestCase):
    def setUp(self):
        """Подготовка тестовых данных"""
        self.client = Client()
        self.type_aa = BatteryType.objects.create(
            name="AA",
            description="Пальчиковая батарейка"
        )
        self.type_aaa = BatteryType.objects.create(
            name="AAA",
            description="Мизинчиковая батарейка"
        )
        self.battery1 = Battery.objects.create(
            brand="BrandA",
            type=self.type_aa,
            capacity=2000,
            rechargeable=True,
            voltage=1.5,
            price=100,
            stock=10,
            description="Тестовая батарейка 1"
        )
        self.battery2 = Battery.objects.create(
            brand="BrandB",
            type=self.type_aaa,
            capacity=1000,
            rechargeable=False,
            voltage=1.5,
            price=50,
            stock=20,
            description="Тестовая батарейка 2"
        )

    def test_battery_creation(self):
        """Тест создания батареек"""
        self.assertEqual(Battery.objects.count(), 2)
        self.assertEqual(self.battery1.brand, "BrandA")
        self.assertEqual(self.battery2.brand, "BrandB")
        self.assertEqual(self.battery1.type, self.type_aa)
        self.assertEqual(self.battery2.type, self.type_aaa)

    def test_alphabetical_sorting(self):
        """Тест сортировки по алфавиту"""
        response = self.client.get(reverse('catalog:home'))
        batteries = response.context['batteries']
        self.assertEqual(batteries[0].brand, "BrandA")
        self.assertEqual(batteries[1].brand, "BrandB")

    def test_price_sorting(self):
        """Тест сортировки по цене"""
        response = self.client.get(reverse('catalog:home') + '?sort=price')
        batteries = response.context['batteries']
        self.assertEqual(batteries[0].price, 50)
        self.assertEqual(batteries[1].price, 100)

    def test_capacity_sorting(self):
        """Тест сортировки по ёмкости"""
        response = self.client.get(reverse('catalog:home') + '?sort=capacity')
        batteries = response.context['batteries']
        self.assertEqual(batteries[0].capacity, 1000)
        self.assertEqual(batteries[1].capacity, 2000)

    def test_type_grouping(self):
        """Тест группировки по типу"""
        response = self.client.get(reverse('catalog:home') + '?group_by=type')
        batteries = response.context['batteries']
        self.assertEqual(batteries[0].type, self.type_aa)
        self.assertEqual(batteries[1].type, self.type_aaa)

    def test_rechargeable_grouping(self):
        """Тест группировки по перезаряжаемости"""
        response = self.client.get(reverse('catalog:home') + '?group_by=rechargeable')
        batteries = response.context['batteries']
        self.assertEqual(batteries[0].rechargeable, False)
        self.assertEqual(batteries[1].rechargeable, True)

    def test_voltage_grouping(self):
        """Тест группировки по напряжению"""
        response = self.client.get(reverse('catalog:home') + '?group_by=voltage')
        batteries = response.context['batteries']
        self.assertEqual(batteries[0].voltage, 1.5)
        self.assertEqual(batteries[1].voltage, 1.5) 