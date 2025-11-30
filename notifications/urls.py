from django.urls import path
from . import views

urlpatterns = [
    path('', views.notification_list, name='notification_list'),
    path('preferences/', views.notification_preferences, name='notification_preferences'),
    path('<int:notification_id>/mark-read/', views.mark_notification_read, name='mark_notification_read'),
    path('mark-all-read/', views.mark_all_read, name='mark_all_read'),
    path('api/unread-count/', views.get_unread_count, name='get_unread_count'),
]