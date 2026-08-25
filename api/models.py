from django.contrib.auth.models import AbstractUser

from django.db import models

# Create your models here.

class User(AbstractUser):
    # Definimos los roles como opciones
    CLIENT: str = 'client'
    HOST: str = 'host'
    ROLES_CHOICES: list[tuple[str, str]] = [
        (CLIENT, 'Client'),
        (HOST, 'Host'),
    ]

    # unique asegura que no haya duplicado
    email = models.EmailField(unique=True)

    # choices limita los roles a los definidos
    rol = models.CharField(max_length=15, choices=ROLES_CHOICES, default=CLIENT)

    # Por defecto django utiliza username para iniciar sesion
    # podemos cambiar
    USERNAME_FIELD = 'email'

    # Internamente sigue necesitando username
    REQUIRED_FIELDS = ['username']
