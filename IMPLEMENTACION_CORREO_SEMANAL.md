# Implementación: Correo Semanal de Resumen de Artes Pendientes

**Fecha:** 2026-02-18
**Módulo afectado:** `backend/`
**Usuarios objetivo:** ID = 2 y ID = 4
**Frecuencia:** Una vez por semana (configurable)

---

## 1. Contexto del Sistema Actual

### Stack tecnológico relevante
| Componente | Tecnología |
|---|---|
| API | FastAPI |
| ORM | SQLAlchemy + PostgreSQL |
| Email | Microsoft Graph API (MSAL) |
| Auth | JWT (python-jose) |
| Scheduler | **No existe actualmente** |

### Flujo de aprobación actual
```
Solicitud creada → Etapa 1 (aprobadores notificados al instante)
                → Etapa 2 → ... → APROBADO_FINAL / RECHAZADO
```

Los correos hoy se disparan de forma **reactiva** (evento → correo).
El correo semanal es **proactivo** (tiempo → correo de resumen acumulado).

---

## 2. Arquitectura de la Solución

### 2.1 Diagrama de flujo

```
┌─────────────────────────────────────────────────────┐
│  APScheduler (proceso interno de FastAPI)           │
│                                                     │
│  Cada lunes a las 08:00 AM (configurable)           │
│         │                                           │
│         ▼                                           │
│  weekly_summary_job()                               │
│         │                                           │
│         ▼                                           │
│  WeeklySummaryService                               │
│         │                                           │
│         ├── get_pending_solicitudes_for_user(id=2)  │
│         │         │                                 │
│         │         └─► DB Query: solicitudes         │
│         │              pendientes donde user_id=2   │
│         │              es aprobador de la etapa     │
│         │              actual                       │
│         │                                           │
│         ├── get_pending_solicitudes_for_user(id=4)  │
│         │                                           │
│         └── Para cada usuario con solicitudes:      │
│               send_weekly_summary_email()           │
│                     │                               │
│                     ▼                               │
│               EmailService (Microsoft Graph)        │
└─────────────────────────────────────────────────────┘
```

### 2.2 Decisión arquitectónica: APScheduler in-process

**Opción elegida:** `APScheduler` integrado directamente en FastAPI.

| Alternativa | Pros | Contras | Decisión |
|---|---|---|---|
| **APScheduler** | Simple, sin infraestructura extra, un solo proceso | No distribuido, muere si el proceso cae | ✅ **Elegido** |
| Celery + Redis | Escalable, distribuido, retry logic | Requiere Redis, proceso separado, overhead | ❌ Excesivo para este caso |
| Cron del SO | Independiente del proceso | Más complejo de mantener, acceso a DB separado | ❌ Acoplamiento externo |
| GitHub Actions / Cloud Scheduler | Independiente, robusto | Requiere endpoint público o infraestructura cloud | ❌ Dependencia externa |

**Justificación:** Con solo 2 usuarios objetivo y frecuencia semanal, APScheduler es suficiente y no agrega complejidad operacional.

---

## 3. Consulta de Base de Datos

### 3.1 Lógica de la query

Para un usuario con `user_id = X`, necesitamos encontrar todas las `solicitudes` que:
1. El usuario es aprobador de la **etapa actual** de esa solicitud (`etapa_aprobadores.user_id = X`)
2. La solicitud **no está en estado final** (no es APROBADO_FINAL ni RECHAZADO)
3. La etapa del aprobador coincide con la **etapa actual** de la solicitud

```sql
-- Solicitudes pendientes de aprobación para un usuario específico
SELECT
    s.id,
    s.title,
    s.description,
    s.created_at,
    e.label AS etapa_label,
    est.label AS estado_label,
    u_creador.full_name AS creado_por,
    a.nombre AS area
FROM solicitudes s
INNER JOIN etapas e ON s.stage_id = e.id
INNER JOIN estados est ON s.status_id = est.id
INNER JOIN etapa_aprobadores ea
    ON ea.etapa_id = s.stage_id
    AND ea.user_id = :user_id
    AND ea.is_active = true
INNER JOIN usuarios u_creador ON s.created_by_user_id = u_creador.id
INNER JOIN areas a ON s.area_id = a.id
WHERE
    est.is_final = false
    AND est.code NOT IN ('RECHAZADO', 'AJUSTES_SOLICITADOS')
ORDER BY s.created_at ASC;
```

