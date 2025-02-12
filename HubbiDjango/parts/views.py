from rest_framework import viewsets, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from .filters import PartFilter
from django_filters.rest_framework import DjangoFilterBackend
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
    filter_backends = [DjangoFilterBackend]
    filterset_class = PartFilter

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'car_models']:
            # Qualquer usuário autenticado pode visualizar as peças
            return [IsAuthenticated()]
        else:
            # Para criação, edição e deleção, somente administradores
            return [IsAuthenticated(), IsAdmin()]
    
    @method_decorator(cache_page(60))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

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
        Endpoint para acionar a reposição automática de estoque manualmente.
        Este endpoint é acessível apenas para administradores.
        
        Quando acionado, ele dispara a tarefa Celery que verifica o estoque
        e reabastece as peças que estão abaixo do limite configurado.
        """
        from .tasks import auto_restock
        task = auto_restock.delay()
        return Response({'status': 'Restock process triggered', 'task_id': task.id})
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsAdmin])
    def import_csv(self, request):
        """
        Endpoint para importar peças via planilha CSV.
        O arquivo deve ser enviado com a chave "file" (multipart/form-data).
        O CSV deve ter o seguinte formato:
        
        part_number, name, details, price, quantity
        XPTO1234, Filtro de Óleo, Filtro de alta qualidade, 45.00, 50
        ABC123, Pastilha de Freio, Conjunto de 4 pastilhas, 120.00, 30
        """
        file = request.FILES.get('file')
        if not file:
            return Response({"error": "Nenhum arquivo enviado."}, status=400)
        try:
            # Lê o conteúdo do arquivo e decodifica (assumindo codificação utf-8)
            file_data = file.read().decode('utf-8')
        except Exception as e:
            return Response({"error": f"Erro ao ler o arquivo: {e}"}, status=400)
        
        # Importa a tarefa do Celery e a dispara de forma assíncrona
        from .tasks import import_parts_csv
        task = import_parts_csv.delay(file_data)
        return Response({"status": "Importação CSV iniciada", "task_id": task.id})
    

# ViewSet para a entidade CarModel
class CarModelViewSet(viewsets.ModelViewSet):
    queryset = CarModel.objects.all()
    serializer_class = CarModelSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'parts']:
            return [IsAuthenticated()]
        else:
            return [IsAuthenticated(), IsAdmin()]
    
    @method_decorator(cache_page(60))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
        
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
