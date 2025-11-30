import pandas as pd
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse
from django.db.models import Count, Sum, Q, Avg
from django.utils import timezone
from datetime import timedelta
from books.models import Book
from loans.models import Loan, Reservation
from accounts.models import User


def is_management(user):
    return user.user_type in ['management', 'it_staff', 'librarian']


@login_required
@user_passes_test(is_management)
def reports_dashboard(request):
    # Basic statistics
    total_books = Book.objects.count()
    total_copies = Book.objects.aggregate(total=Sum('total_copies'))['total'] or 0
    available_copies = Book.objects.aggregate(available=Sum('available_copies'))['available'] or 0
    total_users = User.objects.count()
    active_loans = Loan.objects.filter(returned_date__isnull=True).count()
    overdue_loans = Loan.objects.filter(
        returned_date__isnull=True,
        due_date__lt=timezone.now()
    ).count()
    pending_reservations = Reservation.objects.filter(status='pending').count()

    # Recent activity (last 7 days)
    week_ago = timezone.now() - timedelta(days=7)
    recent_loans = Loan.objects.filter(borrowed_date__gte=week_ago).count()
    recent_returns = Loan.objects.filter(returned_date__gte=week_ago).count()

    context = {
        'total_books': total_books,
        'total_copies': total_copies,
        'available_copies': available_copies,
        'total_users': total_users,
        'active_loans': active_loans,
        'overdue_loans': overdue_loans,
        'pending_reservations': pending_reservations,
        'recent_loans_7d': recent_loans,
        'recent_returns_7d': recent_returns,
        'utilization_rate': round((1 - (available_copies / total_copies)) * 100, 2) if total_copies > 0 else 0
    }

    return render(request, 'reports/reports.html', context)


@login_required
@user_passes_test(is_management)
def popular_books_report(request):
    time_period = request.GET.get('period', 'all')
    now = timezone.now()

    if time_period == 'year':
        start_date = now - timedelta(days=365)
        popular_books = Book.objects.filter(
            loans__borrowed_date__gte=start_date
        ).annotate(
            loan_count=Count('loans')
        ).order_by('-loan_count')[:20]
    elif time_period == 'month':
        start_date = now - timedelta(days=30)
        popular_books = Book.objects.filter(
            loans__borrowed_date__gte=start_date
        ).annotate(
            loan_count=Count('loans')
        ).order_by('-loan_count')[:20]
    elif time_period == 'week':
        start_date = now - timedelta(days=7)
        popular_books = Book.objects.filter(
            loans__borrowed_date__gte=start_date
        ).annotate(
            loan_count=Count('loans')
        ).order_by('-loan_count')[:20]
    else:
        popular_books = Book.objects.annotate(
            loan_count=Count('loans')
        ).order_by('-loan_count')[:20]

    return render(request, 'reports/popular_books.html', {
        'popular_books': popular_books,
        'period': time_period
    })


@login_required
@user_passes_test(is_management)
def user_activity_report(request):
    time_period = request.GET.get('period', 'month')
    now = timezone.now()

    if time_period == 'year':
        start_date = now - timedelta(days=365)
    elif time_period == 'month':
        start_date = now - timedelta(days=30)
    elif time_period == 'week':
        start_date = now - timedelta(days=7)
    else:
        start_date = now - timedelta(days=30)

    active_users = User.objects.filter(
        loans__borrowed_date__gte=start_date
    ).annotate(
        loan_count=Count('loans'),
        active_loans=Count('loans', filter=Q(loans__returned_date__isnull=True)),
        overdue_loans=Count('loans', filter=Q(loans__returned_date__isnull=True, loans__due_date__lt=now))
    ).order_by('-loan_count')[:50]

    # Recent activity statistics
    recent_loans = Loan.objects.filter(borrowed_date__gte=start_date).count()
    recent_returns = Loan.objects.filter(returned_date__gte=start_date).count()

    return render(request, 'reports/user_activity.html', {
        'active_users': active_users,
        'recent_loans': recent_loans,
        'recent_returns': recent_returns,
        'period': time_period
    })


