# Análisis de Arquitectura: EC2 vs Lambda para el Backend de MARKETINGCQ

## Resumen Ejecutivo

**Recomendación: EC2 (o ECS Fargate como evolución natural)**

El backend de MARKETINGCQ tiene características estructurales que lo hacen incompatible con Lambda sin una reescritura significativa. EC2 es la opción correcta hoy; ECS Fargate es la evolución recomendada a mediano plazo.

---

## Características del Backend Analizadas

| Característica | Detalle |
|---|---|
| Framework | FastAPI + Uvicorn (servidor ASGI de larga duración) |
| Base de datos | PostgreSQL via SQLAlchemy 2.0 con connection pooling |
| Pool de conexiones | `pool_size=5`, `max_overflow=10`, `pool_pre_ping=True` |
| Jobs programados | APScheduler (`AsyncIOScheduler`) — resumen semanal por email |
| Procesamiento de archivos | Pillow (miniaturas JPEG), boto3 (S3), presigned URLs |
| Autenticación de email | MSAL (Microsoft Graph API) con caché de tokens OAuth |
| Tamaño | ~12,942 líneas de Python, 13 módulos, ~94 endpoints |
| Arquitectura interna | 3 capas: router → service → repository |

---

## Por qué Lambda NO es la opción correcta

### 1. APScheduler es incompatible con el modelo serverless

El backend usa `AsyncIOScheduler` de APScheduler dentro del ciclo de vida de la aplicación (`@app.lifespan`). Lambda no mantiene procesos vivos entre invocaciones; cuando no hay tráfico, el contenedor se destruye y el scheduler deja de existir.

**Impacto:** El job `weekly_summary_email` simplemente no se ejecutaría de manera confiable. Requeriría reemplazarlo con Amazon EventBridge Scheduled Rules + una Lambda separada.

### 2. Connection Pooling de SQLAlchemy se rompe en Lambda

Lambda puede levantar N instancias en paralelo (una por request concurrente). Cada instancia mantiene su propio pool de conexiones. Con tráfico moderado, esto puede generar cientos de conexiones abiertas a PostgreSQL simultáneamente, agotando el límite de conexiones del servidor.

```
Escenario Lambda con 50 requests concurrentes:
  50 instancias × pool_size=5 = hasta 250 conexiones abiertas
  PostgreSQL default max_connections = 100 → ERROR: too many connections
```

**Impacto directo:** Errores de base de datos bajo carga. Requeriría agregar RDS Proxy (costo adicional ~$0.015/hora) y reconfigurar el pool.

### 3. Cold Starts significativos

FastAPI con las dependencias actuales (SQLAlchemy, Pydantic v2, MSAL, Pillow, boto3, APScheduler, python-jose) genera un paquete de inicialización pesado. Los cold starts en Python con estas librerías pueden tomar **2–5 segundos**, inaceptable para una API de usuario.

### 4. Caché de tokens MSAL no persiste

MSAL guarda el token OAuth de Microsoft Graph en memoria. En Lambda, cada instancia fría debe re-autenticarse desde cero, generando latencia adicional y llamadas innecesarias a los servidores de Microsoft en cada cold start.

### 5. El servidor ASGI no es una función, es un proceso

`uvicorn main:app` es un proceso de larga duración diseñado para manejar múltiples requests. Adaptarlo a Lambda requeriría usar una librería como `Mangum`, lo que introduce una capa de traducción HTTP → ASGI → HTTP con sus propias limitaciones y bugs.

### 6. Límite de 15 minutos (no crítico pero relevante)

El procesamiento de imágenes con Pillow en solicitudes con archivos grandes podría, en combinación con la latencia de S3, acercarse a tiempos de ejecución altos. No es el factor decisivo, pero es un riesgo adicional.

---

## Por qué EC2 es la opción correcta

### 1. Compatibilidad total con Uvicorn/FastAPI

El servidor ASGI corre como proceso continuo. Sin adaptadores, sin cold starts, sin transformaciones HTTP.

