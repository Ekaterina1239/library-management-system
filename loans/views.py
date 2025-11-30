from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Loan, Reservation
from books.models import Book


def is_librarian(user):
    return user.user_type in ['librarian', 'it_staff', 'management']


@login_required
def borrow_book(request, book_id):
    book = get_object_or_404(Book, pk=book_id)

    # Проверяем доступность книги
    if book.available_copies > 0:
        # Проверяем, нет ли у пользователя уже этой книги
        existing_loan = Loan.objects.filter(
            user=request.user,
            book=book,
            returned_date__isnull=True
        ).exists()

        if not existing_loan:
            # Проверяем лимит займов (максимум 5)
            active_loans_count = Loan.objects.filter(
                user=request.user,
                returned_date__isnull=True
            ).count()

            if active_loans_count >= 5:
                messages.error(request, 'You have reached the maximum number of active loans (5).')
                return redirect('book_detail', pk=book_id)

            # Создаем займ
            Loan.objects.create(user=request.user, book=book)
            messages.success(request, f'You have successfully borrowed "{book.title}"')
        else:
            messages.error(request, 'You already have this book on loan.')
    else:
        messages.error(request, 'This book is not available for borrowing.')

    return redirect('book_detail', pk=book_id)


@login_required
def return_book(request, loan_id):
    loan = get_object_or_404(Loan, pk=loan_id)

    # Проверяем права: пользователь может возвращать только свои книги, библиотекарь - любые
    if loan.user != request.user and not is_librarian(request.user):
        messages.error(request, 'You do not have permission to return this book.')
        return redirect('my_loans')

    if not loan.returned_date:
        loan.returned_date = timezone.now()
        loan.save()

        # Обновляем доступные копии книги
        book = loan.book
        if book.available_copies < book.total_copies:
            book.available_copies += 1
            book.save()

        messages.success(request, f'Book "{loan.book.title}" has been returned.')

    if is_librarian(request.user):
        return redirect('all_loans')
    else:
        return redirect('my_loans')


@login_required
def renew_loan(request, loan_id):
    loan = get_object_or_404(Loan, pk=loan_id, user=request.user)

    if loan.can_renew():
        loan.renewals += 1
        loan.due_date = timezone.now() + timedelta(days=14)
        loan.save()
        messages.success(request,
                         f'Loan for "{loan.book.title}" renewed successfully! New due date: {loan.due_date.strftime("%B %d, %Y")}')
    else:
        messages.error(request,
                       'This loan cannot be renewed. You may have reached the maximum renewal limit or the book is overdue.')

    return redirect('my_loans')


@login_required
def reserve_book(request, book_id):
    book = get_object_or_404(Book, pk=book_id)

    existing_reservation = Reservation.objects.filter(
        user=request.user,
        book=book,
        status__in=['pending', 'available']
    ).exists()

    existing_loan = Loan.objects.filter(
        user=request.user,
        book=book,
        returned_date__isnull=True
    ).exists()

    if not existing_reservation and not existing_loan:
        Reservation.objects.create(user=request.user, book=book)
        messages.success(request, f'You have reserved "{book.title}". You will be notified when it becomes available.')
    else:
        messages.error(request, 'You already have an active reservation or loan for this book.')

    return redirect('book_detail', pk=book_id)


@login_required
def cancel_reservation(request, reservation_id):
    reservation = get_object_or_404(Reservation, pk=reservation_id, user=request.user)
    reservation.status = 'cancelled'
    reservation.save()
    messages.success(request, f'Reservation for "{reservation.book.title}" has been cancelled.')
    return redirect('my_reservations')


@login_required
def manage_reservation(request, reservation_id, action):
    if not is_librarian(request.user):
        messages.error(request, 'You do not have permission to manage reservations.')
        return redirect('my_reservations')

    reservation = get_object_or_404(Reservation, pk=reservation_id)

    if action == 'fulfill':
        if reservation.book.available_copies > 0:
            Loan.objects.create(user=reservation.user, book=reservation.book)
            reservation.status = 'fulfilled'
            reservation.save()
            messages.success(request, f'Reservation fulfilled. Book loaned to {reservation.user.username}.')
        else:
            messages.error(request, 'Book is not available for loan.')

    elif action == 'cancel':
        reservation.status = 'cancelled'
        reservation.save()
        messages.success(request, 'Reservation cancelled.')

    return redirect('all_reservations')


@login_required
def my_loans(request):
    loans = Loan.objects.filter(user=request.user).order_by('-borrowed_date')

    active_loans = loans.filter(returned_date__isnull=True)
    overdue_loans = active_loans.filter(due_date__lt=timezone.now())

    context = {
        'loans': loans,
        'active_loans_count': active_loans.count(),
        'overdue_loans_count': overdue_loans.count()
    }

    return render(request, 'loans/my_loans.html', context)


@login_required
def my_reservations(request):
    reservations = Reservation.objects.filter(user=request.user).order_by('-reserved_date')
    return render(request, 'loans/my_reservations.html', {'reservations': reservations})


@login_required
def loan_history(request):
    loans = Loan.objects.filter(user=request.user).order_by('-borrowed_date')
    return render(request, 'loans/loan_history.html', {'loans': loans})


@login_required
@user_passes_test(is_librarian)
def all_loans(request):
    loans = Loan.objects.all().order_by('-borrowed_date')

    # Фильтрация по статусу
    status_filter = request.GET.get('status')
    if status_filter == 'active':
        loans = loans.filter(returned_date__isnull=True, due_date__gte=timezone.now())
    elif status_filter == 'overdue':
        loans = loans.filter(returned_date__isnull=True, due_date__lt=timezone.now())
    elif status_filter == 'returned':
        loans = loans.filter(returned_date__isnull=False)

    paginator = Paginator(loans, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    stats = {
        'total_loans': Loan.objects.count(),
        'active_loans': Loan.objects.filter(returned_date__isnull=True, due_date__gte=timezone.now()).count(),
        'overdue_loans': Loan.objects.filter(returned_date__isnull=True, due_date__lt=timezone.now()).count(),
        'returned_loans': Loan.objects.filter(returned_date__isnull=False).count(),
    }

    return render(request, 'loans/all_loans.html', {
        'loans': page_obj,
        'page_obj': page_obj,
        'stats': stats
    })


@login_required
@user_passes_test(is_librarian)
def all_reservations(request):
    reservations = Reservation.objects.all().order_by('-reserved_date')

    status_filter = request.GET.get('status')
    if status_filter:
        reservations = reservations.filter(status=status_filter)

    return render(request, 'loans/all_reservations.html', {'reservations': reservations})

