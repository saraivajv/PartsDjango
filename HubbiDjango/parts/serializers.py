from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import CarModel, Part

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'user_type']
        extra_kwargs = {
            'user_type': {'default': 'common'}
        }
    
    def create(self, validated_data):
        # Utiliza o método create_user para garantir que a senha seja devidamente criptografada
        user = User.objects.create_user(
            username=validated_data.get('username'),
            email=validated_data.get('email'),
            password=validated_data.get('password'),
            user_type=validated_data.get('user_type', 'common')
        )
        return user

class CarModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarModel
        fields = ['id', 'name', 'manufacturer', 'year']

class PartSerializer(serializers.ModelSerializer):
    # Representa os modelos de carro associados à peça de forma aninhada (read-only)
    car_models = CarModelSerializer(many=True, read_only=True)
    
    class Meta:
        model = Part
        fields = ['id', 'part_number', 'name', 'details', 'price', 'quantity', 'updated_at', 'car_models']