### 3.2 Modelos SQLAlchemy involucrados

```
Usuario (id, full_name, email)
    ↕ via etapa_aprobadores
EtapaAprobador (etapa_id, user_id, is_active)
    ↕
Etapa (id, label, order, area_id)
    ↕ (stage_id en solicitudes)
Solicitud (id, title, stage_id, status_id, created_by_user_id, area_id)
    ↕
Estado (id, code, label, is_final)
```

---

## 4. Archivos a Crear / Modificar

### 4.1 Archivos NUEVOS

```
backend/
├── core/
│   └── scheduler.py                    ← NUEVO: Configuración APScheduler
├── modules/
│   └── weekly_summary/                 ← NUEVO: Módulo completo
│       ├── __init__.py
│       ├── job.py                      ← NUEVO: La tarea programada
│       ├── service.py                  ← NUEVO: Lógica de negocio
│       └── repository.py              ← NUEVO: Queries a DB
```

### 4.2 Archivos MODIFICADOS

```
backend/
├── core/
│   └── email.py                        ← MODIFICADO: Agregar send_weekly_summary_email()
├── core/
│   └── config.py                       ← MODIFICADO: Agregar WEEKLY_SUMMARY_USER_IDS, WEEKLY_CRON_DAY, WEEKLY_CRON_HOUR
└── main.py                             ← MODIFICADO: Iniciar/apagar scheduler con lifespan
```

---

## 5. Implementación Paso a Paso

### PASO 1: Instalar dependencia

```bash
pip install apscheduler==3.10.4
```

Agregar a `backend/requirements.txt`:
```
apscheduler==3.10.4
```

---

### PASO 2: Configuración (`core/config.py`)

Agregar al modelo `Settings` de Pydantic:

```python
# Weekly Summary Email
WEEKLY_SUMMARY_USER_IDS: list[int] = [2, 4]   # IDs de usuarios objetivo
WEEKLY_CRON_DAY: str = "mon"                    # Día de la semana (mon/tue/.../sun)
WEEKLY_CRON_HOUR: int = 8                       # Hora (24h): 8 = 08:00 AM
WEEKLY_CRON_MINUTE: int = 0                     # Minutos
WEEKLY_SUMMARY_ENABLED: bool = True             # Interruptor ON/OFF
```

En `.env` (opcional para override):
```env
WEEKLY_SUMMARY_USER_IDS=[2,4]
WEEKLY_CRON_DAY=mon
WEEKLY_CRON_HOUR=8
WEEKLY_CRON_MINUTE=0
WEEKLY_SUMMARY_ENABLED=true
```

---

### PASO 3: Scheduler (`core/scheduler.py`)

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = AsyncIOScheduler(timezone="America/Mexico_City")  # Ajustar a tu zona horaria

def setup_scheduler():
    """Configura y retorna el scheduler con todos los jobs."""
    from backend.core.config import settings
    from backend.modules.weekly_summary.job import run_weekly_summary

    if settings.WEEKLY_SUMMARY_ENABLED:
        scheduler.add_job(
            func=run_weekly_summary,
            trigger=CronTrigger(
                day_of_week=settings.WEEKLY_CRON_DAY,
                hour=settings.WEEKLY_CRON_HOUR,
                minute=settings.WEEKLY_CRON_MINUTE,
            ),
            id="weekly_summary_email",
            name="Resumen semanal de artes pendientes",
            replace_existing=True,
            misfire_grace_time=3600,  # Si el server estuvo caído, hasta 1h de retraso
        )

    return scheduler
