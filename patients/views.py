from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .models import Patient, PatientHistory

@login_required
def clinician_dashboard(request):
    patients = Patient.objects.filter(clinician=request.user)
    return render(request, 'clinician_dashboard.html', {'patients': patients})

@login_required
def add_patient(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        dob = request.POST.get('dob')
        gender = request.POST.get('gender')
        email = request.POST.get('email', '').strip()

        if not full_name or not dob or gender not in {'Male', 'Female', 'Other'}:
            messages.error(request, "Please provide valid patient details.")
            return redirect('add_patient')

        Patient.objects.create(
            clinician=request.user,
            full_name=full_name,
            dob=dob,
            gender=gender,
            email=email
        )
        messages.success(request, "Patient added successfully.")
        return redirect('add_patient')

    return render(request, 'add_patient.html')

@login_required
def select_test(request):
    patients = Patient.objects.filter(clinician=request.user)

    if request.method == 'POST':
        patient_id = request.POST.get('patient_id')
        test_name = request.POST['test_name']

        selected_patient = patients.filter(id=patient_id).first()
        if not selected_patient:
            messages.error(request, "Invalid patient selected.")
            return redirect('select_test')

        if test_name == "MCMI-III":
            return redirect('take_test', patient_id=selected_patient.id)

        messages.warning(request, "This test is not available yet.")
        return redirect('select_test')

    return render(request, 'select_test.html', {"patients": patients})

@login_required
def add_patient_history(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)

    if not request.user.is_staff and patient.clinician_id != request.user.id:
        messages.error(request, "You are not allowed to modify this patient.")
        return redirect('clinician_dashboard')

    if request.method == 'POST':
        condition_title = request.POST.get('condition_title', '').strip()
        description = request.POST.get('description', '').strip()
        prescribed_treatment = request.POST.get('prescribed_treatment', '').strip()
        diagnosed_by = request.POST.get('diagnosed_by', '').strip()

        if not condition_title or not description:
            messages.error(request, "Condition title and description are required.")
            return redirect('add_patient_history', patient_id=patient.id)

        PatientHistory.objects.create(
            patient=patient,
            condition_title=condition_title,
            description=description,
            prescribed_treatment=prescribed_treatment or None,
            diagnosed_by=diagnosed_by or None,
        )
        messages.success(request, "Patient history added successfully.")
        return redirect('patient_detail', patient_id=patient.id)

    return render(request, 'add_history.html', {'patient': patient})

@login_required
def patient_detail(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)

    if not request.user.is_staff and patient.clinician_id != request.user.id:
        messages.error(request, "You are not allowed to view this patient.")
        return redirect('clinician_dashboard')

    histories = patient.histories.all().order_by('-date_recorded')  # Latest first

    return render(request, 'patient_detail.html', {
        'patient': patient,
        'histories': histories,
    })

@login_required
def patient_dashboard(request):
    return render(request, 'patient_dashboard.html')