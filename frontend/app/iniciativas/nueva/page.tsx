"use client";
import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ArrowLeft, Save, Send, Paperclip, X } from "lucide-react";
import { ToastContainer, ToastData } from "@/components/ui/toast-simple";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function NuevaIniciativaPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    titulo: "",
    producto_propuesto: "",
    analisis_competencia: "",
    descripcion: "",
  });
  const [businessCaseFile, setBusinessCaseFile] = useState<File | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [toasts, setToasts] = useState<ToastData[]>([]);

  const showToast = (message: string, type: "success" | "error" = "success") => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);
  };

  const validate = () => {
    const e: Record<string, string> = {};
    if (!form.titulo.trim()) e.titulo = "El título es obligatorio";
    if (!form.producto_propuesto.trim()) e.producto_propuesto = "El producto propuesto es obligatorio";
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSave = async (enviarAGG = false) => {
    if (!validate()) return;
    const token = localStorage.getItem("access_token");
    if (!token) { router.push("/login"); return; }
    setSubmitting(true);
    try {
      // 1. Crear iniciativa
      const res = await fetch(`${API_URL}/api/v1/iniciativas`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      if (!res.ok) throw new Error("Error al crear iniciativa");
      const data = await res.json();

      // 2. Subir Business Case si se adjuntó
      if (businessCaseFile) {
        const formData = new FormData();
        formData.append("file", businessCaseFile);
        await fetch(`${API_URL}/api/v1/iniciativas/${data.id}/upload-business-case`, {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
          body: formData,
        });
      }

      // 3. Si se quiere enviar directo a GG
      if (enviarAGG) {
        const res2 = await fetch(`${API_URL}/api/v1/iniciativas/${data.id}/enviar-a-gg`, {
          method: "POST",
          headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
          body: JSON.stringify({}),
        });
        if (!res2.ok) throw new Error("Error al enviar a GG");
        showToast("Iniciativa creada y enviada a Prototipado");
      } else {
        showToast("Iniciativa guardada como borrador");
      }
      setTimeout(() => router.push(`/iniciativas/${data.id}`), 1200);
    } catch (err: unknown) {
      showToast(err instanceof Error ? err.message : "Error inesperado", "error");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex w-full flex-col min-h-screen">
      <ToastContainer toasts={toasts} onRemove={(id) => setToasts((p) => p.filter((t) => t.id !== id))} />

      {/* Header */}
      <div
        className="relative w-full"
        style={{ backgroundImage: "url(/plameras%20beige.jpg)", backgroundSize: "cover", backgroundPosition: "center" }}
      >
        <div className="absolute inset-0 bg-gradient-to-br from-[#00829a]/85 via-[#00a3b4]/75 to-[#90cde3]/65" />
        <div className="relative z-10 px-4 md:px-10 py-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white drop-shadow-lg">CAFÉ QUINDÍO</h1>
              <p className="text-white/90 text-sm mt-1">Nueva Iniciativa de Producto</p>
            </div>
            <Button
              className="bg-white/20 hover:bg-white/30 text-white border-white/30 backdrop-blur-sm"
              variant="outline"
              onClick={() => router.push("/dashboard")}
            >
              <ArrowLeft className="h-4 w-4 mr-2" /> Volver
            </Button>
          </div>
        </div>
      </div>

      {/* Form */}
      <div className="flex-1 bg-gradient-to-br from-gray-50 to-gray-100 p-4 md:p-10">
        <div className="max-w-2xl mx-auto">
          <Card className="shadow-lg border-0 overflow-hidden">
            <div className="bg-gradient-to-r from-[#00829a] to-[#00a3b4] px-6 py-4">
              <h2 className="text-white text-xl font-bold uppercase tracking-wide">Análisis de Mercado</h2>
              <p className="text-white/80 text-sm">Documenta el análisis y el producto propuesto</p>
            </div>
            <CardContent className="pt-6 space-y-5">
              {/* Título */}
              <div className="space-y-2">
                <Label htmlFor="titulo" className="font-medium">
                  Título de la iniciativa <span className="text-red-500">*</span>
                </Label>
                <Input
                  id="titulo"
                  placeholder="Ej: Nuevo café especial edición limitada"
                  value={form.titulo}
                  onChange={(e) => setForm((p) => ({ ...p, titulo: e.target.value }))}
                  maxLength={255}
                  className={errors.titulo ? "border-red-500" : ""}
                />
                {errors.titulo && <p className="text-sm text-red-500">{errors.titulo}</p>}
              </div>

              {/* Producto propuesto */}
              <div className="space-y-2">
                <Label htmlFor="producto" className="font-medium">
                  Producto propuesto <span className="text-red-500">*</span>
                </Label>
                <Textarea
                  id="producto"
                  placeholder="Describe el producto que se quiere crear o lanzar..."
                  value={form.producto_propuesto}
                  onChange={(e) => setForm((p) => ({ ...p, producto_propuesto: e.target.value }))}
                  rows={3}
                  className={errors.producto_propuesto ? "border-red-500" : ""}
                />
                {errors.producto_propuesto && (
                  <p className="text-sm text-red-500">{errors.producto_propuesto}</p>
                )}
              </div>

              {/* Análisis de competencia */}
              <div className="space-y-2">
                <Label htmlFor="competencia" className="font-medium">Análisis de competencia</Label>
                <Textarea
                  id="competencia"
                  placeholder="¿Qué está haciendo la competencia? ¿Qué oportunidad se identificó en el mercado?"
                  value={form.analisis_competencia}
                  onChange={(e) => setForm((p) => ({ ...p, analisis_competencia: e.target.value }))}
                  rows={4}
                />
              </div>

              {/* Business Case */}
              <div className="space-y-2">
                <Label className="font-medium">Business Case</Label>
                <div className="flex items-center gap-3">
                  <label
                    htmlFor="business-case-input"
                    className="flex-1 flex items-center gap-2 px-4 py-2 border rounded-md cursor-pointer hover:bg-gray-50 text-sm text-gray-600 transition-colors"
                  >
                    <Paperclip className="h-4 w-4 text-[#00829a] shrink-0" />
                    {businessCaseFile ? (
                      <span className="truncate font-medium text-gray-800">{businessCaseFile.name}</span>
                    ) : (
                      <span className="text-gray-400">Adjuntar archivo (PDF, DOC, DOCX, PPTX)</span>
                    )}
                  </label>
                  {businessCaseFile && (
                    <button
                      type="button"
                      onClick={() => setBusinessCaseFile(null)}
                      className="p-1 rounded-full hover:bg-red-50 text-gray-400 hover:text-red-500 transition-colors"
                      aria-label="Quitar archivo"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  )}
                  <input
                    id="business-case-input"
                    type="file"
                    accept=".pdf,.doc,.docx,.pptx"
                    className="hidden"
                    onChange={(e) => setBusinessCaseFile(e.target.files?.[0] ?? null)}
                  />
                </div>
                <p className="text-xs text-gray-400">Formatos permitidos: PDF, DOC, DOCX, PPTX</p>
              </div>

              {/* Descripción adicional */}
              <div className="space-y-2">
                <Label htmlFor="descripcion" className="font-medium">Descripción adicional</Label>
                <Textarea
                  id="descripcion"
                  placeholder="Información adicional relevante para la Gerencia General..."
                  value={form.descripcion}
                  onChange={(e) => setForm((p) => ({ ...p, descripcion: e.target.value }))}
                  rows={3}
                />
              </div>

              {/* Botones */}
              <div className="flex gap-3 pt-2">
                <Button
                  variant="outline"
                  onClick={() => handleSave(false)}
                  disabled={submitting}
                  className="flex-1"
                >
                  <Save className="h-4 w-4 mr-2" />
                  Guardar borrador
                </Button>
                <Button
                  onClick={() => handleSave(true)}
                  disabled={submitting}
                  className="flex-1 bg-[#00829a] hover:bg-[#006d82] text-white"
                >
                  <Send className="h-4 w-4 mr-2" />
                  {submitting ? "Enviando..." : "Enviar a Prototipado"}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
