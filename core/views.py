from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import EmailMessage, send_mail
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
            'account_title': 'Jahanzeb Kayani',
            'account_number': '03462700408',
            'instructions': 'Open JazzCash app, select Send Money, enter our account number, and complete the payment.',
            'note': 'Please include your username in the reference.'
        },
        'easypaisa': {
            'name': 'EasyPaisa',
            'account_title': 'Jahanzeb Kayani',
            'account_number': '03462700408',
            'instructions': 'Open EasyPaisa app, select Send Money, enter our account number, and complete the payment.',
            'note': 'Please include your username in the reference.'
        },
        'bank': {
            'name': 'Habib Bank Limited (HBL)',
            'account_title': 'Jahanzeb Kayani',
            'account_number': 'PK23HABB0011787900643203',
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
                    'subscription': subscription,
                    'request': request
                }
                
                # Render the HTML template with context
                email_body = render_to_string('core/email/payment_notification.html', email_context)
                
                # Create email message with HTML content type
                email = EmailMessage(
                    subject,
                    email_body,
                    settings.DEFAULT_FROM_EMAIL,
                    [admin_email],
                )
                
                # Set the content type to HTML
                email.content_subtype = 'html'
                
                # Attach the screenshot properly
                if screenshot:
                    # Reset the file pointer to the beginning
                    screenshot.seek(0)
                    # Read the content once
                    content = screenshot.read()
                    # Attach with proper name and content type
                    email.attach(screenshot.name, content, screenshot.content_type)
                
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



def contact_us(request):
    if request.method == 'POST':
        name = request.POST.get('full_name')
        email = request.POST.get('email')
        reason = request.POST.get('reason')
        message = request.POST.get('message')
        
        subject = f"Message from {name}: {message[:20]}"
        
        admin_email = settings.ADMIN_EMAIL
        
        message_to_send = f"""
        Name = {name}
        Email = {email}
        Reason = {reason}
        Message: 
        {message}
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=email,
            recipient_list=[admin_email,],
            fail_silently=True
        )
        
        return redirect('landing')