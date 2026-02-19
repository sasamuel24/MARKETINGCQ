# Plan de Implementación: Forzar Cambio de Contraseña en Primer Login

## Contexto del Proyecto

- **Backend:** FastAPI + SQLAlchemy + Alembic (Python)
- **Frontend:** Next.js 14 (App Router) + TypeScript
- **Base de datos:** PostgreSQL
- **Autenticación:** JWT (access token + refresh token)
- **Tabla de usuarios:** `usuarios` — modelo `User` en `db/models.py`

---

## Resumen de la Estrategia

Se agrega un campo booleano `must_change_password` a la tabla `usuarios`. Cuando un administrador crea un usuario, este campo se establece en `true`. Al hacer login, el token JWT devuelto incluye ese flag. El frontend detecta el flag y redirige al usuario a una pantalla de cambio de contraseña obligatorio antes de acceder al dashboard.

---

## Paso 1 — Base de Datos: Agregar columna `must_change_password`

**Archivo:** `backend/db/models.py`

Agregar la columna al modelo `User`:

```python
must_change_password = Column(Boolean, nullable=False, server_default='true')
```

**Archivo nuevo:** `backend/alembic/versions/xxxx_add_must_change_password.py`

Crear una nueva migración de Alembic:

```bash
cd backend
alembic revision --autogenerate -m "add_must_change_password_to_usuarios"
```

Verificar que la migración generada contenga:

```python
def upgrade() -> None:
    op.add_column('usuarios',
        sa.Column('must_change_password', sa.Boolean(), nullable=False, server_default='true')
    )

def downgrade() -> None:
    op.drop_column('usuarios', 'must_change_password')
```

Aplicar la migración:

```bash
alembic upgrade head
```

---

## Paso 2 — Backend: Incluir el flag en la respuesta del login

### 2.1 Actualizar `AuthService.authenticate_user`

**Archivo:** `backend/modules/auth/service.py`

En el método `authenticate_user`, incluir `must_change_password` en el dict de retorno:

```python
return {
    "id": str(user.id),
    "email": user.email,
    "full_name": user.full_name,
    "role": user.rol.nombre if user.rol else "user",
    "rol_id": user.rol_id,
    "area_id": user.area_id,
    "must_change_password": user.must_change_password,  # <- AGREGAR
}
```

### 2.2 Actualizar `TokenResponse` schema

**Archivo:** `backend/modules/auth/schemas.py`

Agregar el campo a `TokenResponse`:

```python
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    must_change_password: bool = Field(default=False)  # <- AGREGAR
```

### 2.3 Actualizar `AuthService.create_tokens` y el router de login

**Archivo:** `backend/modules/auth/service.py`

Modificar `create_tokens` para recibir el flag:

```python
def create_tokens(self, user_id: str, must_change_password: bool = False) -> Dict[str, Any]:
    access_token = create_access_token(data={"sub": user_id})
    refresh_token = create_refresh_token(data={"sub": user_id})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "must_change_password": must_change_password,  # <- AGREGAR
    }
```

**Archivo:** `backend/modules/auth/router.py`

En el endpoint `/login`, pasar el flag al crear los tokens:

```python
user = auth_service.authenticate_user(credentials.email, credentials.password)
if not user:
    raise HTTPException(status_code=401, detail="Credenciales incorrectas")

tokens = auth_service.create_tokens(
    user["id"],
    must_change_password=user.get("must_change_password", False)  # <- AGREGAR
)
return TokenResponse(**tokens)
```

---

## Paso 3 — Backend: Endpoint para cambiar contraseña

**Archivo:** `backend/modules/auth/router.py`

Agregar nuevo endpoint `POST /auth/change-password`:

```python
from modules.auth.schemas import ChangePasswordRequest

@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    data: ChangePasswordRequest,
    user_id: Annotated[str, Depends(get_current_user_id)]
):
    """
    Cambiar contraseña del usuario autenticado.
    Marca must_change_password = False al completar.
    """
    auth_service = AuthService()
    auth_service.change_user_password(user_id, data.new_password)
    return {"message": "Contraseña actualizada correctamente"}
```

