from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Patient, PatientHistory


User = get_user_model()


class PatientAccessControlTests(TestCase):
	def setUp(self):
		self.owner = User.objects.create_user(
			username='owner',
			password='testpass123',
			is_clinician=True,
		)
		self.other = User.objects.create_user(
			username='other',
			password='testpass123',
			is_clinician=True,
		)
		self.patient = Patient.objects.create(
			clinician=self.owner,
			full_name='A Patient',
			dob='1991-01-01',
			gender='Male',
			email='a@example.com',
		)

	def test_patient_detail_denies_non_owner(self):
		self.client.force_login(self.other)

		response = self.client.get(reverse('patient_detail', kwargs={'patient_id': self.patient.id}))

		self.assertRedirects(response, reverse('clinician_dashboard'))

	def test_add_patient_history_denies_non_owner(self):
		self.client.force_login(self.other)

		response = self.client.post(
			reverse('add_patient_history', kwargs={'patient_id': self.patient.id}),
			{
				'condition_title': 'Condition',
				'description': 'Description',
			},
		)

		self.assertRedirects(response, reverse('clinician_dashboard'))
		self.assertEqual(PatientHistory.objects.count(), 0)

	def test_add_patient_requires_valid_gender(self):
		self.client.force_login(self.owner)

		response = self.client.post(
			reverse('add_patient'),
			{
				'full_name': 'Bad Data',
				'dob': '1990-01-01',
				'gender': 'Unknown',
				'email': 'bad@example.com',
			},
		)

		self.assertRedirects(response, reverse('add_patient'))
		self.assertEqual(Patient.objects.filter(full_name='Bad Data').count(), 0)

	def test_select_test_rejects_non_owned_patient(self):
		self.client.force_login(self.other)

		response = self.client.post(
			reverse('select_test'),
			{
				'patient_id': self.patient.id,
				'test_name': 'MCMI-III',
			},
		)

		self.assertRedirects(response, reverse('select_test'))
