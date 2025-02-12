from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PartViewSet, CarModelViewSet, UserRegistrationView

router = DefaultRouter()
router.register(r'parts', PartViewSet, basename='part')
router.register(r'car_models', CarModelViewSet, basename='car_model')

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('', include(router.urls)),
]