```

> **`misfire_grace_time=3600`**: Si el servidor estuvo caído cuando debía correr el job, lo ejecuta hasta 1 hora después al reiniciarse. Evita perder el envío semanal.

---

### PASO 4: Repository (`modules/weekly_summary/repository.py`)

```python
from sqlalchemy.orm import Session, joinedload
from backend.db.models import Solicitud, EtapaAprobador, Estado, Etapa, Usuario, Area

def get_pending_solicitudes_for_user(db: Session, user_id: int) -> list[Solicitud]:
    """
    Retorna solicitudes donde el usuario es aprobador de la etapa actual
    y la solicitud NO está en estado final.
    """
    return (
        db.query(Solicitud)
        .join(EtapaAprobador,
              (EtapaAprobador.etapa_id == Solicitud.stage_id) &
              (EtapaAprobador.user_id == user_id) &
              (EtapaAprobador.is_active == True))
        .join(Estado, Solicitud.status_id == Estado.id)
        .options(
            joinedload(Solicitud.stage),
            joinedload(Solicitud.state),
            joinedload(Solicitud.area),
            joinedload(Solicitud.created_by),
        )
        .filter(Estado.is_final == False)
        .filter(Estado.code.notin_(["RECHAZADO", "AJUSTES_SOLICITADOS"]))
        .order_by(Solicitud.created_at.asc())
        .all()
    )


def get_user_by_id(db: Session, user_id: int) -> Usuario | None:
    return db.query(Usuario).filter(Usuario.id == user_id).first()
```

---

### PASO 5: Service (`modules/weekly_summary/service.py`)

```python
import logging
from sqlalchemy.orm import Session
from backend.core.email import email_service
from backend.modules.weekly_summary.repository import (
    get_pending_solicitudes_for_user,
    get_user_by_id,
)

logger = logging.getLogger(__name__)


class WeeklySummaryService:

    def run_for_users(self, db: Session, user_ids: list[int]) -> None:
        """
        Ejecuta el envío del resumen semanal para los usuarios indicados.
        Procesa cada usuario de forma independiente para que un error en uno
        no bloquee al otro.
        """
        for user_id in user_ids:
            try:
                self._process_user(db, user_id)
            except Exception as e:
                logger.error(
                    f"[WeeklySummary] Error procesando usuario {user_id}: {e}",
                    exc_info=True,
                )

    def _process_user(self, db: Session, user_id: int) -> None:
        usuario = get_user_by_id(db, user_id)
        if not usuario:
            logger.warning(f"[WeeklySummary] Usuario {user_id} no encontrado. Saltando.")
            return

        solicitudes = get_pending_solicitudes_for_user(db, user_id)

        if not solicitudes:
            logger.info(
                f"[WeeklySummary] Usuario {usuario.full_name} (id={user_id}) "
                f"no tiene solicitudes pendientes. No se envía correo."
            )
            return

        logger.info(
            f"[WeeklySummary] Enviando resumen a {usuario.email} "
            f"con {len(solicitudes)} solicitudes pendientes."
        )
        email_service.send_weekly_summary_email(
            recipient_email=usuario.email,
            recipient_name=usuario.full_name,
            solicitudes=solicitudes,
        )


weekly_summary_service = WeeklySummaryService()
```

---

### PASO 6: Job (`modules/weekly_summary/job.py`)

```python
import logging
from backend.db.session import SessionLocal
from backend.core.config import settings
from backend.modules.weekly_summary.service import weekly_summary_service

logger = logging.getLogger(__name__)


async def run_weekly_summary() -> None:
    """
    Entry point del job. Crea su propia sesión de DB, ejecuta el servicio
    y cierra la sesión al terminar.
    """
    logger.info("[WeeklySummary] Iniciando job de resumen semanal...")
    db = SessionLocal()
    try:
        weekly_summary_service.run_for_users(
            db=db,
            user_ids=settings.WEEKLY_SUMMARY_USER_IDS,
        )
        logger.info("[WeeklySummary] Job completado exitosamente.")
    except Exception as e:
        logger.error(f"[WeeklySummary] Error en job: {e}", exc_info=True)
    finally:
        db.close()
