from django.test import TestCase
from django.urls import reverse


class ShopTests(TestCase):

    def test_home(self):
        response = self.client.get(
            reverse("shop:home")
        )
        self.assertEqual(response.status_code, 200)

    def test_product_list(self):
        response = self.client.get(
            reverse("shop:products")
        )
        self.assertEqual(response.status_code, 200)

    def test_search(self):
        response = self.client.get(
            reverse("shop:search")
        )
        self.assertEqual(response.status_code, 200)
