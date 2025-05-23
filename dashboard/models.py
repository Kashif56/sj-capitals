from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

class Plan(models.Model):
    """Investment plans available to users"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    min_invest = models.DecimalField(max_digits=12, decimal_places=2)
    max_invest = models.DecimalField(max_digits=12, decimal_places=2)
    duration_days = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class Subscription(models.Model):
    """User subscriptions to investment plans"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    screenshot = models.ImageField(upload_to='screenshot/', blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name='subscriptions')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Calculate end date based on plan duration if not set
        if not self.end_date and self.plan:
            self.end_date = self.start_date + timezone.timedelta(days=self.plan.duration_days)
        super().save(*args, **kwargs)
    
    def remaining_days(self):
        """Calculate remaining days in the subscription"""
        if self.status != 'active':
            return 0
        
        now = timezone.now()
        if now > self.end_date:
            return 0
        
        delta = self.end_date - now
        return delta.days
    
    def __str__(self):
        return f"{self.user.username} - {self.plan.name} (${self.amount})"


class Payout(models.Model):
    """Payouts for user subscriptions"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled')
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='payouts')
    date = models.DateTimeField()
    payout_percent = models.DecimalField(max_digits=5, decimal_places=2)  # 4.00 to 10.00
    payout_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Calculate payout amount if not set
        if self.payout_amount == 0 and self.subscription and self.payout_percent:
            self.payout_amount = (self.subscription.amount * self.payout_percent) / 100
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.subscription.user.username} - {self.date.strftime('%Y-%m-%d')} - ${self.payout_amount}"

class InvestmentAllocation(models.Model):
    """Allocation of user investments to different market types"""
    MARKET_TYPE_CHOICES = (
        ('crypto', 'Cryptocurrency'),
        ('forex', 'Foreign Exchange'),
        ('stocks', 'Stock Market'),
        ('real_estate', 'Real Estate'),
        ('other', 'Other Investments')
    )
    
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name='allocations')
    market_type = models.CharField(max_length=20, choices=MARKET_TYPE_CHOICES)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)  # 0.00 to 100.00
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('subscription', 'market_type')
    
    def __str__(self):
        return f"{self.subscription.user.username} - {self.market_type} ({self.percentage}%)"
