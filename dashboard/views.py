from django.shortcuts import render, get_object_or_404
from django.db.models import Sum
from django.utils import timezone
from django.contrib.auth.decorators import login_required
import json
from decimal import Decimal

from .models import Subscription, InvestmentAllocation, Payout

# Market type display info mapping
MARKET_TYPE_INFO = {
    'crypto': {'name': 'Cryptocurrency', 'color': '#FF9F1C'},
    'forex': {'name': 'Foreign Exchange', 'color': '#2EC4B6'},
    'stocks': {'name': 'Stock Market', 'color': '#E71D36'},
    'real_estate': {'name': 'Real Estate', 'color': '#011627'},
    'commodities': {'name': 'Commodities', 'color': '#6A0572'},
    'bonds': {'name': 'Bonds', 'color': '#0B6E4F'},
    'vacant': {'name': 'Vacant (Unallocated)', 'color': '#CCCCCC'}
}

@login_required
def dashboard(request):
    # Get user's subscriptions with prefetched plan data
    subscriptions = Subscription.objects.filter(
        user=request.user
    ).select_related('plan')
    
    active_subscriptions = subscriptions.filter(status='active')
    pending_subscriptions = subscriptions.filter(status='pending')
    completed_subscriptions = subscriptions.filter(status='completed')
    
    # Get the count of active plans
    active_plans_count = active_subscriptions.count()
    
    # Initialize next payout date to None
    next_payout_date = None
    
    # Prepare subscription data for the template
    subscription_data = []
    
    # Process active subscriptions
    for subscription in active_subscriptions:
        subscription_data.append(prepare_subscription_data(subscription, 'Active'))
    
    # Process pending subscriptions
    for subscription in pending_subscriptions:
        subscription_data.append({
            'id': subscription.id,
            'plan_name': subscription.plan.name,
            'amount': subscription.amount,
            'start_date': subscription.created_at,
            'end_date': None,
            'status': 'Pending',
            'progress_percentage': 0,
            'remaining_days': 0,
            'subscription': subscription
        })
    
    # Process completed subscriptions
    for subscription in completed_subscriptions:
        subscription_data.append({
            'id': subscription.id,
            'plan_name': subscription.plan.name,
            'amount': subscription.amount,
            'start_date': subscription.start_date,
            'end_date': subscription.end_date,
            'status': 'Completed',
            'progress_percentage': 100,
            'remaining_days': 0,
            'subscription': subscription
        })
    
    # Calculate total earnings
    total_earnings = calculate_total_earnings(active_subscriptions)
    
    # Get selected subscription
    selected_subscription = get_selected_subscription(request, active_subscriptions)
    
    # Initialize allocation data
    allocation_data = []
    selected_subscription_allocations = []
    
    # Process allocations if a subscription is selected
    if selected_subscription:
        allocation_data = get_allocation_data(selected_subscription)
        selected_subscription_allocations = get_detailed_allocations(selected_subscription)
        
    # Prepare allocation data for the chart
    allocation_json = prepare_allocation_chart_data(allocation_data)
    
    # Sort subscription data by status and amount
    sorted_subscription_data = sort_subscriptions(subscription_data)
    
    # Get payouts for the selected subscription
    payout_data = []
    if selected_subscription:
        payout_data, next_payout_date = get_payout_data(selected_subscription)
    
    # Prepare context for the template
    context = {
        'plans': sorted_subscription_data,
        'total_earnings': round(total_earnings, 2),
        'active_plans_count': active_plans_count,
        'next_payout_date': next_payout_date,
        'has_subscriptions': bool(subscription_data),
        'allocation_data': allocation_data,
        'allocation_json': allocation_json,
        'has_allocations': bool(allocation_data),
        'selected_subscription': selected_subscription,
        'selected_subscription_allocations': selected_subscription_allocations
    }
    
    # Add payout data to context if available
    if payout_data:
        context['payout_data'] = payout_data
    
    if selected_subscription:
        print("Next Payout Date:", context['next_payout_date'])
        print("Subscription Status:", selected_subscription.status)
    
    return render(request, 'dashboard/dashboard.html', context)


def prepare_subscription_data(subscription, status):
    """Prepare data for a subscription to be displayed in the template."""
    now = timezone.now()
    total_duration = (subscription.end_date - subscription.start_date).days
    elapsed_duration = (now - subscription.start_date).days
    
    if total_duration > 0:
        progress_percentage = min(round((elapsed_duration / total_duration) * 100), 100)
    else:
        progress_percentage = 100
    
    return {
        'id': subscription.id,
        'plan_name': subscription.plan.name,
        'amount': subscription.amount,
        'start_date': subscription.start_date,
        'end_date': subscription.end_date,
        'status': status,
        'progress_percentage': progress_percentage,
        'remaining_days': subscription.remaining_days(),
        'subscription': subscription
    }


