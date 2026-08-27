from django.utils.dateparse import parse_datetime

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from rest_framework.response import Response

from rest_framework.permissions import AllowAny, IsAuthenticated

from django.contrib.auth import get_user_model

from django.db import transaction

from django.shortcuts import get_object_or_404

from .models import Resource, Availability, Booking

from .serializers import RegisterSerializer, MyTokenObtainPairSerializer, BookingSerializer

User = get_user_model()


class MyTokenObtainPairView(TokenObtainPairView):
    # Decimos que utilice nuestra lógica personalizada
    serializer_class = MyTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    # Permitimos que cualquier usuario (incluso anónimos) acceda a este endpoint
    permission_classes = [AllowAny]


class CheckAvailabilityView(APIView):
    # Cualquiera puede consultar este servicio
    permission_classes = []

    def get(self, request, *args, **kwargs):
        # 1. Recuperamos las entradas
        resource_id = request.query_params.get('resource_id')
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')

        if not resource_id or not start_date_str or not end_date_str:
            return Response(
                {"error": "Faltan parámetros requeridos: resource_id, start_date, end_date."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Parsear fechas en formato ISO 8601
        start_date = parse_datetime(start_date_str)
        end_date = parse_datetime(end_date_str)

        if not start_date or not end_date:
            return Response(
                {"error": "Formato de fecha inválido. Use ISO 8601 (Ej: YYYY-MM-DDTHH:MM:SS)."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validación rango temporal lógico
        if end_date <= start_date:
            return Response(
                {"error": "La fecha de fin debe ser posterior a la fecha de inicio."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. Buscar el recurso solicitado
        try:
            resource = Resource.objects.get(id=resource_id, active=True)
        except Resource.DoesNotExist:
            return Response(
                {"error": "El recurso no existe o no está activo."},
                status=status.HTTP_404_NOT_FOUND
            )

        # 4. Obtener disponibilidades base (Habilitadas)
        available_slots = Availability.objects.filter(
            resource=resource,
            state=Availability.AVAILABLE,
            end_date__gt=start_date,
            start_date__lt=end_date
        ).order_by('start_date')

        # 5. Obtener bloqueos y reservas activas para sustraerlos
        disabled_slots = Availability.objects.filter(
            resource=resource,
            state=Availability.DISABLED,
            end_date__gt=start_date,
            start_date__lt=end_date
        ).order_by('start_date')

        # Excluimos las reservas canceladas
        active_bookings = Booking.objects.filter(
            resource=resource,
            end_date__gt=start_date,
            start_date__lt=end_date
        ).exclude(state=Booking.CANCELED)

        # 6. Preparar listas de intervalos para el algoritmo
        available_intervals = [(s.start_date, s.end_date) for s in available_slots]

        occupied_intervals = []
        for slot in disabled_slots:
            occupied_intervals.append((slot.start_date, slot.end_date))
        for booking in active_bookings:
            occupied_intervals.append((booking.start_date, booking.end_date))

        # Ordenamos los bloques ocupados por fecha de inicio
        occupied_intervals.sort(key=lambda x: x)

        # 7. Algoritmo de resta de intervalos
        # Iniciamos asumiendo que todo el bloque habilitado está libre,
        # y vamos "recortando" las partes que se solapen con bloques o reservas
        for occ_start, occ_end in occupied_intervals:
            remaining_slots = []
            for avail_start, avail_end in available_intervals:
                if occ_end <= avail_start or occ_start >= avail_end:
                    # Sin solapamiento: este bloque libre sigue intacto
                    remaining_slots.append((avail_start, avail_end))
                else:
                    # Solapamiento parcial o total: se divide el bloque libre
                    if occ_start > avail_start:
                        remaining_slots.append((avail_start, occ_start))
                    if occ_end < avail_end:
                        remaining_slots.append((occ_end, avail_end))

            available_intervals = remaining_slots

        # 8. Retornamos la lista final de slots libres formateada
        result = [
            {
                "start_date": start.isoformat(),
                "end_date": end.isoformat()
            }
            for start, end in available_intervals
        ]

        return Response(result, status=status.HTTP_200_OK)

class CreateBookingView(APIView):
    # Obligatorio estar logueado para reservar
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # 1. Extraer datos del request con query params
        resource_id = request.query_params.get('resource_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        # validaciones de entrada
        if not resource_id or not start_date or not end_date:
            return Response({'error': 'Faltan datos (resource_id, start_date, end_date)'}, status=status.HTTP_400_BAD_REQUEST)

        # parseamos las fechas
        start_date = parse_datetime(start_date)
        end_date = parse_datetime(end_date)

        # validaciones de fechas
        if not start_date or not end_date or start_date >= end_date:
            return Response({'error': 'Deben existir los campos start_date y end_date, y start_date debe ser anterior a end_date'}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Inicio de la transacción atómica
        try:
            with transaction.atomic():
                # Obtenemos el recurso aplicando el bloqueo pesimista
                # (select_for_update) para evitar concurrencia
                try:
                    resource = Resource.objects.select_for_update().get(id=resource_id, active=True)
                except Resource.DoesNotExist:
                    return Response({'error': 'Recurso no encontrado o inactivo'}, status=status.HTTP_404_NOT_FOUND)

                # 3. Verificar dispoinibilidad BASE, (¿El HOST tiene recursos disponibles en las fechas solicitadas?)
                is_available = Availability.objects.filter(
                    resource=resource,
                    state=Availability.AVAILABLE,
                    start_date__lte=start_date,
                    end_date__gte=end_date,
                ).exists()

                # El HOST tiene este horario bloqueado?

                is_disabled = Availability.objects.filter(
                    resource=resource,
                    state=Availability.DISABLED,
                    end_date__gt=start_date,
                    start_date__lt=end_date,
                ).exists()

                if not is_available or is_disabled:
                    return Response({'error': 'El recurso no está disponible en las fechas solicitadas'}, status=status.HTTP_409_CONFLICT)

                # 4. Evitar solpamientos (Ya existe una reserva confirmada o pendiente?)
                # excluimos la que estan canceladas
                exist_reservation = Booking.objects.filter(
                    resource=resource,
                    end_date__gt=start_date,
                    start_date__lt=end_date,
                ).exclude(state=Booking.CANCELED).exists()

                if exist_reservation:
                    return Response({'error': 'El recurso no está disponible en las fechas solicitadas'}, status=status.HTTP_409_CONFLICT)

                # 5. CREAR la reserva si todo es valido
                # El cliente se asigna automáticamente a partir del usuario autenticado en la petición (request.user)
                booking = Booking.objects.create(
                    resource=resource,
                    client=request.user,
                    start_date=start_date,
                    end_date=end_date,
                    state=Booking.CONFIRMED
                )

                # Serializamos para devolver la respuesta exitosa
                serializer = BookingSerializer(booking)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class HistoryBookingView(generics.ListAPIView):
    serializer_class = BookingSerializer

    # solo usuarios autenticados
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # filtramos las reservas del usuario autenticado
        return Booking.objects.filter(client=self.request.user)

class CancelBookingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk, *args, **kwargs):
        # 1. Buscamos la reserva utilizando su clave primaria
        booking = get_object_or_404(Booking, id=pk)

        # 2. Verificamos que el usuario autenticado es el cliente de la reserva
        if booking.client != request.user:
            return Response({'error': 'No tienes permiso para cancelar esta reserva'}, status=status.HTTP_403_FORBIDDEN)

        # 3. Cancelación lógica
        booking.state = Booking.CANCELED
        booking.save()

        # 4. Retornamos el objeto actualizado
        serializer = BookingSerializer(booking)
        return Response(serializer.data, status=status.HTTP_200_OK)
