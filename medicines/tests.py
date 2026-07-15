from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Medicine, MedicineOrder, MedicineOrderItem


User = get_user_model()


class MedicineOrderFlowTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(
			username='patientuser',
			password='testpass123',
			email='patient@example.com',
			is_patient=True,
		)
		self.medicine = Medicine.objects.create(
			name='Paracetamol',
			description='Pain relief',
			available_quantity=5,
			price='10.00',
		)

	def test_place_order_creates_items_and_reduces_stock(self):
		self.client.force_login(self.user)
		session = self.client.session
		session['cart'] = {str(self.medicine.id): 2}
		session.save()

		response = self.client.post(
			reverse('place_order'),
			{
				'full_name': 'Alex',
				'address': 'Street 1',
				'phone': '9999999999',
			},
		)

		self.assertRedirects(response, reverse('medicine_list'))
		self.assertEqual(MedicineOrder.objects.count(), 1)
		self.assertEqual(MedicineOrderItem.objects.count(), 1)
		self.medicine.refresh_from_db()
		self.assertEqual(self.medicine.available_quantity, 3)

	def test_place_order_rejects_when_stock_is_insufficient(self):
		self.client.force_login(self.user)
		session = self.client.session
		session['cart'] = {str(self.medicine.id): 9}
		session.save()

		response = self.client.post(
			reverse('place_order'),
			{
				'full_name': 'Alex',
				'address': 'Street 1',
				'phone': '9999999999',
			},
		)

		self.assertRedirects(response, reverse('view_cart'))
		self.assertEqual(MedicineOrder.objects.count(), 0)
		self.assertEqual(MedicineOrderItem.objects.count(), 0)
		self.medicine.refresh_from_db()
		self.assertEqual(self.medicine.available_quantity, 5)
