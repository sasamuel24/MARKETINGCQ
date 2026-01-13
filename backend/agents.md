# MarketingCQ Backend API

Sistema de aprobación de artes con arquitectura modular usando FastAPI + SQLAlchemy + PostgreSQL.

## 🏗️ Arquitectura

```
backend/
├── alembic/              # Migraciones de base de datos
├── backend/              # Código fuente principal
│   ├── core/            # Configuración, seguridad, middlewares
│   ├── db/              # Database engine, session, base
│   ├── modules/         # Módulos de negocio (auth, health, requests)
│   ├── storage/         # Manejo de archivos (local/S3)
│   └── main.py          # Entry point de la aplicación
├── scripts/             # Scripts de utilidad
├── tests/               # Tests con pytest
└── storage/uploads/     # Almacenamiento local de archivos
```

## 🚀 Instalación

1. **Crear entorno virtual**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

2. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

3. **Configurar variables de entorno**
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

4. **Crear base de datos PostgreSQL**
```sql
CREATE DATABASE marketingcq_db;
```

5. **Ejecutar migraciones**
```bash
alembic upgrade head
```

## 🏃 Ejecutar

**Modo desarrollo (con hot-reload)**
```bash
uvicorn backend.main:app --reload
```

**Modo producción**
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

## 📚 Documentación API

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🧪 Testing

```bash
pytest
pytest -v  # verbose
pytest --cov=backend  # con cobertura
```

## 🔐 Autenticación

El sistema usa JWT (JSON Web Tokens) con los siguientes endpoints:

- `POST /api/v1/auth/login` - Login y obtener token
- `POST /api/v1/auth/refresh` - Refrescar token
- `GET /api/v1/auth/me` - Obtener usuario actual

## 📦 Módulos

- **auth**: Autenticación y autorización
- **health**: Health checks
- **requests**: CRUD de solicitudes (ejemplo de patrón completo)

## 🗄️ Migraciones

```bash
# Crear nueva migración
alembic revision --autogenerate -m "descripcion"

# Aplicar migraciones
alembic upgrade head

# Revertir última migración
alembic downgrade -1
```

## 🔧 Stack Tecnológico

- **FastAPI**: Framework web moderno y rápido
- **SQLAlchemy 2.0**: ORM con soporte async
- **Alembic**: Migraciones de base de datos
- **Pydantic**: Validación de datos
- **PostgreSQL**: Base de datos
- **JWT**: Autenticación stateless
- **Pytest**: Testing framework
