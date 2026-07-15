from datetime import date

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render

from doctors.models import Doctor
from patients.models import Patient

from .models import Appointment

@login_required
def book_appointment(request, slug):
    doctor = get_object_or_404(Doctor, slug=slug)

    patients = Patient.objects.all()

    if request.method == 'POST':
        patient_id = request.POST.get('patient')
        appointment_date = request.POST.get('appointment_date')
        appointment_time = request.POST.get('appointment_time')
        mode_of_consultation = request.POST.get('mode_of_consultation')

        patient = get_object_or_404(Patient, id=patient_id)

        if appointment_date and appointment_date < date.today().isoformat():
            messages.error(request, "Appointment date cannot be in the past.")
            return redirect('book_appointment', slug=doctor.slug)

        conflict_exists = Appointment.objects.filter(
            doctor=doctor,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
        ).exists()
        if conflict_exists:
            messages.error(request, "Selected slot is already booked for this doctor.")
            return redirect('book_appointment', slug=doctor.slug)

        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            mode_of_consultation=mode_of_consultation
        )

        if patient.email:
            send_mail(
                subject='Appointment Confirmed',
                message=(
                    f"Dear {appointment.patient.full_name},\n\n"
                    f"Your appointment with Dr. {appointment.doctor.full_name} "
                    f"is confirmed for {appointment.appointment_date} at "
                    f"{appointment.appointment_time}.\n\nThank you!"
                ),
                from_email='noreply@healthcareplatform.com',
                recipient_list=[patient.email],
                fail_silently=True,
            )

        return redirect('appointment_success')

    return render(request, 'book_appointment.html', {'doctor': doctor, 'patients': patients})

@login_required
def appointment_success(request):
    return render(request, 'appointment_success.html')


@login_required
def patient_appointments(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)

    if not request.user.is_staff and patient.clinician_id != request.user.id:
        messages.error(request, "You are not allowed to view this patient's appointments.")
        return redirect('clinician_dashboard')
    
    appointments = Appointment.objects.filter(patient=patient).order_by('appointment_date', 'appointment_time')

    return render(request, 'patient_appointments.html', {
        'patient': patient,
        'appointments': appointments
    })

@login_required
def doctor_appointments(request, doctor_slug):
    doctor = get_object_or_404(Doctor, slug=doctor_slug)

    appointments = Appointment.objects.filter(doctor=doctor).order_by('appointment_date', 'appointment_time')
    
    return render(request, 'doctor_appointments.html', {
        'doctor': doctor,
        'appointments': appointments
    })
