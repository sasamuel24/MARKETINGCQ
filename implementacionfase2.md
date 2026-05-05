# Plan de Implementación: Flujo de Iniciativa de Producto (Fase 2)

## Visión General del Flujo Completo

```
[1] Director Mercadeo          [2] Gerencia General
    Análisis de mercado    →       Aprueba + Business Case
    Crea Iniciativa                      ↓
                               [3] Notificación automática
                                   a Área 4
                                         ↓
                               [4] Área 4 - Prototipado
                                   Diagnóstico técnico
                                   Cierre diagnóstico
                                         ↓
                               [5] Aprobación dual
                               ┌──────────────────────┐
                               │ Luisa Ibañez (App)   │
                               │ Gerente Tiendas (?)  │
                               └──────────────────────┘
                                         ↓
                               [6] Junta Directiva
                                   Aprobación final
                                         ↓
                               [7] Auto-crea solicitud
                                   → INNOVACION (área 2)
                                   → Flujo normal existente
```

---

## Fase 1 — Nueva Entidad: `Iniciativa de Producto`

### Por qué no usar `solicitudes` existente
La solicitud actual asume que existe un área, etapas y aprobadores configurados. La iniciativa
es un flujo previo, más libre, con campos distintos (análisis de competencia, Business Case,
producto propuesto). Mezclarlos complicaría la lógica existente.

### Nueva tabla `iniciativas`

```sql
CREATE TABLE iniciativas (
  id                     SERIAL PRIMARY KEY,
  titulo                 VARCHAR(255) NOT NULL,
  producto_propuesto     TEXT NOT NULL,
  analisis_competencia   TEXT,
  descripcion            TEXT,
  business_case_path     VARCHAR(500),  -- archivo en S3
  status                 VARCHAR(50) DEFAULT 'BORRADOR',
  created_by_user_id     INTEGER FK → usuarios,
  approved_by_user_id    INTEGER FK → usuarios (nullable),
  solicitud_id           INTEGER FK → solicitudes (nullable),  -- link al flujo Área 4
  created_at             TIMESTAMP,
  updated_at             TIMESTAMP
);
```

### Estados de la Iniciativa

| code | Descripción |
|------|-------------|
| `BORRADOR` | Director está redactando |
| `PENDIENTE_GG` | Enviada a Gerencia General |
| `APROBADA_GG` | GG aprobó → activa flujo Área 4 |
| `RECHAZADA_GG` | GG rechazó |
| `EN_PROTOTIPADO` | Área 4 trabajando |
| `PENDIENTE_JD` | Esperando Junta Directiva |
| `APROBADA_JD` | Aprobación final → solicitud INNOVACION creada |
| `RECHAZADA_JD` | Rechazada en Junta Directiva |

---

## Fase 2 — Sistema de Notificaciones Internas (Mensajes en la App)

### Por qué es necesario
Actualmente solo hay email. Para informar a Área 4 que deben iniciar un prototipado, se
necesita algo visible dentro de la plataforma además del correo.

### Nueva tabla `notificaciones`

```sql
CREATE TABLE notificaciones (
  id               SERIAL PRIMARY KEY,
  user_id          INTEGER FK → usuarios,
  tipo             VARCHAR(50),   -- 'NUEVO_PROTOTIPADO', 'INICIATIVA_APROBADA', etc.
  titulo           VARCHAR(255),
  mensaje          TEXT,
  iniciativa_id    INTEGER FK → iniciativas (nullable),
  solicitud_id     INTEGER FK → solicitudes (nullable),
  leida            BOOLEAN DEFAULT false,
  created_at       TIMESTAMP
);
```

**En el frontend:** Un ícono de campana en el header con contador de no leídas. Al hacer
click muestra el listado con links directos a la iniciativa o solicitud correspondiente.

---

## Fase 3 — El Punto de Debate: Gerente de Tiendas

Este es el punto más crítico del diseño. Hay tres opciones:

### Opción A — Email Magic Link (Recomendada)

El sistema genera un **token único** y le envía al Gerente de Tiendas un email con dos
botones: `Aprobar` y `Rechazar`. Al hacer click en cualquiera, se procesa sin necesidad
de login.

```
Email → "Resumen ejecutivo del prototipado"
  [✓ APROBAR PROTOTIPADO]    [✗ RECHAZAR]
  (URL: /api/v1/token-approval/{token})
```

**Ventajas:** Cero fricción para él, trazabilidad completa, queda registrado quién
aprobó y cuándo.

**Desventajas:** Hay que construir el sistema de tokens en backend, y el email puede
irse a spam.

#### Nueva tabla `approval_tokens`

```sql
CREATE TABLE approval_tokens (
  id            SERIAL PRIMARY KEY,
  token         UUID UNIQUE NOT NULL,
  iniciativa_id INTEGER FK → iniciativas,
  user_name     VARCHAR(255),  -- nombre del aprobador externo
  user_email    VARCHAR(255),
  action        VARCHAR(50),   -- 'PENDIENTE', 'APROBADO', 'RECHAZADO'
  comment       TEXT,
  expires_at    TIMESTAMP,
  used_at       TIMESTAMP,
  created_at    TIMESTAMP
);
```

---

### Opción B — Luisa Ibañez documenta la aprobación

Luisa Ibañez, cuando habla con el Gerente de Tiendas (en reunión o por teléfono), registra
en la app que él aprobó, sube evidencia (email, foto de WhatsApp, acta) y da el visto bueno
por ambos.

