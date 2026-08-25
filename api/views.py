from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import MyTokenObtainPairSerializer

from rest_framework import generics
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from .serializers import RegisterSerializer

User = get_user_model()


class MyTokenObtainPairView(TokenObtainPairView):
    # Decimos que utilice nuestra lógica personalizada
    serializer_class = MyTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    # Permitimos que cualquier usuario (incluso anónimos) acceda a este endpoint
    permission_classes = [AllowAny]
