"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from api.views import (
    MyTokenObtainPairView,
    RegisterView,
    CheckAvailabilityView,
    CreateBookingView,
    CancelBookingView,
    HistoryBookingView
)

from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Endpoint de inicio de sesión (Devuelve Token de Acceso y de Refresco)
    path('api/auth/login/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),

    # Endpoint para obtener un nuevo token de acceso cuando el actual expire
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Endpoint de registro
    path('api/auth/register/', RegisterView.as_view(), name='auth_register'),

    # Endpoint de consultad disponibilidad
    path('api/resource/availability/', CheckAvailabilityView.as_view(), name='check_availability'),

    # Endpoint de creación de reserva
    path('api/booking/', CreateBookingView.as_view(), name='create_booking'),

    # Endpoint de cancelación de reserva
    path('api/booking/<int:pk>/cancel/', CancelBookingView.as_view(), name='cancel_booking'),

    # Endpoint de historial de reservas
    path('api/booking/me/', HistoryBookingView.as_view(), name='history_booking'),
]
