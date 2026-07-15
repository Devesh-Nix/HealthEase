from datetime import timedelta

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.utils import timezone

from ambulance.models import AmbulanceBooking
from appointments.models import Appointment
from doctors.models import Doctor
from medicines.models import MedicineOrder
from patients.models import Patient
from services.models import ServiceBooking


@staff_member_required
def superadmin_dashboard(request):
    doctor_count = Doctor.objects.count()
    patient_count = Patient.objects.count()
    appointment_count = Appointment.objects.count()
    ambulance_count = AmbulanceBooking.objects.count()
    medicine_orders = MedicineOrder.objects.count()
    service_bookings = ServiceBooking.objects.count()

    unconfirmed_appointments = Appointment.objects.filter(confirmed=False).count()
    pending_ambulances = AmbulanceBooking.objects.filter(status='Pending').count()

    today = timezone.now().date()
    trend_labels = []
    trend_data = []
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        next_day = day + timedelta(days=1)
        trend_labels.append(day.strftime('%d %b'))
        day_total = (
            Appointment.objects.filter(created_at__gte=day, created_at__lt=next_day).count()
            + AmbulanceBooking.objects.filter(booked_at__gte=day, booked_at__lt=next_day).count()
            + MedicineOrder.objects.filter(ordered_at__gte=day, ordered_at__lt=next_day).count()
            + ServiceBooking.objects.filter(booked_at__gte=day, booked_at__lt=next_day).count()
        )
        trend_data.append(day_total)

    context = {
        'doctor_count': doctor_count,
        'patient_count': patient_count,
        'appointment_count': appointment_count,
        'ambulance_count': ambulance_count,
        'medicine_orders': medicine_orders,
        'service_bookings': service_bookings,
        'unconfirmed_appointments': unconfirmed_appointments,
        'pending_ambulances': pending_ambulances,
        'trend_labels': trend_labels,
        'trend_data': trend_data,
    }
    latest_appointments = Appointment.objects.order_by('-created_at')[:5]
    latest_ambulances = AmbulanceBooking.objects.order_by('-booked_at')[:5]
    latest_medicines = MedicineOrder.objects.order_by('-ordered_at')[:5]
    latest_services = ServiceBooking.objects.order_by('-booked_at')[:5]

    recent_activities = []

    for app in latest_appointments:
        recent_activities.append({
            'timestamp': app.created_at,
            'icon': '📋',
            'text': (
                f"Appointment: {app.patient.full_name} with Dr. {app.doctor.full_name} "
                f"on {app.appointment_date}"
            ),
        })
    for amb in latest_ambulances:
        recent_activities.append({
            'timestamp': amb.booked_at,
            'icon': '🚑',
            'text': f"Ambulance booked by: {amb.patient_name} ({amb.get_emergency_type_display()})",
        })
    for med in latest_medicines:
        recent_activities.append({
            'timestamp': med.ordered_at,
            'icon': '💊',
            'text': f"Medicine order placed by: {med.full_name}",
        })
    for serv in latest_services:
        recent_activities.append({
            'timestamp': serv.booked_at,
            'icon': '🏠',
            'text': f"Home service booked by: {serv.client_name}",
        })

    recent_activities = sorted(recent_activities, key=lambda x: x['timestamp'], reverse=True)[:10]
    context['recent_activities'] = recent_activities

    return render(request, 'superadmin_dashboard.html', context)