@login_required
@user_passes_test(is_management)
def loan_statistics_report(request):
    # Loan statistics for different periods
    now = timezone.now()

    periods = {
        'week': now - timedelta(days=7),
        'month': now - timedelta(days=30),
        'year': now - timedelta(days=365),
        'all': None
    }

    stats = {}
    for period_name, start_date in periods.items():
        loans_query = Loan.objects.all()
        if start_date:
            loans_query = loans_query.filter(borrowed_date__gte=start_date)

        stats[period_name] = {
            'total_loans': loans_query.count(),
            'active_loans': loans_query.filter(returned_date__isnull=True).count(),
            'overdue_loans': loans_query.filter(returned_date__isnull=True, due_date__lt=now).count(),
            'returned_loans': loans_query.filter(returned_date__isnull=False).count(),
        }

    return render(request, 'reports/loan_statistics.html', {
        'stats': stats,
        'periods': list(periods.keys())
    })


@login_required
@user_passes_test(is_management)
def export_books_excel(request):
    books = Book.objects.all().values(
        'title', 'author__first_name', 'author__last_name', 'isbn',
        'genre__name', 'publication_year', 'publisher',
        'total_copies', 'available_copies'
    )

    df = pd.DataFrame(books)
    df.rename(columns={
        'author__first_name': 'Author First Name',
        'author__last_name': 'Author Last Name',
        'genre__name': 'Genre',
        'publication_year': 'Publication Year',
        'total_copies': 'Total Copies',
        'available_copies': 'Available Copies'
    }, inplace=True)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="books_report.xlsx"'

    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Books', index=False)

    return response


@login_required
@user_passes_test(is_management)
def export_loans_excel(request):
    loans = Loan.objects.select_related('user', 'book').all()

    # Подготавливаем данные с преобразованием дат
    data = []
    for loan in loans:
        # Преобразуем даты в строки для избежания проблем с timezone
        borrowed_date = loan.borrowed_date.strftime('%Y-%m-%d %H:%M') if loan.borrowed_date else ''
        due_date = loan.due_date.strftime('%Y-%m-%d %H:%M') if loan.due_date else ''
        returned_date = loan.returned_date.strftime('%Y-%m-%d %H:%M') if loan.returned_date else ''

        data.append({
            'Username': loan.user.username,
            'User First Name': loan.user.first_name or '',
            'User Last Name': loan.user.last_name or '',
            'Book Title': loan.book.title,
            'ISBN': loan.book.isbn,
            'Borrowed Date': borrowed_date,
            'Due Date': due_date,
            'Returned Date': returned_date,
            'Status': loan.get_status_display(),
            'Renewals': loan.renewals,
            'Is Overdue': 'Yes' if loan.is_overdue() else 'No',
        })

    df = pd.DataFrame(data)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="loans_report.xlsx"'

    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Loans', index=False)

        # Авто-ширина колонок
        worksheet = writer.sheets['Loans']
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width

    return response


@login_required
@user_passes_test(is_management)
def export_users_excel(request):
    users = User.objects.all()

    # Подготавливаем данные с преобразованием дат
    data = []
    for user in users:
        date_joined = user.date_joined.strftime('%Y-%m-%d %H:%M') if user.date_joined else ''

        data.append({
            'Username': user.username,
            'First Name': user.first_name or '',
            'Last Name': user.last_name or '',
            'Email': user.email or '',
            'User Type': user.get_user_type_display(),
            'Membership ID': user.membership_id or '',
            'Is Active': 'Yes' if user.is_active else 'No',
            'Date Joined': date_joined,
        })

    df = pd.DataFrame(data)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="users_report.xlsx"'

    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Users', index=False)

        # Авто-ширина колонок
        worksheet = writer.sheets['Users']
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width

    return response


@login_required
@user_passes_test(is_management)
def export_reservations_excel(request):
    reservations = Reservation.objects.select_related('user', 'book').all()

    data = []
    for reservation in reservations:
        reserved_date = reservation.reserved_date.strftime('%Y-%m-%d %H:%M') if reservation.reserved_date else ''
        expiry_date = reservation.expiry_date.strftime('%Y-%m-%d %H:%M') if reservation.expiry_date else ''

        data.append({
            'Username': reservation.user.username,
            'Book Title': reservation.book.title,
            'ISBN': reservation.book.isbn,
            'Reserved Date': reserved_date,
            'Expiry Date': expiry_date,
            'Status': reservation.get_status_display(),
            'Priority': reservation.priority,
            'Notified': 'Yes' if reservation.notified else 'No',
        })

    df = pd.DataFrame(data)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="reservations_report.xlsx"'

    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Reservations', index=False)

        # Авто-ширина колонок
        worksheet = writer.sheets['Reservations']
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width

    return response


@login_required
@user_passes_test(is_management)
def export_data(request):
    return render(request, 'reports/export_data.html')