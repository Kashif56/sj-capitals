import uuid
import secrets
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.template.loader import render_to_string
from .models import Profile


def login_view(request):
    """Handle user login with email or username"""
    # Redirect to dashboard if already logged in
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me') == 'on'
        
        # Try to get the user by email
        try:
            username = User.objects.get(email=email).username
        except User.DoesNotExist:
            username = email  # If email doesn't exist, try using it as username directly
            
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if not user.profile.is_email_verified and settings.REQUIRE_EMAIL_VERIFICATION:
                messages.warning(request, 'Please verify your email address before logging in.')
                return render(request, 'accounts/login.html')
                
            login(request, user)
            
            if not remember_me:
                request.session.set_expiry(0)
                
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            return redirect('landing')
        else:
            messages.error(request, 'Invalid email or password. Please try again.')
            
    return render(request, 'accounts/login.html')


def register_view(request):
    """Handle user registration with profile creation"""
    # Redirect to dashboard if already logged in
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        # Get form data
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        name = request.POST.get('name', '')
        address = request.POST.get('address', '')
        phone = request.POST.get('phone', '')
        
        # Basic validation
        if password != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'accounts/register.html')
            
        # Check if username or email already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'accounts/register.html')
            
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return render(request, 'accounts/register.html')
        
        try:
            with transaction.atomic():
                # Create user with properly hashed password
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password
                )
                
                # Set name if provided
                if name:
                    first_name, *last_name_parts = name.split(' ', 1)
                    user.first_name = first_name
                    if last_name_parts:
                        user.last_name = last_name_parts[0]
                    user.save()
                
                # Update profile with additional fields
                profile = user.profile
                profile.address = address
                profile.phone = phone
                
                # Generate verification token if email verification is required
                if settings.REQUIRE_EMAIL_VERIFICATION:
                    profile.verification_token = secrets.token_urlsafe(32)
                    profile.save()
                    
                    # Send verification email
                    send_verification_email(request, user, profile.verification_token)
                    
                    messages.success(request, f'Account created successfully! Please check your email to verify your account.')
                    return redirect('login')
                else:
                    # If email verification is not required, mark as verified
                    profile.is_email_verified = True
                    profile.save()
                
                # Log the user in if email verification is not required
                login(request, user)
                messages.success(request, f'Welcome to SJ Capitals, {user.first_name or user.username}!')
                return redirect('dashboard')
            
        except IntegrityError:
            messages.error(request, 'An error occurred during registration. Please try again.')
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            
    return render(request, 'accounts/register.html')


@login_required
def logout_view(request):
    """Handle user logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


def forgot_password_view(request):
    """Handle password reset request"""
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        email = request.POST.get('email')
        
        # Check if email exists
        try:
            user = User.objects.get(email=email)
            
            # Generate password reset token
            token = secrets.token_urlsafe(32)
            
            # Save token to profile
            profile = user.profile
            profile.verification_token = token
            profile.save()
            
            # Send password reset email
            send_password_reset_email(request, user, token)
            
            messages.success(request, 'Password reset instructions have been sent to your email.')
            return redirect('login')
            
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email address.')
            
    return render(request, 'accounts/forgot_password.html')


def verify_email_view(request, token):
    """Handle email verification"""
    # Find user by verification token
    profile = get_object_or_404(Profile, verification_token=token)
    
    # Mark email as verified
    profile.is_email_verified = True
    profile.verification_token = None  # Clear the token for security
    profile.save()
    
    messages.success(request, 'Your email has been verified successfully! You can now log in.')
    return redirect('login')


def reset_password_view(request, token):
    """Handle password reset"""
    # Validate token
    profile = get_object_or_404(Profile, verification_token=token)
    user = profile.user
    
    if request.method == 'POST':
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        
        if password != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'accounts/reset_password.html', {'token': token})
            
        # Update password
        user.set_password(password)
        user.save()
        
        # Clear verification token
        profile.verification_token = None
        profile.save()
        
        messages.success(request, 'Your password has been reset successfully! You can now log in with your new password.')
        return redirect('login')
        
    return render(request, 'accounts/reset_password.html', {'token': token})


# Helper functions
def send_verification_email(request, user, token):
    """Send email verification link"""
    subject = 'Verify your SJ Capitals account'
    verification_url = f"{request.scheme}://{request.get_host()}/accounts/verify-email/{token}/"
    
    message = render_to_string('accounts/email/verify_email.html', {
        'user': user,
        'verification_url': verification_url,
    })
    
    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [user.email],
        fail_silently=False,
        html_message=message
    )


def send_password_reset_email(request, user, token):
    """Send password reset link"""
    subject = 'Reset your SJ Capitals password'
    reset_url = f"{request.scheme}://{request.get_host()}/accounts/reset-password/{token}/"
    
    message = render_to_string('accounts/email/reset_password.html', {
        'user': user,
        'reset_url': reset_url,
    })
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
        html_message=message
    )