from django.contrib import admin
from .models import Plan, Subscription, Payout, InvestmentAllocation

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'min_invest', 'max_invest', 'duration_days', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'amount', 'start_date', 'end_date', 'status', 'remaining_days')
    list_filter = ('status', 'start_date', 'plan')
    search_fields = ('user__username', 'user__email', 'plan__name')
    ordering = ('-start_date',)
    readonly_fields = ('id',)
    
    def remaining_days(self, obj):
        return obj.remaining_days()
    remaining_days.short_description = 'Remaining Days'

@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    list_display = ('subscription_user', 'subscription_plan', 'date', 'payout_percent', 'payout_amount', 'status')
    list_filter = ('status', 'date')
    search_fields = ('subscription__user__username', 'subscription__user__email')
    ordering = ('-date',)
    readonly_fields = ('id',)
    
    def subscription_user(self, obj):
        return obj.subscription.user.username
    subscription_user.short_description = 'User'
    
    def subscription_plan(self, obj):
        return obj.subscription.plan.name
    subscription_plan.short_description = 'Plan'

@admin.register(InvestmentAllocation)
class InvestmentAllocationAdmin(admin.ModelAdmin):
    list_display = ('subscription_user', 'market_type', 'percentage')
    list_filter = ('market_type',)
    search_fields = ('subscription__user__username', 'subscription__user__email')
    
    def subscription_user(self, obj):
        return obj.subscription.user.username
    subscription_user.short_description = 'User'
