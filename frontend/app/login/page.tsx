"use client";

import React from "react"

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

import { useRouter } from "next/navigation";
import { useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/api/v1/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email,
          password,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Error al iniciar sesión");
      }

      const data = await response.json();
      
      // Guardar tokens en localStorage
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("refresh_token", data.refresh_token);
      
      // Verificar si debe cambiar contraseña
      if (data.must_change_password) {
        document.cookie = "must_change_password=true; path=/; SameSite=Strict";
        router.push("/change-password");
      } else {
        document.cookie = "must_change_password=; path=/; max-age=0";
        router.push("/dashboard");
      }
    } catch (error: unknown) {
      setError(error instanceof Error ? error.message : "Ocurrió un error");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div 
      className="flex min-h-svh w-full items-center justify-center p-6 md:p-10 relative"
      style={{
        backgroundImage: 'url(/plameras%20beige.jpg)',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat'
      }}
    >
      {/* Overlay para mejorar legibilidad */}
      <div className="absolute inset-0 bg-gradient-to-br from-[#00829a]/60 via-[#00a3b4]/50 to-[#90cde3]/40"></div>
      
      <div className="w-full max-w-sm relative z-10">
        <div className="flex flex-col gap-6">
          {/* Logo o título de la marca */}
          <div className="text-center mb-4">
            <h1 className="text-4xl font-bold text-white mb-2 drop-shadow-lg">CAFÉ QUINDÍO</h1>
            <p className="text-white/90 text-sm">Sistema de Gestión de Marketing</p>
          </div>
          
          <Card className="shadow-2xl border-0">
            <CardHeader className="space-y-1 pb-4">
              <CardTitle className="text-2xl font-bold text-primary">Iniciar sesión</CardTitle>
              <CardDescription className="text-muted-foreground">
                Ingresa tu correo y contraseña para acceder
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleLogin}>
                <div className="flex flex-col gap-6">
                  <div className="grid gap-2">
                    <Label htmlFor="email" className="text-sm font-medium">
                      Correo electrónico
                    </Label>
                    <Input
                      id="email"
                      type="email"
                      placeholder="correo@ejemplo.com"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="border-2 focus:border-primary transition-colors"
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="password" className="text-sm font-medium">
                      Contraseña
                    </Label>
                    <Input
                      id="password"
                      type="password"
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="border-2 focus:border-primary transition-colors"
                    />
                  </div>
                  {error && (
                    <div className="bg-destructive/10 border border-destructive/30 rounded-md p-3">
                      <p className="text-sm text-destructive font-medium">{error}</p>
                    </div>
                  )}
                  <Button 
                    type="submit" 
                    className="w-full bg-primary hover:bg-primary/90 text-white font-semibold py-5 shadow-lg hover:shadow-xl transition-all duration-200" 
                    disabled={isLoading}
                  >
                    {isLoading ? "Iniciando sesión..." : "Iniciar sesión"}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
          
          {/* Footer opcional */}
          <p className="text-center text-white/80 text-xs">
            © 2026 Sistema de Gestión de Marketing Café Quindío. Todos los derechos reservados.
          </p>
        </div>
      </div>
    </div>
  );
}
