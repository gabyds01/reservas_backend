from django.contrib.auth.models import AbstractUser

from django.conf import settings

from django.db import models

# Modelos de la aplicación.

class User(AbstractUser):
    # Definimos los roles como opciones
    CLIENT: str = 'client'
    HOST: str = 'host'
    ROLES_CHOICES: list[tuple[str, str]] = [
        (CLIENT, 'Client'),
        (HOST, 'Host'),
    ]

    # unique asegura que no haya duplicados
    email = models.EmailField(unique=True)

    # choices limita los roles a los definidos
    role = models.CharField(max_length=15, choices=ROLES_CHOICES, default=CLIENT)

    # Por defecto django utiliza username para iniciar sesión
    # podemos cambiarlo
    USERNAME_FIELD = 'email'

    # Internamente sigue necesitando username
    REQUIRED_FIELDS = ['username']

class Resource(models.Model):
    # Relacionamos el recurso con el usuario del propietario (HOST)
    owner = models.ForeignKey(
        # No importar el modelo directamente, evita importación circular
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='resources'
    )

    name = models.CharField(max_length=150)

    # Capacidad unitaria
    capacity = models.PositiveIntegerField(default=1)

    # Estado activo / inactivo
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} (Capacidad: {self.capacity})"

class Availability(models.Model):
    AVAILABLE = 'available'
    DISABLED = 'disabled'
    STATES_CHOICES = [
        (AVAILABLE, 'Available'),
        (DISABLED, 'Disabled')
    ]

    resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        related_name='availabilities'
    )

    start_date = models.DateTimeField()
    end_date = models.DateField()

    state = models.CharField(
        max_length=15,
        choices=STATES_CHOICES,
        default=AVAILABLE
    )

    class Meta:
        # Añadimos un nombre representativo para el panel de administración
        verbose_name_plural = 'Availabilities'

    def __str__(self):
        return f"{self.resource.name}: {self.state} ({self.start_date} a {self.end_date})"


# Modelo de reserva, asocia un cliente y un recurso en un espacio temporal
class Booking(models.Model):

    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    CANCELED = 'canceled'

    STATES_CHOICES = [
        (PENDING, 'Pending'),
        (CONFIRMED, 'Confirmed'),
        (CANCELED, 'Canceled')
    ]

    # Relaciones
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings'
    )

    resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        related_name='bookings'
    )

    # Rango temporal
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    # Estado y auditoría
    state = models.CharField(
        max_length=15,
        choices=STATES_CHOICES,
        default=PENDING
    )

    created_at = models.DateTimeField(auto_now_add=True) # Timestamp de creación automática

    class Meta:
        ordering = ['-created_at'] # Las más recientes primero

    def __str__(self):
        return f"Reserva {self.id} - {self.resource.name} ({self.state})"