```bash
# Deployment simple y directo
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 2. Connection Pooling funciona como fue diseñado

Con EC2, hay **una instancia del proceso** con su pool de conexiones persistente. Las 5 conexiones del pool se reutilizan entre todos los requests, exactamente como SQLAlchemy espera.

### 3. APScheduler funciona nativamente

El `AsyncIOScheduler` vive dentro del mismo proceso de la aplicación durante toda su vida útil. El job del email semanal se ejecuta sin infraestructura adicional.

### 4. Token MSAL en caché durante toda la sesión

El token OAuth de Microsoft Graph se obtiene una vez y se reutiliza hasta su expiración, reduciendo latencia y llamadas a servicios externos.

### 5. Costo predecible para carga constante

Si el sistema tiene usuarios activos durante el horario laboral (8 horas/día, 5 días/semana), EC2 es más económico que Lambda para ese patrón de uso.

---

## Comparación de Costos Estimados (región us-east-1)

| Escenario | EC2 t3.small | Lambda |
|---|---|---|
| 1M requests/mes, 500ms avg | ~$17/mes (instancia + EBS) | ~$8/mes |
| 5M requests/mes, 500ms avg | ~$17/mes (misma instancia) | ~$40/mes |
| 10M requests/mes | ~$35/mes (t3.medium) | ~$80/mes |
| Jobs de scheduler | Incluido | +EventBridge +Lambda extra |
| RDS Proxy (necesario en Lambda) | No aplica | +$11/mes |

> A partir de ~2M requests/mes, EC2 es más económico. Para un sistema empresarial interno con usuarios concurrentes moderados, EC2 gana en costo total.

---

## Recomendación de Infraestructura EC2

```
Internet
    │
    ▼
[Application Load Balancer]  ← HTTPS termination, certificado SSL
    │
    ▼
[EC2 t3.small / t3.medium]   ← FastAPI + Uvicorn (4 workers)
    │           │
    ▼           ▼
[RDS PostgreSQL  [S3 Bucket]  ← Archivos y miniaturas
 db.t3.micro]
```

### Configuración mínima recomendada

```
Instancia: t3.small (2 vCPU, 2 GB RAM) — suficiente para empezar
OS: Amazon Linux 2023
RDS: PostgreSQL db.t3.micro con Multi-AZ desactivado (costo) → activar en producción
ALB: Para HTTPS y health checks
Security Groups: Solo puerto 8000 desde el ALB, no expuesto directo a internet
```

### User Data para arranque automático

```bash
#!/bin/bash
yum update -y
yum install -y python3.11 python3-pip git nginx
cd /app
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8000 --workers 4 &
```

---

## Evolución Recomendada: ECS Fargate (mediano plazo)

ECS Fargate es el **punto medio ideal**: mantiene todas las ventajas de EC2 (proceso continuo, connection pooling, APScheduler, MSAL cache) pero elimina la gestión del servidor.

```
Ventajas de Fargate sobre EC2 puro:
  ✓ No hay que parchear el OS
  ✓ Escalado automático de contenedores
  ✓ Deployments sin downtime (rolling updates)
  ✓ Integración nativa con ECR, CloudWatch, Secrets Manager
  ✓ Pago por segundo de uso del contenedor
```

### Cuándo migrar a Fargate

- Cuando el equipo necesite deployments más frecuentes sin interrupciones
- Cuando se requieran múltiples ambientes (dev/staging/prod) con el mismo stack
- Cuando el tráfico sea variable y se quiera escalar horizontalmente

---

## Checklist de Implementación en EC2

- [ ] Crear VPC con subnets públicas (ALB) y privadas (EC2, RDS)
- [ ] Security Groups: ALB → EC2 (8000), EC2 → RDS (5432), EC2 → Internet (HTTPS saliente)
- [ ] Instancia EC2 con IAM Role (permisos S3, Secrets Manager — nunca access keys en código)
- [ ] Credenciales en AWS Secrets Manager (DB password, MSAL client secret)
- [ ] RDS PostgreSQL en subnet privada, backups automáticos activados
- [ ] ALB con certificado ACM (HTTPS)
- [ ] CloudWatch agent para logs de Uvicorn
- [ ] Alarma CloudWatch: CPU > 80% por 5 minutos
- [ ] Snapshot automático de EBS diario

---

## Conclusión

| Criterio | EC2 | Lambda |
|---|---|---|
| Compatibilidad con FastAPI/Uvicorn | ✅ Nativa | ⚠️ Requiere Mangum |
| APScheduler | ✅ Funciona | ❌ No funciona |
| Connection Pooling SQLAlchemy | ✅ Correcto | ❌ Peligroso |
| MSAL token cache | ✅ Persiste | ❌ Se pierde |
| Cold starts | ✅ Sin cold starts | ❌ 2–5 seg |
| Costo con uso constante | ✅ Predecible | ⚠️ Mayor a escala |
| Esfuerzo de migración desde código actual | ✅ Mínimo | ❌ Alto |
| Gestión de servidor | ⚠️ Necesaria | ✅ No necesaria |

**EC2 gana en 6 de 8 criterios** para este backend específico. Lambda solo sería conveniente si el backend fuera stateless, sin scheduler, sin connection pooling, y con tráfico muy esporádico — ninguna de esas condiciones aplica aquí.
