from django.shortcuts import render
from django.db.models import Sum, F, ExpressionWrapper, DecimalField, Case, When, Value
from django.utils import timezone
from django.contrib.auth.decorators import login_required
import json

from .models import Subscription, Plan, InvestmentAllocation, Payout

@login_required
def dashboard(request):
    # Get user's subscriptions
    active_subscriptions = Subscription.objects.filter(
        user=request.user,
        status='active'
    ).select_related('plan')
    
    pending_subscriptions = Subscription.objects.filter(
        user=request.user,
        status='pending'
    ).select_related('plan')
    
    completed_subscriptions = Subscription.objects.filter(
        user=request.user,
        status='completed'
    ).select_related('plan')
    
    # Calculate total invested amount
    total_invested = active_subscriptions.aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    # Prepare subscription data for the template
    subscription_data = []
    
    for subscription in active_subscriptions:
        # Calculate progress percentage
        now = timezone.now()
        total_duration = (subscription.end_date - subscription.start_date).days
        elapsed_duration = (now - subscription.start_date).days
        
        if total_duration > 0:
            progress_percentage = min(round((elapsed_duration / total_duration) * 100), 100)
        else:
            progress_percentage = 100
        
        # Calculate remaining days
        remaining_days = subscription.remaining_days()
        
        subscription_data.append({
            'id': subscription.id,
            'plan_name': subscription.plan.name,
            'amount': subscription.amount,
            'start_date': subscription.start_date,
            'end_date': subscription.end_date,
            'status': 'Active',
            'progress_percentage': progress_percentage,
            'remaining_days': remaining_days,
            'subscription': subscription
        })
    
    # Add pending subscriptions
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
        
    # Add completed subscriptions
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
    
    # Calculate total earnings (simplified example - in a real app this would be more complex)
    # This is just a placeholder calculation
    total_earnings = 0
    for subscription in active_subscriptions:
        # Simple ROI calculation based on elapsed time
        now = timezone.now()
        total_duration = (subscription.end_date - subscription.start_date).days
        elapsed_duration = (now - subscription.start_date).days
        
        if total_duration > 0:
            progress_ratio = min(elapsed_duration / total_duration, 1.0)
            # Assuming a simple 10% return over the full period
            estimated_roi = 0.10 * float(subscription.amount) * progress_ratio
            total_earnings += estimated_roi
    
    # Get the count of active plans
    active_plans_count = active_subscriptions.count()
    
    # Calculate the next payout date (previous payout date + 10 days)
    next_payout_date = None
    
    # Get the most recent payout date (could be from a payout model in a real app)
    # For now, we'll use a simple approach: check if there's a last_payout_date in the session
    # If not, we'll set it to 10 days from now for the first time
    last_payout_date = request.session.get('last_payout_date')
    
    if last_payout_date:
        # Convert string date back to datetime
        try:
            last_payout_date = timezone.datetime.strptime(last_payout_date, '%Y-%m-%d').date()
            next_payout_date = timezone.datetime.combine(
                last_payout_date + timezone.timedelta(days=10),
                timezone.datetime.min.time()
            )
        except (ValueError, TypeError):
            # If there's an error parsing the date, set a default
            next_payout_date = timezone.now() + timezone.timedelta(days=10)
    else:
        # For demonstration, if no previous payout, set next payout to 10 days from now
        next_payout_date = timezone.now() + timezone.timedelta(days=10)
        # Store this as the 'last payout date' for future reference
        request.session['last_payout_date'] = next_payout_date.date().strftime('%Y-%m-%d')
    
    # Get investment allocations for active subscriptions
    allocation_data = []
    
    # Market type display info mapping
    market_type_info = {
        'crypto': {'name': 'Cryptocurrency', 'color': '#FF9F1C'},
        'forex': {'name': 'Foreign Exchange', 'color': '#2EC4B6'},
        'stocks': {'name': 'Stock Market', 'color': '#E71D36'},
        'real_estate': {'name': 'Real Estate', 'color': '#011627'},
        'other': {'name': 'Other Investments', 'color': '#6A0572'}
    }
    
    # Create actual allocation data for each subscription
    for subscription in active_subscriptions:
        # Get allocations for this subscription
        subscription_allocations = InvestmentAllocation.objects.filter(subscription=subscription)
        
    
    # Now get all allocations after ensuring they exist
    if active_subscriptions.exists():
        # Get all allocations for active subscriptions with weighted percentages based on subscription amount
        all_allocations = []
        total_investment = sum(subscription.amount for subscription in active_subscriptions)
        
        for market_type in ['crypto', 'forex', 'stocks', 'real_estate', 'other']:
            market_total = 0
            
            for subscription in active_subscriptions:
                # Get allocations for this subscription and market type
                allocation = InvestmentAllocation.objects.filter(
                    subscription=subscription,
                    market_type=market_type
                ).first()
                
                if allocation:
                    # Weight the percentage by the subscription amount relative to total investment
                    weight = float(subscription.amount) / float(total_investment)
                    # Convert Decimal to float before multiplication
                    market_total += float(allocation.percentage) * weight
            
            # Add to allocation data if there's any allocation for this market type
            if market_total > 0:
                # Calculate dollar amount based on percentage of total investment
                dollar_amount = round(float(total_investment) * (market_total / 100), 2)
                
                # Get the most recent allocation for this market type to get the created date
                recent_allocation = InvestmentAllocation.objects.filter(
                    subscription__in=active_subscriptions,
                    market_type=market_type
                ).order_by('-created_at').first()
                
                created_date = recent_allocation.created_at if recent_allocation else None
                
                allocation_data.append({
                    'market_type': market_type,
                    'name': market_type_info[market_type]['name'],
                    'percentage': round(market_total, 1),
                    'color': market_type_info[market_type]['color'],
                    'amount': dollar_amount,
                    'created_at': created_date
                })
        
        # Calculate total allocated percentage
        total_percentage = sum(item['percentage'] for item in allocation_data)
        
        # If total is less than 100%, add a 'Vacant' category for unallocated funds
        if total_percentage < 100:
            # Calculate the remaining amount for vacant allocation
            vacant_percentage = 100 - total_percentage
            vacant_amount = round(float(total_investment) * (vacant_percentage / 100), 2)
            
            allocation_data.append({
                'market_type': 'vacant',
                'name': 'Vacant (Unallocated)',
                'percentage': round(vacant_percentage, 1),
                'color': '#CCCCCC',  # Light gray color for vacant
                'amount': vacant_amount,
                'created_at': timezone.now()  # Current time for vacant allocation
            })
        # If total is not exactly 100%, normalize to ensure they sum to 100%
        elif total_percentage != 100:
            for item in allocation_data:
                item['percentage'] = round((item['percentage'] / total_percentage) * 100, 1)
    
    # Create a copy of allocation data for JSON serialization without datetime objects
    chart_allocation_data = []
    for item in allocation_data:
        chart_item = {
            'market_type': item['market_type'],
            'name': item['name'],
            'percentage': item['percentage'],
            'color': item['color']
        }
        chart_allocation_data.append(chart_item)
    
    # Convert allocation data to JSON for the chart (without datetime objects)
    allocation_json = json.dumps(chart_allocation_data)
    
    # Sort subscription data in the order: Active, Pending, Completed
    def sort_key(plan):
        status_order = {'Active': 0, 'Pending': 1, 'Completed': 2}
        return status_order.get(plan['status'], 3)
    
    sorted_subscription_data = sorted(subscription_data, key=sort_key)
    
    # Handle subscription_id query parameter for viewing specific subscription details
    selected_subscription = None
    selected_subscription_id = request.GET.get('subscription_id')
    
    if selected_subscription_id:
        # Try to find the subscription with the given ID
        try:
            selected_subscription = Subscription.objects.get(
                id=selected_subscription_id,
                user=request.user
            )
        except Subscription.DoesNotExist:
            selected_subscription = None
    else:
        # If no subscription_id provided, default to the first active subscription
        active_subs = active_subscriptions.order_by('-created_at')
        if active_subs.exists():
            selected_subscription = active_subs.first()
            
    # If we have a selected subscription, adjust the dashboard data to focus on this subscription
    if selected_subscription:
        # Calculate total invested amount based on the selected subscription
        total_invested = selected_subscription.amount
        
        # Calculate earnings for the selected subscription
        total_earnings = 0
        
        # Simple ROI calculation based on elapsed time for the selected subscription
        if selected_subscription.status == 'active' or selected_subscription.status == 'completed':
            now = timezone.now()
            total_duration = (selected_subscription.end_date - selected_subscription.start_date).days
            elapsed_duration = (now - selected_subscription.start_date).days
            
            if total_duration > 0:
                progress_ratio = min(elapsed_duration / total_duration, 1.0)
                # Assuming a simple 10% return over the full period
                total_earnings = 0.10 * float(selected_subscription.amount) * progress_ratio
        
        # Get allocation data specific to the selected subscription
        allocation_data = []
        market_type_info = {
            'crypto': {'name': 'Cryptocurrency', 'color': '#FF9F1C'},
            'forex': {'name': 'Foreign Exchange', 'color': '#2EC4B6'},
            'stocks': {'name': 'Stock Market', 'color': '#E71D36'},
            'real_estate': {'name': 'Real Estate', 'color': '#011627'},
            'other': {'name': 'Other Investments', 'color': '#6A0572'}
        }
        
        # Get allocations for the selected subscription
        allocations = InvestmentAllocation.objects.filter(subscription=selected_subscription)
        
        # If allocations exist, use them
        if allocations.exists():
            total_percentage = 0
            
            for allocation in allocations:
                percentage = float(allocation.percentage)
                amount = round(float(selected_subscription.amount) * percentage / 100, 2)
                total_percentage += percentage
                
                allocation_data.append({
                    'market_type': allocation.market_type,
                    'name': market_type_info[allocation.market_type]['name'],
                    'percentage': percentage,
                    'color': market_type_info[allocation.market_type]['color'],
                    'amount': amount,
                    'created_at': allocation.created_at
                })
            
            # If total is less than 100%, add a 'Vacant' category for unallocated funds
            if total_percentage < 100:
                # Calculate the remaining amount for vacant allocation
                vacant_percentage = 100 - total_percentage
                vacant_amount = round(float(selected_subscription.amount) * (vacant_percentage / 100), 2)
                
                allocation_data.append({
                    'market_type': 'vacant',
                    'name': 'Vacant (Unallocated)',
                    'percentage': round(vacant_percentage, 1),
                    'color': '#CCCCCC',  # Light gray color for vacant
                    'amount': vacant_amount,
                    'created_at': timezone.now()  # Current time for vacant allocation
                })
    
    # Get allocation data for the selected subscription if it exists
    selected_subscription_allocations = []
    if selected_subscription:
        allocations = InvestmentAllocation.objects.filter(subscription=selected_subscription)
        for allocation in allocations:
            market_type_display = dict(InvestmentAllocation.MARKET_TYPE_CHOICES).get(allocation.market_type, allocation.market_type)
            selected_subscription_allocations.append({
                'market_type': allocation.market_type,
                'name': market_type_display,
                'percentage': allocation.percentage,
                'amount': round(float(selected_subscription.amount) * float(allocation.percentage) / 100, 2),
                'created_at': allocation.created_at
            })
            
        # Get payouts for the selected subscription (only those added by admin)
        payouts = Payout.objects.filter(subscription=selected_subscription).order_by('date')
        payout_data = []
        
        # Find the next pending payout directly from the database
        if selected_subscription and selected_subscription.status == 'active':
            next_payout = payouts.filter(status='pending').order_by('date').first()
            if next_payout:
                # Update the global next_payout_date variable
                next_payout_date = next_payout.date
        
        for payout in payouts:
            payout_data.append({
                'amount': payout.amount,
                'date': payout.date,
                'status': payout.status,
                'created_at': payout.created_at
            })
    
    # Prepare context for the template
    context = {
        'plans': sorted_subscription_data,
        'total_invested': total_invested,
        'total_earnings': round(total_earnings, 2),
        'active_plans_count': active_plans_count,
        'next_payout_date': next_payout_date,
        'has_subscriptions': len(subscription_data) > 0,
        'allocation_data': allocation_data,
        'allocation_json': allocation_json,
        'has_allocations': len(allocation_data) > 0,
        'selected_subscription': selected_subscription,
        'selected_subscription_allocations': selected_subscription_allocations
    }
    
    # If we have payout data for the selected subscription, add it to the context
    if selected_subscription and 'payout_data' in locals():
        context['payout_data'] = payout_data
        
        # Only show next payout date if the subscription is active (not completed or pending)
        if selected_subscription.status == 'active':
            # Find the next pending payout
            next_pending_payout = None
            for payout in payout_data:
                if payout['status'] == 'pending':
                    if next_pending_payout is None or payout['date'] < next_pending_payout['date']:
                        next_pending_payout = payout
            
            if next_pending_payout:
                context['next_payout_date'] = next_pending_payout['date']
            else:
                # If no pending payouts found in the database, use the default calculation for active subscriptions
                # Calculate next payout date as 10 days from now
                context['next_payout_date'] = timezone.now() + timezone.timedelta(days=10)
        else:
            # For completed or pending subscriptions, don't show next payout date
            context['next_payout_date'] = None
    
    print("Next Payout Date:", context['next_payout_date'])
    print("Subscription Status:", selected_subscription.status)
    
    return render(request, 'dashboard/dashboard.html', context)
