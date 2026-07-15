from django.shortcuts import render, redirect
from .models import Medicine, MedicineOrder, MedicineOrderItem
from django.contrib import messages
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from django.db import transaction

def medicine_list(request):
    query = request.GET.get('q')
    if query:
        medicines = Medicine.objects.filter(name__icontains=query)
    else:
        medicines = Medicine.objects.all()
    return render(request, 'medicine_list.html', {'medicines': medicines})

@login_required
def add_to_cart(request, medicine_id):
    cart = request.session.get('cart', {})
    cart[str(medicine_id)] = cart.get(str(medicine_id), 0) + 1
    request.session['cart'] = cart
    messages.success(request, "Medicine added to cart.")
    return redirect('medicine_list')

@login_required
def view_cart(request):
    cart = request.session.get('cart', {})
    medicine_ids = cart.keys()
    medicines = Medicine.objects.filter(id__in=medicine_ids)

    cart_items = []
    total = 0
    for med in medicines:
        quantity = cart[str(med.id)]
        subtotal = med.price * quantity
        cart_items.append({'medicine': med, 'quantity': quantity, 'subtotal': subtotal})
        total += subtotal

    return render(request, 'view_cart.html', {'cart_items': cart_items, 'total': total})

@login_required
def place_order(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, "Cart is empty.")
        return redirect('medicine_list')

    if request.method == 'POST':
        full_name = request.POST['full_name']
        address = request.POST['address']
        phone = request.POST['phone']

        with transaction.atomic():
            medicine_ids = [int(med_id) for med_id in cart.keys()]
            medicines = {
                medicine.id: medicine
                for medicine in Medicine.objects.select_for_update().filter(id__in=medicine_ids)
            }

            missing_or_invalid = [
                med_id for med_id in medicine_ids if med_id not in medicines
            ]
            if missing_or_invalid:
                messages.error(request, "Some cart items are no longer available.")
                return redirect('view_cart')

            for med_id_str, quantity in cart.items():
                medicine = medicines[int(med_id_str)]
                if quantity > medicine.available_quantity:
                    messages.error(
                        request,
                        f"Insufficient stock for {medicine.name}. Only {medicine.available_quantity} left.",
                    )
                    return redirect('view_cart')

            order = MedicineOrder.objects.create(
                full_name=full_name,
                address=address,
                phone=phone,
            )

            for med_id_str, quantity in cart.items():
                medicine = medicines[int(med_id_str)]
                MedicineOrderItem.objects.create(order=order, medicine=medicine, quantity=quantity)
                medicine.available_quantity -= quantity
                medicine.save(update_fields=['available_quantity'])

        if request.user.email:
            send_mail(
                subject='Medicine Order Confirmation',
                message=(
                    f"Dear {order.full_name},\n\n"
                    "Your medicine order has been received. "
                    "We are preparing your order for delivery.\n\n"
                    "Thank you for choosing our service!"
                ),
                from_email='noreply@healthcareplatform.com',
                recipient_list=[request.user.email],
                fail_silently=True,
            )

        request.session['cart'] = {}
        messages.success(request, "Order placed successfully!")
        return redirect('medicine_list')

    return render(request, 'place_order.html')
