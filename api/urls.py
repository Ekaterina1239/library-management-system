from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'books', views.BookViewSet, basename='book')
router.register(r'authors', views.AuthorViewSet, basename='author')
router.register(r'genres', views.GenreViewSet, basename='genre')
router.register(r'loans', views.LoanViewSet, basename='loan')
router.register(r'reservations', views.ReservationViewSet, basename='reservation')
router.register(r'notifications', views.NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/login/', views.AuthView.as_view(), name='api-login'),
    path('auth/register/', views.RegisterView.as_view(), name='api-register'),
]