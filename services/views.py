from django.shortcuts import render, redirect, get_object_or_404
from .models import ServiceProvider, ServiceBooking
from django.contrib import messages
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required

def service_list(request):
    services = ServiceProvider.objects.filter(available=True)
    return render(request, 'service_list.html', {'services': services})

@login_required
def book_service(request, service_id):
    service_provider = get_object_or_404(ServiceProvider, id=service_id)

    if request.method == 'POST':
        client_name = request.POST['client_name']
        client_phone = request.POST['client_phone']
        address = request.POST['address']
        date = request.POST['date']
        start_time = request.POST['start_time']
        duration_hours = int(request.POST['duration_hours'])

        total_cost = duration_hours * service_provider.hourly_rate

        booking = ServiceBooking.objects.create(
            client_name=client_name,
            client_phone=client_phone,
            address=address,
            service_provider=service_provider,
            date=date,
            start_time=start_time,
            duration_hours=duration_hours,
            total_cost=total_cost
        )
        if request.user.email:
            send_mail(
                subject='Service Booking Confirmation',
                message=(
                    f"Dear {booking.client_name},\n\n"
                    f"Your booking for {booking.service_provider.full_name} "
                    f"has been confirmed for {booking.date} at {booking.start_time}.\n\n"
                    "Thank you!"
                ),
                from_email='noreply@healthcareplatform.com',
                recipient_list=[request.user.email],
                fail_silently=True,
            )


        messages.success(request, "✅ Service booked successfully!")
        return redirect('service_list')

    return render(request, 'book_service.html', {'service_provider': service_provider})
