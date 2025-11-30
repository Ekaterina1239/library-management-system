from django.urls import path
from . import views

urlpatterns = [
    path('', views.reports_dashboard, name='reports_dashboard'),
    path('popular-books/', views.popular_books_report, name='popular_books'),
    path('user-activity/', views.user_activity_report, name='user_activity'),
    path('loan-statistics/', views.loan_statistics_report, name='loan_statistics'),
    path('export/books/', views.export_books_excel, name='export_books_excel'),
    path('export/loans/', views.export_loans_excel, name='export_loans_excel'),
    path('export/users/', views.export_users_excel, name='export_users_excel'),
    path('export/', views.export_data, name='export_data'),
]