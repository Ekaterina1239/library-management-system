from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import Book, Author, Genre
from .forms import BookForm, BookSearchForm


def is_librarian(user):
    return user.user_type in ['librarian', 'it_staff', 'management']


def book_list(request):
    form = BookSearchForm(request.GET or None)
    books = Book.objects.all().select_related('author', 'genre')

    if form.is_valid():
        query = form.cleaned_data.get('query')
        genre = form.cleaned_data.get('genre')
        publication_year = form.cleaned_data.get('publication_year')
        author = form.cleaned_data.get('author')
        available_only = request.GET.get('available_only')

        if query:
            books = books.filter(
                Q(title__icontains=query) |
                Q(author__first_name__icontains=query) |
                Q(author__last_name__icontains=query) |
                Q(isbn__icontains=query) |
                Q(publisher__icontains=query) |
                Q(description__icontains=query)
            )

        if genre:
            books = books.filter(genre=genre)

        if publication_year:
            books = books.filter(publication_year=publication_year)

        if author:
            books = books.filter(author=author)

        if available_only:
            books = books.filter(available_copies__gt=0)

    # Пагинация
    paginator = Paginator(books, 12)  # 12 книг на страницу
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    genres = Genre.objects.all()
    authors = Author.objects.all()

    return render(request, 'books/book_list.html', {
        'page_obj': page_obj,
        'form': form,
        'genres': genres,
        'authors': authors
    })


def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    is_available = book.available_copies > 0

    user_has_loan = False
    user_has_reservation = False

    if request.user.is_authenticated:
        user_has_loan = book.loans.filter(
            user=request.user,
            returned_date__isnull=True
        ).exists()

        user_has_reservation = book.reservations.filter(
            user=request.user,
            status__in=['pending', 'available']
        ).exists()

    return render(request, 'books/book_detail.html', {
        'book': book,
        'is_available': is_available,
        'user_has_loan': user_has_loan,
        'user_has_reservation': user_has_reservation
    })


@login_required
@user_passes_test(is_librarian)
def book_create(request):
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save()
            messages.success(request, f'Book "{book.title}" added successfully!')
            return redirect('book_detail', pk=book.pk)
    else:
        form = BookForm()

    return render(request, 'books/book_form.html', {
        'form': form,
        'title': 'Add New Book',
        'action_url': 'book_create'
    })


@login_required
@user_passes_test(is_librarian)
def book_edit(request, pk):
    book = get_object_or_404(Book, pk=pk)

    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            book = form.save()
            messages.success(request, f'Book "{book.title}" updated successfully!')
            return redirect('book_detail', pk=book.pk)
    else:
        form = BookForm(instance=book)

    return render(request, 'books/book_form.html', {
        'form': form,
        'title': 'Edit Book',
        'action_url': 'book_edit',
        'book': book
    })


@login_required
@user_passes_test(is_librarian)
def book_delete(request, pk):
    book = get_object_or_404(Book, pk=pk)

    if request.method == 'POST':
        book_title = book.title

        # Проверяем, нет ли активных займов этой книги
        active_loans = book.loans.filter(returned_date__isnull=True)
        if active_loans.exists():
            messages.error(request, f'Cannot delete "{book_title}" because it has active loans.')
            return redirect('book_detail', pk=book.pk)

        book.delete()
        messages.success(request, f'Book "{book_title}" deleted successfully!')
        return redirect('book_list')

    return render(request, 'books/book_confirm_delete.html', {'book': book})


def book_search(request):
    query = request.GET.get('q', '')
    books = Book.objects.all()

    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(author__first_name__icontains=query) |
            Q(author__last_name__icontains=query) |
            Q(isbn__icontains=query)
        )[:20]  # Ограничиваем результаты

    return render(request, 'books/search.html', {
        'books': books,
        'query': query
    })


def book_search_api(request):
    query = request.GET.get('q', '')
    if query:
        books = Book.objects.filter(
            Q(title__icontains=query) |
            Q(author__first_name__icontains=query) |
            Q(author__last_name__icontains=query) |
            Q(isbn__icontains=query)
        )[:10]

        results = [{
            'id': book.id,
            'title': book.title,
            'author': str(book.author),
            'is_available': book.is_available,
            'available_copies': book.available_copies,
            'cover_url': book.cover_image.url if book.cover_image else '',
            'detail_url': f'/books/{book.id}/'
        } for book in books]
    else:
        results = []

    return JsonResponse({'results': results})


def genre_list(request):
    genres = Genre.objects.all().prefetch_related('books')
    return render(request, 'books/genre_list.html', {'genres': genres})


def author_list(request):
    authors = Author.objects.all().prefetch_related('books')
    return render(request, 'books/author_list.html', {'authors': authors})