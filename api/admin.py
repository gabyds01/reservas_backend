from django.contrib import admin

from .models import User, Resource, Availability, Booking

# Registramos los modelos para que sean visibles en el administrador
#
admin.site.register(User)
admin.site.register(Resource)
admin.site.register(Availability)
admin.site.register(Booking)