**Archivo:** `backend/modules/auth/schemas.py`

Agregar el schema del request:

```python
class ChangePasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=8, description="Nueva contraseña (mínimo 8 caracteres)")
```

**Archivo:** `backend/modules/auth/service.py`

Agregar el método `change_user_password`:

```python
def change_user_password(self, user_id: str, new_password: str) -> None:
    user = self.db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    user.password_hash = get_password_hash(new_password)
    user.must_change_password = False  # Marcar como completado
    self.db.commit()
```

---

## Paso 4 — Backend: Usuarios nuevos creados con `must_change_password = true`

**Archivo:** `backend/modules/usuarios/service.py`

En el método `create_user`, asegurarse de que el campo se establezca en `True` por defecto (ya lo hace `server_default='true'` en el modelo, pero para claridad se puede dejar explícito):

```python
# Al crear usuario, el campo must_change_password = True por defecto de la BD
# No requiere cambio adicional si el model_default está configurado correctamente
```

Si el administrador edita un usuario y quiere forzar un nuevo cambio, agregar soporte en `UserUpdate`:

```python
# backend/modules/usuarios/schemas.py
class UserUpdate(BaseModel):
    ...
    must_change_password: Optional[bool] = Field(None, description="Forzar cambio de contraseña")
```

---

## Paso 5 — Frontend: Guardar el flag tras el login

**Archivo:** `frontend/app/login/page.tsx`

En la función `handleLogin`, después de guardar los tokens, guardar también el flag:

```typescript
localStorage.setItem("access_token", data.access_token);
localStorage.setItem("refresh_token", data.refresh_token);

// Guardar flag de cambio de contraseña obligatorio
if (data.must_change_password) {
  localStorage.setItem("must_change_password", "true");
  router.push("/change-password"); // <- redirigir a pantalla de cambio
} else {
  localStorage.removeItem("must_change_password");
  router.push("/dashboard");
}
```

---

## Paso 6 — Frontend: Crear página de cambio de contraseña obligatorio

**Archivo nuevo:** `frontend/app/change-password/page.tsx`

Crear la página con un formulario que:
1. Solicite la nueva contraseña y confirmación.
2. Llame a `POST /api/v1/auth/change-password` con el token en el header.
3. Al éxito, limpie el flag de localStorage y redirija al dashboard.

```typescript
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function ChangePasswordPage() {
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (newPassword !== confirmPassword) {
      setError("Las contraseñas no coinciden");
      return;
    }
    if (newPassword.length < 8) {
      setError("La contraseña debe tener al menos 8 caracteres");
      return;
    }

    setIsLoading(true);

    try {
      const token = localStorage.getItem("access_token");
      const response = await fetch(`${API_URL}/api/v1/auth/change-password`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ new_password: newPassword }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Error al cambiar la contraseña");
      }

      // Limpiar flag y redirigir al dashboard
      localStorage.removeItem("must_change_password");
      router.push("/dashboard");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Ocurrió un error");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-svh w-full items-center justify-center p-6">
      <div className="w-full max-w-sm">
        <Card>
          <CardHeader>
            <CardTitle>Cambio de contraseña requerido</CardTitle>
            <CardDescription>
              Por seguridad, debes establecer una nueva contraseña antes de continuar.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              <div className="grid gap-2">
                <Label htmlFor="new-password">Nueva contraseña</Label>
                <Input
                  id="new-password"
                  type="password"
                  required
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="confirm-password">Confirmar contraseña</Label>
                <Input
                  id="confirm-password"
                  type="password"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                />
              </div>
              {error && (
                <p className="text-sm text-destructive">{error}</p>
              )}
              <Button type="submit" disabled={isLoading} className="w-full">
                {isLoading ? "Guardando..." : "Guardar nueva contraseña"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
```

