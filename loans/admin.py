from django.contrib import admin
from .models import Loan, Reservation


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('book', 'user', 'borrowed_date', 'due_date', 'returned_date', 'status', 'is_overdue')
    list_filter = ('status', 'borrowed_date', 'due_date', 'returned_date')
    search_fields = ('book__title', 'user__username', 'user__first_name', 'user__last_name')
    readonly_fields = ('borrowed_date',)
    date_hierarchy = 'borrowed_date'

    fieldsets = (
        ('Loan Information', {
            'fields': ('book', 'user', 'borrowed_date', 'due_date', 'returned_date')
        }),
        ('Loan Management', {
            'fields': ('status', 'renewals', 'max_renewals')
        }),
    )

    def is_overdue(self, obj):
        return obj.is_overdue()

    is_overdue.boolean = True
    is_overdue.short_description = 'Overdue'


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('book', 'user', 'reserved_date', 'expiry_date', 'status', 'is_expired')
    list_filter = ('status', 'reserved_date', 'expiry_date')
    search_fields = ('book__title', 'user__username')
    readonly_fields = ('reserved_date',)
    date_hierarchy = 'reserved_date'

    def is_expired(self, obj):
        return obj.is_expired()

    is_expired.boolean = True
    is_expired.short_description = 'Expired'