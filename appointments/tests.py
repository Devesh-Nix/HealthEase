from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from doctors.models import Doctor
from patients.models import Patient

from .models import Appointment


User = get_user_model()


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class AppointmentViewsTests(TestCase):
	def setUp(self):
		self.clinician = User.objects.create_user(
			username='clinician1',
			password='testpass123',
			is_clinician=True,
		)
		self.other_clinician = User.objects.create_user(
			username='clinician2',
			password='testpass123',
			is_clinician=True,
		)
		self.patient = Patient.objects.create(
			clinician=self.clinician,
			full_name='John Doe',
			dob='1990-01-01',
			gender='Male',
			email='john@example.com',
		)
		self.doctor = Doctor.objects.create(
			full_name='Jane Smith',
			specialization='Cardiology',
			experience_years=7,
			clinic_address='Main Road',
			city='Delhi',
			available_for='video',
			phone_number='9999999999',
			consultation_fee='1500.00',
		)

	def test_book_appointment_creates_record_and_sends_patient_email(self):
		self.client.force_login(self.clinician)
		response = self.client.post(
			reverse('book_appointment', kwargs={'slug': self.doctor.slug}),
			{
				'patient': self.patient.id,
				'appointment_date': (date.today() + timedelta(days=1)).isoformat(),
				'appointment_time': '10:30',
				'mode_of_consultation': 'video',
			},
		)

		self.assertRedirects(response, reverse('appointment_success'))
		self.assertEqual(Appointment.objects.count(), 1)
		self.assertEqual(len(mail.outbox), 1)
		self.assertEqual(mail.outbox[0].to, ['john@example.com'])

	def test_book_appointment_rejects_duplicate_doctor_slot(self):
		self.client.force_login(self.clinician)
		slot_date = date.today() + timedelta(days=1)
		Appointment.objects.create(
			patient=self.patient,
			doctor=self.doctor,
			appointment_date=slot_date,
			appointment_time='11:00',
			mode_of_consultation='chat',
		)

		response = self.client.post(
			reverse('book_appointment', kwargs={'slug': self.doctor.slug}),
			{
				'patient': self.patient.id,
				'appointment_date': slot_date.isoformat(),
				'appointment_time': '11:00',
				'mode_of_consultation': 'physical',
			},
		)

		self.assertRedirects(response, reverse('book_appointment', kwargs={'slug': self.doctor.slug}))
		self.assertEqual(Appointment.objects.count(), 1)

	def test_patient_appointments_denies_other_clinician(self):
		self.client.force_login(self.other_clinician)

		response = self.client.get(reverse('patient_appointments', kwargs={'patient_id': self.patient.id}))

		self.assertRedirects(response, reverse('clinician_dashboard'))

	def test_patient_appointments_allows_owner_clinician(self):
		self.client.force_login(self.clinician)

		response = self.client.get(reverse('patient_appointments', kwargs={'patient_id': self.patient.id}))

		self.assertEqual(response.status_code, 200)
