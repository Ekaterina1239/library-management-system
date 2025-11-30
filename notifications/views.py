from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Notification, NotificationPreference


@login_required
def notification_list(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    unread_count = notifications.filter(is_read=False).count()

    return render(request, 'notifications/notification_list.html', {
        'notifications': notifications,
        'unread_count': unread_count
    })


@login_required
def mark_notification_read(request, notification_id):
    notification = Notification.objects.get(id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True})

    messages.success(request, 'Notification marked as read.')
    return redirect('notification_list')


@login_required
def mark_all_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True})

    messages.success(request, 'All notifications marked as read.')
    return redirect('notification_list')


@login_required
def notification_preferences(request):
    preference, created = NotificationPreference.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        preference.email_due_reminders = 'email_due_reminders' in request.POST
        preference.email_overdue_alerts = 'email_overdue_alerts' in request.POST
        preference.email_reservation_available = 'email_reservation_available' in request.POST
        preference.email_general = 'email_general' in request.POST
        preference.save()
        messages.success(request, 'Notification preferences updated successfully!')
        return redirect('notification_preferences')

    return render(request, 'notifications/preferences.html', {'preference': preference})


@login_required
def get_unread_count(request):
    if request.user.is_authenticated:
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return JsonResponse({'unread_count': count})
    return JsonResponse({'unread_count': 0})

@login_required
def notification_list(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    unread_count = notifications.filter(is_read=False).count()

    # Support for partial rendering in dropdown
    if request.GET.get('partial'):
        return render(request, 'notifications/notification_dropdown.html', {
            'notifications': notifications[:5]  # Only show 5 in dropdown
        })

    return render(request, 'notifications/notification_list.html', {
        'notifications': notifications,
        'unread_count': unread_count
    })
@login_required
def mark_notification_read(request, notification_id):
    notification = Notification.objects.get(id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True})

    messages.success(request, 'Notification marked as read.')
    return redirect('notification_list')


@login_required
def mark_all_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True})

    messages.success(request, 'All notifications marked as read.')
    return redirect('notification_list')


@login_required
def notification_preferences(request):
    preference, created = NotificationPreference.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        preference.email_due_reminders = 'email_due_reminders' in request.POST
        preference.email_overdue_alerts = 'email_overdue_alerts' in request.POST
        preference.email_reservation_available = 'email_reservation_available' in request.POST
        preference.email_general = 'email_general' in request.POST
        preference.save()
        messages.success(request, 'Notification preferences updated successfully!')
        return redirect('notification_preferences')

    return render(request, 'notifications/preferences.html', {'preference': preference})


@login_required
def get_unread_count(request):
    if request.user.is_authenticated:
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return JsonResponse({'unread_count': count})
    return JsonResponse({'unread_count': 0})