```

> **Importante:** El job crea su **propia sesión de DB** (no usa las de los requests HTTP). Esto es necesario porque el scheduler corre en un contexto diferente al de los endpoints FastAPI.

---

### PASO 7: Plantilla de correo (`core/email.py`)

Agregar el método `send_weekly_summary_email()` a la clase `EmailService`:

```python
def send_weekly_summary_email(
    self,
    recipient_email: str,
    recipient_name: str,
    solicitudes: list,  # List[Solicitud]
) -> None:
    """Envía el resumen semanal de artes pendientes de aprobación."""

    # Construir filas de la tabla HTML
    filas_html = ""
    for s in solicitudes:
        dias_pendiente = (datetime.utcnow() - s.created_at).days
        alerta_clase = "color: #c0392b; font-weight: bold;" if dias_pendiente > 7 else ""
        filas_html += f"""
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #eee;">{s.title}</td>
            <td style="padding: 10px; border-bottom: 1px solid #eee;">{s.area.nombre}</td>
            <td style="padding: 10px; border-bottom: 1px solid #eee;">{s.stage.label}</td>
            <td style="padding: 10px; border-bottom: 1px solid #eee;">
                <span style="{alerta_clase}">{dias_pendiente} día(s)</span>
            </td>
            <td style="padding: 10px; border-bottom: 1px solid #eee;">
                <a href="{settings.FRONTEND_URL}/solicitudes/{s.id}"
                   style="color: #00829a; text-decoration: none;">Ver arte</a>
            </td>
        </tr>
        """

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
        <div style="max-width: 700px; margin: 0 auto; background: white;
                    border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">

            <!-- Header -->
            <div style="background-color: #00829a; padding: 24px 32px;">
                <h1 style="color: white; margin: 0; font-size: 22px;">
                    Resumen Semanal de Artes Pendientes
                </h1>
                <p style="color: rgba(255,255,255,0.85); margin: 8px 0 0 0; font-size: 14px;">
                    Marketing CQ · Semana del {_get_week_range()}
                </p>
            </div>

            <!-- Body -->
            <div style="padding: 32px;">
                <p style="color: #333; font-size: 15px;">
                    Hola <strong>{recipient_name}</strong>,
                </p>
                <p style="color: #555; font-size: 14px;">
                    Tienes <strong style="color: #00829a;">{len(solicitudes)}</strong>
                    arte(s) pendiente(s) de tu aprobación esta semana:
                </p>

                <!-- Tabla de solicitudes -->
                <table style="width: 100%; border-collapse: collapse; margin-top: 16px;
                              font-size: 13px; color: #333;">
                    <thead>
                        <tr style="background-color: #f0f9fb;">
                            <th style="padding: 10px; text-align: left; color: #00829a;">Título</th>
                            <th style="padding: 10px; text-align: left; color: #00829a;">Área</th>
                            <th style="padding: 10px; text-align: left; color: #00829a;">Etapa</th>
                            <th style="padding: 10px; text-align: left; color: #00829a;">Tiempo en espera</th>
                            <th style="padding: 10px; text-align: left; color: #00829a;">Acción</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filas_html}
                    </tbody>
                </table>

                <!-- CTA -->
                <div style="text-align: center; margin-top: 28px;">
                    <a href="{settings.FRONTEND_URL}"
                       style="background-color: #96c121; color: white; padding: 12px 28px;
                              border-radius: 6px; text-decoration: none; font-size: 14px;
                              font-weight: bold; display: inline-block;">
                        Ir al Panel de Aprobaciones
                    </a>
                </div>
            </div>

            <!-- Footer -->
            <div style="background-color: #f9f9f9; padding: 16px 32px;
                        border-top: 1px solid #eee; text-align: center;">
                <p style="color: #999; font-size: 12px; margin: 0;">
                    Este correo es generado automáticamente · Marketing CQ
                </p>
            </div>
        </div>
    </body>
    </html>
    """

    self.send_email(
        to_email=recipient_email,
        subject=f"[Marketing CQ] Resumen semanal: {len(solicitudes)} arte(s) por aprobar",
        html_body=html_body,
    )


def _get_week_range() -> str:
    """Retorna el rango de la semana actual como string legible."""
    from datetime import datetime, timedelta
    today = datetime.utcnow()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    return f"{monday.strftime('%d/%m')} - {sunday.strftime('%d/%m/%Y')}"
```

---

### PASO 8: Integrar scheduler en `main.py`

Reemplazar los `@app.on_event("startup")` deprecados por el patrón `lifespan`:

```python
from contextlib import asynccontextmanager
from backend.core.scheduler import setup_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── STARTUP ──
    scheduler = setup_scheduler()
    scheduler.start()
    print(f"✅ Scheduler iniciado. Jobs: {[j.name for j in scheduler.get_jobs()]}")

    yield  # La app corre aquí

    # ── SHUTDOWN ──
    scheduler.shutdown(wait=False)
    print("🔴 Scheduler detenido.")


app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
    ...
)
```

---

## 6. Endpoint Manual de Disparo (para pruebas)

Agregar un endpoint de administración para disparar el job manualmente sin esperar el lunes:

```python
# En main.py o en un router admin separado
@app.post("/api/v1/admin/trigger-weekly-summary", include_in_schema=False)
async def trigger_weekly_summary(
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Disparador manual del resumen semanal (solo para administradores)."""
    from backend.modules.weekly_summary.service import weekly_summary_service
    from backend.core.config import settings

    weekly_summary_service.run_for_users(
        db=db,
        user_ids=settings.WEEKLY_SUMMARY_USER_IDS,
    )
    return {"message": "Resumen semanal enviado manualmente"}
