from django.contrib.auth import get_user_model
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse

from .models import ServiceBooking, ServiceProvider


User = get_user_model()


class ServiceBookingTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(
			username='patient2',
			password='testpass123',
			email='patient2@example.com',
			is_patient=True,
		)
		self.provider = ServiceProvider.objects.create(
			full_name='Nurse Anna',
			service_type='nurse',
			experience_years=5,
			hourly_rate='300.00',
			city='Delhi',
			contact_number='8888888888',
			available=True,
		)

	def test_booking_requires_login(self):
		response = self.client.post(
			reverse('book_service', kwargs={'service_id': self.provider.id}),
			{
				'client_name': 'Alex',
				'client_phone': '7777777777',
				'address': 'Street 12',
				'date': '2026-07-20',
				'start_time': '10:00',
				'duration_hours': '3',
			},
		)

		self.assertEqual(response.status_code, 302)
		self.assertIn('/accounts/login/', response.url)

	def test_booking_calculates_total_cost(self):
		self.client.force_login(self.user)
		response = self.client.post(
			reverse('book_service', kwargs={'service_id': self.provider.id}),
			{
				'client_name': 'Alex',
				'client_phone': '7777777777',
				'address': 'Street 12',
				'date': '2026-07-20',
				'start_time': '10:00',
				'duration_hours': '3',
			},
		)

		self.assertRedirects(response, reverse('service_list'))
		booking = ServiceBooking.objects.get()
		self.assertEqual(booking.total_cost, Decimal('900.00'))
