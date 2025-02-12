import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from parts.models import Part, CarModel

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username="admin", 
        password="adminpass", 
        email="admin@example.com", 
        user_type="admin"
    )

@pytest.fixture
def common_user(db):
    return User.objects.create_user(
        username="common", 
        password="commonpass", 
        email="common@example.com", 
        user_type="common"
    )

@pytest.fixture
def admin_token(api_client, admin_user):
    url = reverse("token_obtain_pair")
    response = api_client.post(url, {"username": "admin", "password": "adminpass"}, format="json")
    assert response.status_code == status.HTTP_200_OK
    return response.data["access"]

@pytest.fixture
def common_token(api_client, common_user):
    url = reverse("token_obtain_pair")
    response = api_client.post(url, {"username": "common", "password": "commonpass"}, format="json")
    assert response.status_code == status.HTTP_200_OK
    return response.data["access"]

@pytest.fixture
def sample_part(db):
    part = Part.objects.create(
        part_number="P001",
        name="Filtro de Óleo",
        details="Filtro de alta qualidade",
        price=45.00,
        quantity=50
    )
    return part

@pytest.fixture
def sample_car_model(db):
    car_model = CarModel.objects.create(
        name="Modelo X",
        manufacturer="Fabricante Y",
        year=2020
    )
    return car_model

# Testes de API

def test_user_registration(api_client, db):
    url = reverse("register")
    data = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "testpassword",
        "user_type": "common"
    }
    response = api_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    # Verifica se o usuário foi criado
    assert User.objects.filter(username="testuser").exists()

def test_obtain_jwt_token(api_client, admin_user):
    url = reverse("token_obtain_pair")
    data = {"username": "admin", "password": "adminpass"}
    response = api_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data
    assert "refresh" in response.data

def test_unauthenticated_access(api_client):
    url = reverse("part-list")
    response = api_client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_list_parts_with_pagination(api_client, common_user, sample_part):
    api_client.force_authenticate(user=common_user)
    url = reverse("part-list")
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    # Se a paginação estiver configurada, deve haver a chave "results"
    assert "results" in response.data

def test_create_part_as_admin(api_client, admin_token):
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {admin_token}")
    url = reverse("part-list")
    data = {
        "part_number": "P002",
        "name": "Pastilha de Freio",
        "details": "Conjunto de 4 pastilhas",
        "price": 120.00,
        "quantity": 30
    }
    response = api_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert Part.objects.filter(part_number="P002").exists()

def test_create_part_as_common_user(api_client, common_token):
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {common_token}")
    url = reverse("part-list")
    data = {
        "part_number": "P003",
        "name": "Sensor de Oxigênio",
        "details": "Sensor para controle da mistura ar/combustível",
        "price": 150.00,
        "quantity": 20
    }
    response = api_client.post(url, data, format="json")
    # Usuários comuns não podem criar peças, então espera 403 Forbidden
    assert response.status_code == status.HTTP_403_FORBIDDEN

def test_update_part_as_admin(api_client, admin_token, sample_part):
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {admin_token}")
    url = reverse("part-detail", args=[sample_part.id])
    data = {"price": 50.00}
    response = api_client.patch(url, data, format="json")
    assert response.status_code == status.HTTP_200_OK
    sample_part.refresh_from_db()
    assert sample_part.price == 50.00

def test_filter_parts_by_name(api_client, admin_token, sample_part):
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {admin_token}")
    url = f"{reverse('part-list')}?name=Filtro"
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    results = response.data.get("results", [])
    # Verifica se há pelo menos um item com o nome contendo "Filtro"
    assert any("Filtro" in part["name"] for part in results)

# Testes de CarModel

def test_list_car_models(api_client, common_user, sample_car_model):
    api_client.force_authenticate(user=common_user)
    url = reverse("car_model-list")
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK

def test_create_car_model_as_admin(api_client, admin_token):
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {admin_token}")
    url = reverse("car_model-list")
    data = {
        "name": "Modelo Z",
        "manufacturer": "Fabricante Z",
        "year": 2021
    }
    response = api_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    from parts.models import CarModel
    assert CarModel.objects.filter(name="Modelo Z").exists()

def test_car_model_associated_parts(api_client, common_user, sample_car_model, sample_part):
    # Garanta que a peça esteja associada ao modelo de carro
    sample_car_model.parts.add(sample_part)
    api_client.force_authenticate(user=common_user)
    url = reverse("car_model-parts", args=[sample_car_model.id])
    response = api_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    # Verifica que pelo menos uma peça está associada
    assert len(response.data) > 0
