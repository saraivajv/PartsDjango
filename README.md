# HubbiDjango API

Esta é a API RESTful para gerenciamento de peças automotivas e modelos de carro, com autenticação JWT, caching e tarefas assíncronas (Celery). A API permite que:

- Usuários comuns possam listar e visualizar detalhes de peças e modelos de carro.
- Administradores possam realizar operações de CRUD, associações, importação de peças via CSV e acionar a reposição automática de estoque.

Abaixo estão instruções sobre a configuração do ambiente, execução das tarefas assíncronas, execução de testes e utilização de um arquivo CSV para importar peças via Postman.

---

## Índice

- [1. Configuração e Execução do Ambiente](#1-configuracao-e-execucao-do-ambiente)
  - [Requisitos](#requisitos)
  - [Instalação e Configuração](#instalacao-e-configuracao)
  - [Iniciando o Servidor](#iniciando-o-servidor)
- [2. Execução das Tarefas Assíncronas](#2-execucao-das-tarefas-assincronas)
  - [Iniciando o Worker Celery](#iniciando-o-worker-celery)
- [3. Execução dos Testes](#3-execucao-dos-testes)
- [4. Importação de Peças via CSV (Postman)](#4-importacao-de-pecas-via-csv-postman)
- [5. Coleção Postman](#5-colecao-postman)

---

## 1. Configuração e Execução do Ambiente

### Requisitos

- **Python 3.12** (ou versão similar)
- **PostgreSQL** (configurado para ser usado no  `settings.py`)
- **Redis ou Memurai** (para funcionamento do Celery e cache, se configurado)
- **Pacotes** listados em `requirements.txt` (incluindo Django, djangorestframework, django-filter, celery, django-redis, pytest, pytest-django, etc.)

### Instalação e Configuração

1. **Clone o repositório e entre na pasta do projeto**:

```bash
git clone <URL-do-seu-repositorio>
cd HubbiDjango
```

2. **Crie e ative um ambiente virtual**:

```bash
python -m venv venv
# Windows
.venvScriptsactivate
# macOS/Linux
source venv/bin/activate
```

3. **Instale as dependências**:

```bash
pip install -r requirements.txt
```

4. **Configure o banco de dados (PostgreSQL)** no arquivo `HubbiDjango/settings.py`, na seção `DATABASES`. Exemplo:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'hubbi_django',
        'USER': 'postgres',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

5. **Aplique as migrações**:

```bash
python manage.py makemigrations
python manage.py migrate
```

6. **Crie um superusuário (opcional, para uso no Django Admin)**:

```bash
python manage.py createsuperuser
```

### Iniciando o Servidor

Para iniciar o servidor de desenvolvimento, rode:

```bash
python manage.py runserver
```

A API estará acessível em `http://127.0.0.1:8000/`.

---

## 2. Execução das Tarefas Assíncronas

O Celery é utilizado para tarefas assíncronas, como reposição automática de estoque e importação de peças via CSV de forma assíncrona.

### Iniciando o Worker Celery

No diretório do projeto (onde está o `manage.py`), execute:

```bash
celery -A HubbiDjango worker --pool=solo -l info
```

- **`-A HubbiDjango`**: indica ao Celery que o aplicativo principal se chama `HubbiDjango`.
- **`--pool=solo`**: em alguns ambientes Windows/Python 3.12, este pool evita erros relacionados ao multiprocessing.
- **`-l info`**: define o nível de log para informativo.

Quando você aciona endpoints que disparam tarefas Celery (como `/api/parts/restock/` ou `/api/parts/import_csv/`), o worker as processará em segundo plano.

---

## 3. Execução dos Testes

O projeto utiliza **pytest** e **pytest-django** para testes.

1. **Instale as dependências de teste** (já incluídas em `requirements.txt`).
2. **Rode os testes**:

```bash
pytest
```

- O Pytest detectará automaticamente os arquivos `test_*.py` ou `*_tests.py` e executará os testes do Django.
- Caso queira ver mais detalhes, use `pytest -v`.

---

## 4. Importação de Peças via CSV (Postman)

Para importar peças via CSV, utilize a rota `/api/parts/import_csv/`. Segue o fluxo:

1. **Autentique-se** obtendo um token JWT (caso ainda não tenha). Necessário ter um usuário com `user_type=admin`.
2. **Faça uma requisição POST** para `/api/parts/import_csv/`, com **Form-Data**:
   - **key**: `file`
   - **type**: `file`
   - Selecione o arquivo CSV localmente.

   Exemplo de CSV:
   ```
   part_number,name,details,price,quantity
   XPTO1234,Filtro de Óleo,Filtro de alta qualidade,45.00,50
   ABC123,Pastilha de Freio,Conjunto de 4 pastilhas,120.00,30
   ```

3. **Observe o Worker Celery** (veja o log do terminal onde executou `celery -A HubbiDjango worker --pool=solo -l info`). Ele processará o arquivo de forma assíncrona.
4. **Resposta**: O endpoint retornará “Importação CSV iniciada” e um `task_id`. Você pode monitorar o log do worker ou configurar um backend de resultados para confirmar a conclusão.

---

## 5. Coleção Postman

Você pode importar o arquivo JSON (incluído neste repositório ou conforme exibido acima) no Postman para ter acesso rápido aos endpoints. O arquivo contém:

- **Users**: Registro, Obtenção e Renovação de Tokens JWT.
- **Parts**: Listagem, Filtros (`part_number`, `name`, `price`, `price_min`, `price_max`), Criação, Atualização, Remoção e Reabastecimento.
- **Import Parts via CSV**: Envio de arquivo CSV com peças.
- **Car Models**: Listagem, Criação, Atualização, Remoção e Visualização de detalhes.
- **Car Parts Associations**: Associação e desassociação de peças a modelos de carro.
- **Restock Parts**: Para acionar a reposição automática de estoque.

Para usar:

1. **Importe a coleção** no Postman (botão “Import” > “Raw text”).
2. **Configure as variáveis** de ambiente:
   - `base_url`: Geralmente `http://127.0.0.1:8000`
   - `access_token`: Após obter o token JWT via endpoint de login (`/api/token/`), copie o valor do campo `"access"` e cole aqui. Esse token será usado para autenticar nas requisições protegidas.
   - `refresh_token`: Em alguns cenários, você também precisará do token de refresh (campo `"refresh"`). Ele serve para obter um novo access token quando o atual expira. Nesse caso, faça uma requisição para `/api/token/refresh/` com o `"refresh"` token. O endpoint retornará um novo `"access"` token.

---

Boas implementações!
