from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string

from dashboard.models import Plan, Subscription


# Create your views here.


def landing(request):
    plans = Plan.objects.all()

    context = {
        'plans': plans,
    }
    return render(request, 'core/landing.html', context)


@login_required
def payment(request, plan_id):
    # Get the selected plan
    plan = get_object_or_404(Plan, id=plan_id, is_active=True)
    
    # Check if user already has an active subscription for this plan
    active_subscription = Subscription.objects.filter(
        user=request.user,
        plan=plan,
        status='active'
    ).first()
    
    # If there's an active subscription, redirect to dashboard
    if active_subscription:
        messages.info(request, f'You already have an active subscription for {plan.name}.')
        return redirect('dashboard')
    
    # Check if user already has a pending subscription for this plan
    pending_subscription = Subscription.objects.filter(
        user=request.user,
        plan=plan,
        status='pending'
    ).first()
    
    # Define payment methods
    payment_methods = {
        'jazzcash': {
            'name': 'JazzCash',
            'account_title': 'SJ Capitals',
            'account_number': '03001234567',
            'instructions': 'Open JazzCash app, select Send Money, enter our account number, and complete the payment.',
            'note': 'Please include your username in the reference.'
        },
        'easypaisa': {
            'name': 'EasyPaisa',
            'account_title': 'SJ Capitals',
            'account_number': '03009876543',
            'instructions': 'Open EasyPaisa app, select Send Money, enter our account number, and complete the payment.',
            'note': 'Please include your username in the reference.'
        },
        'bank': {
            'name': 'Bank Transfer',
            'account_title': 'SJ Capitals Ltd.',
            'account_number': 'PK36ABCD1234567890123456',
            'instructions': 'Transfer the amount to our bank account through your banking app or visit your nearest branch.',
            'note': 'Please include your username in the transfer reference.'
        }
    }
    
    if request.method == 'POST':
        # Handle the form submission
        amount = request.POST.get('amount')
        comment = request.POST.get('comment', '')
        screenshot = request.FILES.get('screenshot')
        
        if not screenshot:
            messages.error(request, 'Please upload a payment screenshot')
            return redirect('payment', plan_id=plan.id)
        
        # Create a new subscription
        subscription = Subscription.objects.create(
            user=request.user,
            plan=plan,
            amount=amount,
            screenshot=screenshot,
            status='pending'
        )
        
        # Send email to admin
        try:
            admin_email = settings.ADMIN_EMAIL
            if admin_email:
                subject = f"New Payment Submitted by {request.user.username}"
                
                email_context = {
                    'user': request.user,
                    'plan': plan,
                    'amount': amount,
                    'comment': comment,
                    'subscription': subscription
                }
                
                email_body = render_to_string('core/email/payment_notification.html', email_context)
                
                email = EmailMessage(
                    subject,
                    email_body,
                    settings.DEFAULT_FROM_EMAIL,
                    [admin_email],
                )
                
                # Attach the screenshot
                if screenshot:
                    email.attach(screenshot.name, screenshot.read(), screenshot.content_type)
                
                email.send()
        except Exception as e:
            # Log the error but don't stop the process
            print(f"Error sending email: {e}")
        
        # Show success message
        messages.success(request, ' Payment submitted. Awaiting admin confirmation.')
        return redirect('payment', plan_id=plan.id)
    
    context = {
        'plan': plan,
        'payment_methods': payment_methods,
        'pending_subscription': pending_subscription,
    }
    
    return render(request, 'core/payment.html', context)
