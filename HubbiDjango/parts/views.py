from rest_framework import viewsets, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Part, CarModel
from .serializers import PartSerializer, CarModelSerializer, UserRegistrationSerializer
from .permissions import IsAdmin  # Classe de permissão que permite acesso somente a administradores
from django.contrib.auth import get_user_model

User = get_user_model()

# Endpoint de registro (acesso público)
class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

# ViewSet para a entidade Part
class PartViewSet(viewsets.ModelViewSet):
    queryset = Part.objects.all()
    serializer_class = PartSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            # Qualquer usuário autenticado pode visualizar as peças
            return [IsAuthenticated()]
        else:
            # Para criação, edição e deleção, somente administradores
            return [IsAuthenticated(), IsAdmin()]

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdmin])
    def associate(self, request, pk=None):
        """
        Associa uma ou mais peças a modelos de carro.
        Payload exemplo:
        {
          "car_model_ids": [1, 2, 3]
        }
        """
        part = self.get_object()
        car_model_ids = request.data.get('car_model_ids', [])
        car_models = CarModel.objects.filter(id__in=car_model_ids)
        part.car_models.add(*car_models)
        return Response({'status': 'Car models associated'})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsAdmin])
    def disassociate(self, request, pk=None):
        """
        Remove a associação entre uma peça e os modelos de carro indicados.
        Payload exemplo:
        {
          "car_model_ids": [1, 2]
        }
        """
        part = self.get_object()
        car_model_ids = request.data.get('car_model_ids', [])
        car_models = CarModel.objects.filter(id__in=car_model_ids)
        part.car_models.remove(*car_models)
        return Response({'status': 'Car models disassociated'})
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def car_models(self, request, pk=None):
        """
        Retorna todos os modelos de carro associados a esta peça.
        Exemplo de endpoint: GET /api/parts/{id}/car_models/
        """
        part = self.get_object()
        car_models = part.car_models.all()
        serializer = CarModelSerializer(car_models, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsAdmin])
    def restock(self, request):
        """
        Endpoint para acionar a reposição automática de estoque.
        Aqui você pode, por exemplo, chamar uma tarefa assíncrona via Celery.
        """
        # Exemplo: auto_restock.delay()  (se estiver usando Celery)
        return Response({'status': 'Restock process triggered'})

# ViewSet para a entidade CarModel
class CarModelViewSet(viewsets.ModelViewSet):
    queryset = CarModel.objects.all()
    serializer_class = CarModelSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        else:
            return [IsAuthenticated(), IsAdmin()]
        
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def parts(self, request, pk=None):
        """
        Retorna todas as peças associadas a este modelo de carro.
        Exemplo de endpoint: GET /api/car_models/{id}/parts/
        """
        car_model = self.get_object()
        parts = car_model.parts.all()
        serializer = PartSerializer(parts, many=True)
        return Response(serializer.data)
