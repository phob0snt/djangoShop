from django.test import TestCase, Client
from django.urls import reverse
from catalog.models import Battery, BatteryType

class RoutesTest(TestCase):
    def setUp(self):
        """Подготовка тестовых данных"""
        self.client = Client()
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

    def test_home_page(self):
        """Тест главной страницы"""
        response = self.client.get(reverse('catalog:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/home.html')
        self.assertContains(response, "Каталог батареек")

    def test_battery_detail_page(self):
        """Тест страницы деталей батарейки"""
        response = self.client.get(
            reverse('catalog:battery_detail', kwargs={'pk': self.battery.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/battery_detail.html')
        self.assertContains(response, self.battery.brand)
        self.assertContains(response, self.battery.type.name)

    def test_about_page(self):
        """Тест страницы 'О сервисе'"""
        response = self.client.get(reverse('catalog:about'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'catalog/about.html')
        self.assertContains(response, "О сервисе") 