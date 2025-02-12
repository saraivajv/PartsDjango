from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    
    USER_TYPE_CHOICES = (
        ('common', 'Usuário Comum'),
        ('admin', 'Administrador'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='common')

    def __str__(self):
        return self.username


class CarModel(models.Model):
    name = models.CharField(max_length=255)
    manufacturer = models.CharField(max_length=255)
    year = models.IntegerField()

    def __str__(self):
        return f"{self.manufacturer} {self.name} ({self.year})"


class Part(models.Model):
    part_number = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    details = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()
    updated_at = models.DateTimeField(auto_now=True)

    # Relacionamento muitos-para-muitos com CarModel
    car_models = models.ManyToManyField(CarModel, related_name='parts')

    def __str__(self):
        return self.name
