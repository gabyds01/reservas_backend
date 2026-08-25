from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import MyTokenObtainPairSerializer

# Create your views here.

class MyTokenObtainPairView(TokenObtainPairView):
    # Decimos que utilice nuestra lógica personalizada
    serializer_class = MyTokenObtainPairSerializer