```

> Proteger este endpoint verificando que el `current_user_id` tenga rol administrador.

---

## 7. Diagrama de Secuencia Completo

```
Lunes 08:00 AM
      │
      ▼
APScheduler.trigger()
      │
      ▼
run_weekly_summary() [job.py]
      │
      ├── db = SessionLocal()
      │
      ▼
WeeklySummaryService.run_for_users(db, [2, 4])
      │
      ├── Para user_id = 2:
      │     ├── get_user_by_id(db, 2) → Usuario(email="...", full_name="...")
      │     ├── get_pending_solicitudes_for_user(db, 2) → [Solicitud, ...]
      │     └── email_service.send_weekly_summary_email(...)
      │               └── Microsoft Graph API → 📧 correo enviado
      │
      └── Para user_id = 4:
            ├── get_user_by_id(db, 4)
            ├── get_pending_solicitudes_for_user(db, 4)
            └── email_service.send_weekly_summary_email(...)
                          └── Microsoft Graph API → 📧 correo enviado
```

---

## 8. Consideraciones y Puntos Críticos

### 8.1 Zona horaria
El servidor probablemente corre en UTC. Configurar `APScheduler` con la zona horaria correcta para que `08:00 AM` signifique 08:00 hora local:
```python
scheduler = AsyncIOScheduler(timezone="America/Mexico_City")
# o bien: "America/Bogota", "America/Lima", "America/Santiago", etc.
```

### 8.2 Reinicio del servidor
Si el servidor se reinicia justo antes de la hora programada y el job no corre, `misfire_grace_time=3600` lo ejecutará dentro de la siguiente hora. Sin esta configuración, el job simplemente se pierde.

### 8.3 Sesión de DB independiente
El scheduler no tiene acceso al ciclo de vida de los requests HTTP. **El job debe crear y cerrar su propia sesión de DB** usando `SessionLocal()`. No usar `Depends(get_db)` desde un job.

### 8.4 No bloquear el evento loop
El email se envía via HTTP (Microsoft Graph). Como el job es `async`, usar `httpx.AsyncClient` en el email service o correr la llamada con `asyncio.to_thread()` si el cliente actual es síncrono (requests).

### 8.5 Logs y monitoreo
Todos los pasos deben loguear con `logger.info/error`. Verificar que el logging esté configurado para persistir (archivo o servicio externo) y así poder auditar si el job corrió y cuántos correos se enviaron.

### 8.6 Idempotencia
Si el job se dispara dos veces en la misma semana (error operacional), se enviarán dos correos. Para evitarlo, se puede:
- Guardar en DB la última vez que se envió (`weekly_summary_sent_at` en tabla `usuarios`)
- Verificar si ya se envió en la misma semana antes de enviar

### 8.7 Email vacío
Si un usuario no tiene solicitudes pendientes **no enviar el correo**. Ya está contemplado en el service (`if not solicitudes: return`).

---

## 9. Checklist de Implementación

```
[ ] 1. pip install apscheduler==3.10.4  →  agregar a requirements.txt
[ ] 2. Actualizar core/config.py        →  agregar settings de scheduler
[ ] 3. Crear core/scheduler.py          →  instancia y configuración de APScheduler
[ ] 4. Crear modules/weekly_summary/__init__.py
[ ] 5. Crear modules/weekly_summary/repository.py  →  query de solicitudes pendientes
[ ] 6. Crear modules/weekly_summary/service.py     →  lógica de negocio y loop de usuarios
[ ] 7. Crear modules/weekly_summary/job.py         →  entry point del cron job
[ ] 8. Modificar core/email.py          →  agregar send_weekly_summary_email()
[ ] 9. Modificar main.py                →  lifespan con start/stop del scheduler
[ ] 10. Agregar endpoint admin manual   →  para pruebas sin esperar el lunes
[ ] 11. Ajustar timezone en scheduler   →  configurar zona horaria correcta
[ ] 12. Probar con endpoint manual      →  verificar llegada de correo
[ ] 13. Verificar logs al reiniciar     →  confirmar que el job aparece en startup
[ ] 14. Deploy y monitorear primer lunes automático
```

---

## 10. Estructura Final de Archivos

```
backend/
├── core/
│   ├── config.py          (MODIFICADO)
│   ├── email.py           (MODIFICADO → +send_weekly_summary_email)
│   └── scheduler.py       (NUEVO)
├── modules/
│   └── weekly_summary/    (NUEVO módulo completo)
│       ├── __init__.py
│       ├── job.py
│       ├── repository.py
│       └── service.py
└── main.py                (MODIFICADO → lifespan con scheduler)
```

---

## 11. Ejemplo de Correo Resultante

```
Asunto: [Marketing CQ] Resumen semanal: 3 arte(s) por aprobar

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  RESUMEN SEMANAL DE ARTES PENDIENTES
  Marketing CQ · Semana del 16/02 - 22/02/2026
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Hola [Nombre del Usuario],

Tienes 3 arte(s) pendiente(s) de tu aprobación:

┌──────────────────────┬──────────┬────────────┬──────────────┬──────────────┐
│ Título               │ Área     │ Etapa      │ En espera    │ Acción       │
├──────────────────────┼──────────┼────────────┼──────────────┼──────────────┤
│ Campaña Verano 2026  │ Ventas   │ Revisión 1 │ 2 día(s)     │ [Ver arte]   │
│ Banner Redes Feb     │ Digital  │ Revisión 2 │ 5 día(s)     │ [Ver arte]   │
│ Flyer Promoción      │ Tienda   │ Revisión 1 │ 12 día(s) ⚠️ │ [Ver arte]   │
└──────────────────────┴──────────┴────────────┴──────────────┴──────────────┘

              [ Ir al Panel de Aprobaciones ]

────────────────────────────────────────
Este correo es generado automáticamente · Marketing CQ
```

> Los artes con más de 7 días esperando se resaltan en rojo como alerta de urgencia.
