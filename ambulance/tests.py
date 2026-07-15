from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import AmbulanceBooking, AmbulanceService


User = get_user_model()


class AmbulanceBookingTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(
			username='patient1',
			password='testpass123',
			email='patient1@example.com',
			is_patient=True,
		)
		self.service = AmbulanceService.objects.create(
			provider_name='City Ambulance',
			contact_number='9999999999',
			available=True,
			location_city='Delhi',
			base_price='500.00',
		)

	def test_booking_requires_login(self):
		response = self.client.post(
			reverse('book_ambulance', kwargs={'ambulance_id': self.service.id}),
			{
				'patient_name': 'John',
				'phone': '9999999999',
				'pickup_address': 'Somewhere',
				'emergency_type': 'normal',
			},
		)

		self.assertEqual(response.status_code, 302)
		self.assertIn('/accounts/login/', response.url)

	def test_booking_creates_record_for_logged_in_user(self):
		self.client.force_login(self.user)
		response = self.client.post(
			reverse('book_ambulance', kwargs={'ambulance_id': self.service.id}),
			{
				'patient_name': 'John',
				'phone': '9999999999',
				'pickup_address': 'Somewhere',
				'emergency_type': 'critical',
			},
		)

		self.assertRedirects(response, reverse('ambulance_services'))
		self.assertEqual(AmbulanceBooking.objects.count(), 1)