**Ventajas:** Cero desarrollo adicional para tokens.

**Desventajas:** Menos trazabilidad directa. La aprobación del Gerente no queda
digitalizada de su parte.

---

### Opción C — Perfil de "Aprobador Ligero"

Crear un perfil mínimo para el Gerente de Tiendas: solo recibe un email con un link,
llega a una página ultra-simple (sin menú, sin dashboard) que solo muestra el resumen
del prototipado y los botones Aprobar/Rechazar. Login automático por link de único uso.

**Ventajas:** Tiene cuenta en el sistema para auditoría, experiencia muy simplificada.

**Desventajas:** Hay que crear el perfil y manejar sesión de un solo uso.

> **Recomendación:** Opción A (Email Magic Link). Es la que mejor equilibra cero
> fricción para el Gerente y trazabilidad completa para el sistema. 

VAMONOS POR LA OPCION A , LO DECIDO , ME GUSTA , ME GUSTA 

---

## Fase 4 — Aprobación Dual (Luisa + Gerente Tiendas)

Una vez el Área 4 cierra el diagnóstico técnico, antes de pasar a Junta Directiva:

```
Iniciativa en estado: EN_PROTOTIPADO
         ↓
Sistema envía:
  → Email normal a Luisa Ibañez (aprueba dentro de la app, ya tiene perfil)
  → Email Magic Link al Gerente de Tiendas

Estado: PENDIENTE_APROBACION_DUAL
  ├── luisa_approved: false
  └── gerente_tiendas_approved: false

Cuando ambos aprueban:
  → Estado cambia a PENDIENTE_JD
  → Email a Junta Directiva
```

---

## Fase 5 — Auto-creación de Solicitud en INNOVACION

Cuando Junta Directiva aprueba la iniciativa, el backend automáticamente:

1. Busca el área `INNOVACION` (id=2) y su primera etapa
2. Crea una `solicitud` nueva con los datos de la iniciativa
3. Registra el link `iniciativa.solicitud_id = nueva_solicitud.id`
4. Notifica a los aprobadores de la primera etapa de INNOVACION
5. La iniciativa pasa a estado `APROBADA_JD`

---

## Resumen de Cambios por Capa

### Backend (FastAPI + Python)

| Componente | Cambio |
|------------|--------|
| `db/models.py` | + modelos `Iniciativa`, `Notificacion`, `ApprovalToken` |
| `alembic/versions/` | Migraciones para las 3 nuevas tablas |
| `modules/iniciativas/` | `router.py` + `service.py` + `repository.py` + `schemas.py` |
| `modules/notificaciones/` | `router.py` + `service.py` + endpoint marcar leída |
| `core/email.py` | + `send_magic_link_email()` + `send_jd_approval_email()` |
| `main.py` | Registrar nuevos routers `/api/v1/iniciativas` y `/api/v1/notificaciones` |

### Frontend (Next.js)

| Componente | Cambio |
|------------|--------|
| `app/dashboard/page.tsx` | + Panel "Mis Iniciativas" para Director de Mercadeo |
| `app/iniciativas/new/` | Formulario crear iniciativa (análisis, producto, archivos) |
| `app/iniciativas/[id]/` | Detalle + acciones según etapa |
| `app/approve/[token]/` | Página pública aprobación magic link (sin login) |
| `components/NotificationBell.tsx` | Campana con contador en header |
| `components/NotificationPanel.tsx` | Panel lateral listado de notificaciones |

### Base de Datos

| Elemento | Cambio |
|----------|--------|
| Tabla `iniciativas` | Nueva |
| Tabla `notificaciones` | Nueva |
| Tabla `approval_tokens` | Nueva (si se elige Opción A) |
| Tabla `solicitudes` | + columna `iniciativa_id` (FK nullable) |

---

## Orden de Implementación Sugerido

```
Sprint 1 — Fundamentos
  [ ] Migraciones BD (3 tablas nuevas)
  [ ] CRUD básico de Iniciativas (backend)
  [ ] Pantalla crear/ver iniciativa (frontend)
  [ ] Flujo Director → GG (email + aprobación en app)

Sprint 2 — Conexión con Área 4
  [ ] Notificación interna (campana) + email a Área 4
  [ ] Link Iniciativa ↔ Solicitud Área 4
  [ ] Cierre diagnóstico activa aprobación dual

Sprint 3 — Aprobación dual + Magic Link
  [ ] Sistema de tokens (ApprovalToken)
  [ ] Email Magic Link al Gerente de Tiendas
  [ ] Página pública /approve/[token]
  [ ] Lógica "ambos aprobaron → avanza a JD"

Sprint 4 — Junta Directiva + Auto-solicitud
  [ ] Flujo JD (aprobación / rechazo)
  [ ] Auto-creación solicitud INNOVACION
  [ ] Trazabilidad completa (iniciativa → solicitud)
```

---

## Preguntas Pendientes de Confirmación

Antes de iniciar la implementación, confirmar:

1. **Gerente de Tiendas**: ¿Opción A (Magic Link), B (Luisa documenta) o C (Perfil simplificado)?
2. **Gerencia General**: ¿Ya tienen usuario en la app, o hay que crearles uno?
3. **Junta Directiva**: ¿El usuario `JuntaDirectiva@cafequindio.com.co` (rol APPROVER) es quien aprueba en el paso 6?
4. **Director de Mercadeo**: ¿Es un usuario nuevo con rol especial o uno ya existente?
5. **Notificaciones internas**: ¿Campana en el header, o banner en el dashboard?
