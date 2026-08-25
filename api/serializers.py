from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from django.contrib.auth import get_user_model

from rest_framework import serializers

User = get_user_model()

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


class RegisterSerializer(serializers.ModelSerializer):
    # Definimos la contraseña como "solo escritura" para que nunca viaje de vuelta en la respuesta JSON
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'role']

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este correo ya está registrado.")

        return value

    def create(self, validated_data):
        # USAR create_user ES CLAVE: Django se encarga de aplicar hashing (PBKDF2) y salting
        # automáticamente a la contraseña para que sea 100% segura.

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            role=validated_data.get('role', User.CLIENT) # Si no se envía role, por defecto es cliente
        )

        return user