---

## Paso 7 — Frontend: Proteger el dashboard con middleware

**Archivo:** `frontend/middleware.ts`

Actualizar el middleware para que, si existe el flag `must_change_password` en las cookies o se detecta en el token, redirigir a `/change-password`.

> **Nota:** `localStorage` no es accesible en middleware de Next.js (corre en el servidor/edge). La forma recomendada es usar una **cookie** en lugar de localStorage para el flag.

### Alternativa recomendada: usar cookie para el flag

En `login/page.tsx`, al recibir `must_change_password: true`, establecer una cookie en el cliente:

```typescript
// Usar js-cookie o document.cookie nativo
document.cookie = "must_change_password=true; path=/; SameSite=Strict";
```

Luego en `middleware.ts`:

```typescript
import { type NextRequest, NextResponse } from "next/server";

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Si ya está en change-password, login o assets, no interferir
  if (
    pathname.startsWith("/change-password") ||
    pathname.startsWith("/login") ||
    pathname.startsWith("/_next")
  ) {
    return NextResponse.next();
  }

  // Verificar si debe cambiar contraseña
  const mustChange = request.cookies.get("must_change_password")?.value;
  if (mustChange === "true") {
    return NextResponse.redirect(new URL("/change-password", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)"],
};
```

En `change-password/page.tsx`, al completar el cambio, borrar la cookie:

```typescript
document.cookie = "must_change_password=; path=/; max-age=0";
```

---

## Paso 8 — Verificación y pruebas

### Pruebas manuales

1. **Crear usuario nuevo** desde el panel de administración → verificar que `must_change_password = true` en la BD.
2. **Iniciar sesión** con ese usuario → verificar que la respuesta del login incluye `must_change_password: true`.
3. **Confirmar redirección** a `/change-password` en lugar del dashboard.
4. **Intentar navegar al dashboard** directamente → verificar que el middleware redirige a `/change-password`.
5. **Ingresar nueva contraseña** → verificar que el campo se actualiza a `false` en la BD.
6. **Iniciar sesión de nuevo** → verificar que ya redirige al dashboard directamente.
7. **Usuario existente** (sin el flag) → verificar que el login funciona sin interrupciones.

### Pruebas de validación

- Contraseña menor a 8 caracteres → debe mostrar error de validación.
- Contraseñas que no coinciden → debe mostrar error en el frontend.
- Token inválido o expirado al llamar `/change-password` → debe retornar 401.

---

## Resumen de Archivos Afectados

| Archivo | Tipo de cambio |
|---|---|
| `backend/db/models.py` | Agregar columna `must_change_password` al modelo `User` |
| `backend/alembic/versions/xxxx_add_must_change_password.py` | Nueva migración (autogenerada) |
| `backend/modules/auth/schemas.py` | Agregar `must_change_password` a `TokenResponse` y crear `ChangePasswordRequest` |
| `backend/modules/auth/service.py` | Actualizar `authenticate_user`, `create_tokens`, agregar `change_user_password` |
| `backend/modules/auth/router.py` | Pasar flag en `/login`, agregar endpoint `/change-password` |
| `backend/modules/usuarios/schemas.py` | Agregar campo `must_change_password` en `UserUpdate` (opcional) |
| `frontend/app/login/page.tsx` | Leer flag y redirigir / establecer cookie |
| `frontend/app/change-password/page.tsx` | Nueva página de cambio de contraseña obligatorio |
| `frontend/middleware.ts` | Interceptar rutas si la cookie `must_change_password` está activa |

---

## Orden de Ejecución

```
1. Modificar modelo User (backend/db/models.py)
2. Generar y aplicar migración Alembic
3. Actualizar schemas de auth
4. Actualizar AuthService (service.py)
5. Actualizar router de auth (router.py)
6. Actualizar login page (frontend)
7. Crear página change-password (frontend)
8. Actualizar middleware (frontend)
9. Probar flujo completo
```
