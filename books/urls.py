from django.urls import path
from . import views

urlpatterns = [
    path('', views.book_list, name='book_list'),
    path('<int:pk>/', views.book_detail, name='book_detail'),
    path('create/', views.book_create, name='book_create'),
    path('<int:pk>/edit/', views.book_edit, name='book_edit'),
    path('<int:pk>/delete/', views.book_delete, name='book_delete'),
    path('search/', views.book_search, name='book_search'),
    path('api/search/', views.book_search_api, name='book_search_api'),
    path('genres/', views.genre_list, name='genre_list'),
    path('authors/', views.author_list, name='author_list'),
]