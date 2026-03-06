from django.contrib import admin
from .models import Badge, EmployeeBadge, PointsTransaction, EmployeePoints


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ['name', 'badge_type', 'rarity', 'points_awarded', 'is_active', 'is_hidden', 'company']
    list_filter = ['rarity', 'is_active', 'is_hidden', 'company']
    search_fields = ['name', 'name_ar', 'description']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        (None, {
            'fields': ('name', 'name_ar', 'badge_type', 'description', 'description_ar')
        }),
        ('Visual', {
            'fields': ('icon', 'color', 'rarity')
        }),
        ('Settings', {
            'fields': ('points_awarded', 'criteria', 'is_active', 'is_hidden', 'company')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(EmployeeBadge)
class EmployeeBadgeAdmin(admin.ModelAdmin):
    list_display = ['employee', 'badge', 'company', 'awarded_at', 'points_awarded', 'is_notified']
    list_filter = ['badge', 'company', 'is_notified', 'awarded_at']
    search_fields = ['employee__email', 'employee__first_name', 'badge__name']
    readonly_fields = ['awarded_at']
    raw_id_fields = ['employee', 'badge']
    date_hierarchy = 'awarded_at'


@admin.register(PointsTransaction)
class PointsTransactionAdmin(admin.ModelAdmin):
    list_display = ['employee', 'transaction_type', 'points', 'balance_after', 'created_at']
    list_filter = ['transaction_type', 'company', 'created_at']
    search_fields = ['employee__email', 'description']
    readonly_fields = ['created_at', 'balance_after']
    raw_id_fields = ['employee']
    date_hierarchy = 'created_at'


@admin.register(EmployeePoints)
class EmployeePointsAdmin(admin.ModelAdmin):
    list_display = ['employee', 'company', 'total_points', 'weekly_points', 'monthly_points', 'badge_count']
    list_filter = ['company']
    search_fields = ['employee__email', 'employee__first_name']
    readonly_fields = ['created_at', 'updated_at']
    raw_id_fields = ['employee']
    fieldsets = (
        (None, {
            'fields': ('employee', 'company')
        }),
        ('Points', {
            'fields': ('total_points', 'weekly_points', 'monthly_points', 'badge_count')
        }),
        ('Period Tracking', {
            'fields': ('week_start', 'month_start')
        }),
        ('Streak', {
            'fields': ('current_streak_days', 'longest_streak_days', 'last_activity_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
