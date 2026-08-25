from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        # 1. Obtenemos el token base generado por Simple JWT
        token = super().get_token(user)

        # 2. Añadimos el rol dentro del payload del token (encriptado)
        # Esto es muy útil para que el Frontend pueda leerlo al decodificar el JWT
        token['role'] = user.role
        token['email'] = user.email

        return token

    def validate(self, attrs):
        # 3. Obtenemos los tokens de acceso y refresco estándar
        data = super().validate(attrs)

        # 4. Inyectamos los datos requeridos en el cuerpo de la respuesta
        data['user_id'] = self.user.id
        data['role'] = self.user.role
        data['email'] = self.user.email

        return data