def calculate_total_earnings(active_subscriptions):
    """Calculate total earnings from active subscriptions."""
    total_earnings = 0
    for subscription in active_subscriptions:
        now = timezone.now()
        total_duration = (subscription.end_date - subscription.start_date).days
        elapsed_duration = (now - subscription.start_date).days
        
        if total_duration > 0:
            progress_ratio = min(elapsed_duration / total_duration, 1.0)
            # Assuming a simple 10% return over the full period
            estimated_roi = 0.10 * float(subscription.amount) * progress_ratio
            total_earnings += estimated_roi
    
    return total_earnings


def get_selected_subscription(request, active_subscriptions):
    """Get the selected subscription based on request parameters."""
    subscription_id = request.GET.get('subscription_id')
    
    if subscription_id:
        try:
            return Subscription.objects.get(id=subscription_id, user=request.user)
        except Subscription.DoesNotExist:
            pass
    
    # Default to first active subscription if available
    if active_subscriptions.exists():
        return active_subscriptions.first()
    
    return None


def get_allocation_data(subscription):
    """Get allocation data for a subscription."""
    allocation_data = []
    allocations = InvestmentAllocation.objects.filter(subscription=subscription)
    
    if allocations.exists():
        total_percentage = 0
        
        for allocation in allocations:
            percentage = float(allocation.percentage)
            amount = round(float(subscription.amount) * percentage / 100, 2)
            total_percentage += percentage
            
            allocation_data.append({
                'market_type': allocation.market_type,
                'name': MARKET_TYPE_INFO[allocation.market_type]['name'],
                'percentage': percentage,
                'color': MARKET_TYPE_INFO[allocation.market_type]['color'],
                'amount': amount,
                'created_at': allocation.created_at
            })
        
        # Add vacant allocation if total is less than 100%
        if total_percentage < 100:
            vacant_percentage = 100 - total_percentage
            vacant_amount = round(float(subscription.amount) * (vacant_percentage / 100), 2)
            
            allocation_data.append({
                'market_type': 'vacant',
                'name': 'Vacant (Unallocated)',
                'percentage': round(vacant_percentage, 1),
                'color': '#CCCCCC',
                'amount': vacant_amount,
                'created_at': timezone.now()
            })
    
    return allocation_data


def get_detailed_allocations(subscription):
    """Get detailed allocation data for display in a table."""
    detailed_allocations = []
    allocations = InvestmentAllocation.objects.filter(subscription=subscription)
    
    for allocation in allocations:
        market_type_display = dict(InvestmentAllocation.MARKET_TYPE_CHOICES).get(
            allocation.market_type, allocation.market_type
        )
        amount = round(Decimal(subscription.amount) * Decimal(allocation.percentage) / 100, 2)
        
        detailed_allocations.append({
            'market_type': allocation.market_type,
            'market_type_display': market_type_display,
            'percentage': allocation.percentage,
            'amount': amount,
            'created_at': allocation.created_at
        })
    
    return detailed_allocations


def prepare_allocation_chart_data(allocation_data):
    """Prepare allocation data for the chart."""
    if not allocation_data:
        return json.dumps({
            'labels': [],
            'data': [],
            'colors': []
        })
    
    return json.dumps({
        'labels': [item['name'] for item in allocation_data],
        'data': [item['percentage'] for item in allocation_data],
        'colors': [item['color'] for item in allocation_data]
    })


def sort_subscriptions(subscription_data):
    """Sort subscriptions by status and amount."""
    return sorted(
        subscription_data,
        key=lambda x: (
            0 if x['status'] == 'Active' else (1 if x['status'] == 'Pending' else 2),
            -float(x['amount'])
        )
    )


def get_payout_data(subscription):
    """Get payout data for a subscription and determine next payout date."""
    payouts = Payout.objects.filter(subscription=subscription).order_by('date')
    payout_data = []
    next_payout_date = None
    
    # Find the next pending payout directly from the database
    if subscription.status == 'active':
        next_payout = payouts.filter(status='pending').order_by('date').first()
        if next_payout:
            next_payout_date = next_payout.date
    
    for payout in payouts:
        payout_data.append({
            'id': payout.id,
            'amount': payout.amount,
            'date': payout.date,
            'status': payout.status,
            'created_at': payout.created_at
        })
    
    # Determine next payout date based on subscription status
    if subscription.status == 'active':
        # Find the next pending payout from the processed data
        next_pending_payout = None
        for payout in payout_data:
            if payout['status'] == 'pending':
                if next_pending_payout is None or payout['date'] < next_pending_payout['date']:
                    next_pending_payout = payout
        
        if next_pending_payout:
            next_payout_date = next_pending_payout['date']
        else:
            # If no pending payouts found, use default calculation
            next_payout_date = timezone.now() + timezone.timedelta(days=10)
    else:
        # For completed or pending subscriptions, don't show next payout date
        next_payout_date = None
    
    return payout_data, next_payout_date
