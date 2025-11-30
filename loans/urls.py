from django.urls import path
from . import views

urlpatterns = [
    path('my-loans/', views.my_loans, name='my_loans'),
    path('my-reservations/', views.my_reservations, name='my_reservations'),
    path('loan-history/', views.loan_history, name='loan_history'),
    path('all-loans/', views.all_loans, name='all_loans'),
    path('all-reservations/', views.all_reservations, name='all_reservations'),
    path('borrow/<int:book_id>/', views.borrow_book, name='borrow_book'),
    path('return/<int:loan_id>/', views.return_book, name='return_book'),
    path('renew/<int:loan_id>/', views.renew_loan, name='renew_loan'),
    path('reserve/<int:book_id>/', views.reserve_book, name='reserve_book'),
    path('cancel-reservation/<int:reservation_id>/', views.cancel_reservation, name='cancel_reservation'),
    path('manage-reservation/<int:reservation_id>/<str:action>/', views.manage_reservation, name='manage_reservation'),
]