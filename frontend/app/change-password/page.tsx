"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
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

      // Limpiar cookie y redirigir al dashboard
      document.cookie = "must_change_password=; path=/; max-age=0";
      router.push("/dashboard");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Ocurrió un error");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      className="flex min-h-svh w-full items-center justify-center p-6 relative"
      style={{
        backgroundImage: "url(/plameras%20beige.jpg)",
        backgroundSize: "cover",
        backgroundPosition: "center",
        backgroundRepeat: "no-repeat",
      }}
    >
      {/* Overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-[#00829a]/60 via-[#00a3b4]/50 to-[#90cde3]/40"></div>

      <div className="w-full max-w-sm relative z-10">
        <div className="flex flex-col gap-6">
          <div className="text-center mb-4">
            <h1 className="text-4xl font-bold text-white mb-2 drop-shadow-lg">
              CAFÉ QUINDÍO
            </h1>
            <p className="text-white/90 text-sm">
              Sistema de Gestión de Marketing
            </p>
          </div>

          <Card className="shadow-2xl border-0">
            <CardHeader className="space-y-1 pb-4">
              <CardTitle className="text-2xl font-bold text-primary">
                Cambio de contraseña requerido
              </CardTitle>
              <CardDescription className="text-muted-foreground">
                Por seguridad, debes establecer una nueva contraseña antes de
                continuar.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="new-password" className="text-sm font-medium">
                    Nueva contraseña
                  </Label>
                  <Input
                    id="new-password"
                    type="password"
                    required
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className="border-2 focus:border-primary transition-colors"
                  />
                </div>
                <div className="grid gap-2">
                  <Label
                    htmlFor="confirm-password"
                    className="text-sm font-medium"
                  >
                    Confirmar contraseña
                  </Label>
                  <Input
                    id="confirm-password"
                    type="password"
                    required
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="border-2 focus:border-primary transition-colors"
                  />
                </div>
                {error && (
                  <div className="bg-destructive/10 border border-destructive/30 rounded-md p-3">
                    <p className="text-sm text-destructive font-medium">
                      {error}
                    </p>
                  </div>
                )}
                <Button
                  type="submit"
                  disabled={isLoading}
                  className="w-full bg-primary hover:bg-primary/90 text-white font-semibold py-5 shadow-lg hover:shadow-xl transition-all duration-200"
                >
                  {isLoading ? "Guardando..." : "Guardar nueva contraseña"}
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
