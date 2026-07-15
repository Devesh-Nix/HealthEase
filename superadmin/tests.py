from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from ambulance.models import AmbulanceBooking, AmbulanceService
from appointments.models import Appointment
from doctors.models import Doctor
from medicines.models import MedicineOrder
from patients.models import Patient
from services.models import ServiceBooking, ServiceProvider


User = get_user_model()


class SuperadminDashboardTests(TestCase):
	def setUp(self):
		self.staff_user = User.objects.create_user(
			username='adminuser',
			password='testpass123',
			is_staff=True,
		)
		self.non_staff = User.objects.create_user(
			username='regularuser',
			password='testpass123',
		)
		clinician = User.objects.create_user(
			username='clinician',
			password='testpass123',
			is_clinician=True,
		)
		patient = Patient.objects.create(
			clinician=clinician,
			full_name='Patient One',
			dob='1990-01-01',
			gender='Male',
			email='patient@example.com',
		)
		doctor = Doctor.objects.create(
			full_name='Doctor One',
			specialization='Cardiology',
			experience_years=8,
			clinic_address='Road 1',
			city='Delhi',
			available_for='video',
			phone_number='9999999999',
			consultation_fee='1200.00',
		)
		Appointment.objects.create(
			patient=patient,
			doctor=doctor,
			appointment_date='2026-07-20',
			appointment_time='10:00',
			mode_of_consultation='chat',
			confirmed=False,
		)
		ambulance = AmbulanceService.objects.create(
			provider_name='FastAid',
			contact_number='8888888888',
			available=True,
			location_city='Delhi',
			base_price='500.00',
		)
		AmbulanceBooking.objects.create(
			patient_name='Patient One',
			phone='7777777777',
			pickup_address='Street 1',
			emergency_type='critical',
			ambulance_service=ambulance,
			status='Pending',
		)
		MedicineOrder.objects.create(
			full_name='Patient One',
			address='Street 1',
			phone='7777777777',
		)
		service = ServiceProvider.objects.create(
			full_name='Nurse Mary',
			service_type='nurse',
			experience_years=4,
			hourly_rate='300.00',
			city='Delhi',
			contact_number='6666666666',
			available=True,
		)
		ServiceBooking.objects.create(
			client_name='Patient One',
			client_phone='7777777777',
			address='Street 1',
			service_provider=service,
			date='2026-07-20',
			start_time='09:00',
			duration_hours=2,
			total_cost='600.00',
		)

	def test_non_staff_user_cannot_access_dashboard(self):
		self.client.force_login(self.non_staff)

		response = self.client.get(reverse('superadmin_dashboard'))

		self.assertEqual(response.status_code, 302)

	def test_staff_user_gets_dashboard_with_context(self):
		self.client.force_login(self.staff_user)

		response = self.client.get(reverse('superadmin_dashboard'))

		self.assertEqual(response.status_code, 200)
		self.assertIn('recent_activities', response.context)
		self.assertGreaterEqual(len(response.context['recent_activities']), 1)
		self.assertEqual(response.context['unconfirmed_appointments'], 1)
		self.assertEqual(response.context['pending_ambulances'], 1)
