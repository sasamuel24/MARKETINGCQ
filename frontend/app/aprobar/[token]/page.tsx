"use client";
import React, { useEffect, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { CheckCircle, XCircle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type PageState = "loading" | "confirm" | "processing" | "success" | "error" | "already_used";

export default function TokenApprovalPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const token = params?.token as string;
  const actionParam = searchParams?.get("action") as "APROBADO" | "RECHAZADO" | null;

  const [state, setState] = useState<PageState>("loading");
  const [action, setAction] = useState<"APROBADO" | "RECHAZADO">(actionParam || "APROBADO");
  const [comment, setComment] = useState("");
  const [resultMessage, setResultMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    // Si viene acción en URL, ir directo a confirmación
    if (actionParam) {
      setAction(actionParam);
    }
    setState("confirm");
  }, [actionParam]);

  const handleSubmit = async () => {
    setState("processing");
    try {
      const url = new URL(`${API_URL}/api/v1/token-approval/${token}`);
      url.searchParams.set("action", action);
      if (comment.trim()) url.searchParams.set("comment", comment.trim());

      const res = await fetch(url.toString(), { method: "POST" });
      const data = await res.json().catch(() => ({}));

      if (res.ok) {
        setResultMessage(data.message || "Respuesta registrada");
        setState("success");
      } else if (res.status === 400 && data.detail?.includes("ya fue utilizado")) {
        setState("already_used");
      } else {
        setErrorMessage(data.detail || "Ocurrió un error inesperado");
        setState("error");
      }
    } catch {
      setErrorMessage("No se pudo conectar al servidor. Intenta de nuevo.");
      setState("error");
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#00829a]/10 to-gray-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl max-w-md w-full overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-[#00829a] to-[#00a3b4] px-8 py-6 text-center">
          <h1 className="text-white text-xl font-bold">CAFÉ QUINDÍO</h1>
          <p className="text-white/80 text-sm mt-1">Validación de Prototipado</p>
        </div>

        <div className="px-8 py-8">
          {/* Loading */}
          {state === "loading" && (
            <div className="flex flex-col items-center gap-4 py-8">
              <Loader2 className="h-10 w-10 text-[#00829a] animate-spin" />
              <p className="text-gray-500">Verificando enlace...</p>
            </div>
          )}

          {/* Confirm */}
          {state === "confirm" && (
            <div className="flex flex-col gap-5">
              <p className="text-gray-700 text-center">
                Está a punto de registrar su validación del prototipado. Por favor seleccione su decisión:
              </p>

              {/* Selector aprobación/rechazo */}
              <div className="flex gap-3">
                <button
                  onClick={() => setAction("APROBADO")}
                  className={`flex-1 flex flex-col items-center gap-2 rounded-xl border-2 p-4 transition-all ${
                    action === "APROBADO"
                      ? "border-green-500 bg-green-50"
                      : "border-gray-200 hover:border-gray-300"
                  }`}
                >
                  <CheckCircle className={`h-8 w-8 ${action === "APROBADO" ? "text-green-500" : "text-gray-300"}`} />
                  <span className={`text-sm font-semibold ${action === "APROBADO" ? "text-green-700" : "text-gray-400"}`}>
                    APROBAR
                  </span>
                </button>
                <button
                  onClick={() => setAction("RECHAZADO")}
                  className={`flex-1 flex flex-col items-center gap-2 rounded-xl border-2 p-4 transition-all ${
                    action === "RECHAZADO"
                      ? "border-red-500 bg-red-50"
                      : "border-gray-200 hover:border-gray-300"
                  }`}
                >
                  <XCircle className={`h-8 w-8 ${action === "RECHAZADO" ? "text-red-500" : "text-gray-300"}`} />
                  <span className={`text-sm font-semibold ${action === "RECHAZADO" ? "text-red-700" : "text-gray-400"}`}>
                    RECHAZAR
                  </span>
                </button>
              </div>

              {/* Comentario */}
              <div className="space-y-2">
                <Label className="text-sm font-medium">
                  Comentario {action === "RECHAZADO" && <span className="text-red-500">*</span>}
                </Label>
                <Textarea
                  placeholder={
                    action === "RECHAZADO"
                      ? "Indique el motivo del rechazo..."
                      : "Observaciones adicionales (opcional)..."
                  }
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  rows={3}
                />
              </div>

              <Button
                onClick={handleSubmit}
                disabled={action === "RECHAZADO" && !comment.trim()}
                className={`w-full py-3 text-base font-semibold ${
                  action === "APROBADO"
                    ? "bg-green-600 hover:bg-green-700 text-white"
                    : "bg-red-600 hover:bg-red-700 text-white"
                }`}
              >
                Confirmar {action === "APROBADO" ? "aprobación" : "rechazo"}
              </Button>

              <p className="text-xs text-gray-400 text-center">
                Este enlace es de uso único y válido por 72 horas.
              </p>
            </div>
          )}

          {/* Processing */}
          {state === "processing" && (
            <div className="flex flex-col items-center gap-4 py-8">
              <Loader2 className="h-10 w-10 text-[#00829a] animate-spin" />
              <p className="text-gray-500">Registrando su respuesta...</p>
            </div>
          )}

          {/* Success */}
          {state === "success" && (
            <div className="flex flex-col items-center gap-4 py-6 text-center">
              <div className={`rounded-full p-4 ${action === "APROBADO" ? "bg-green-100" : "bg-red-100"}`}>
                {action === "APROBADO"
                  ? <CheckCircle className="h-12 w-12 text-green-600" />
                  : <XCircle className="h-12 w-12 text-red-600" />}
              </div>
              <h2 className="text-xl font-bold text-gray-800">
                {action === "APROBADO" ? "¡Aprobación registrada!" : "Rechazo registrado"}
              </h2>
              <p className="text-gray-500 text-sm">{resultMessage}</p>
              <p className="text-gray-400 text-xs mt-2">
                Puede cerrar esta ventana. El equipo de Café Quindío ha sido notificado.
              </p>
            </div>
          )}

          {/* Already used */}
          {state === "already_used" && (
            <div className="flex flex-col items-center gap-4 py-6 text-center">
              <div className="bg-yellow-100 rounded-full p-4">
                <CheckCircle className="h-12 w-12 text-yellow-600" />
              </div>
              <h2 className="text-xl font-bold text-gray-800">Enlace ya utilizado</h2>
              <p className="text-gray-500 text-sm">
                Su respuesta ya fue registrada anteriormente. Puede cerrar esta ventana.
              </p>
            </div>
          )}

          {/* Error */}
          {state === "error" && (
            <div className="flex flex-col items-center gap-4 py-6 text-center">
              <div className="bg-red-100 rounded-full p-4">
                <XCircle className="h-12 w-12 text-red-600" />
              </div>
              <h2 className="text-xl font-bold text-gray-800">Ocurrió un error</h2>
              <p className="text-gray-500 text-sm">{errorMessage}</p>
              <Button variant="outline" onClick={() => setState("confirm")}>
                Intentar de nuevo
              </Button>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="bg-gray-50 border-t px-8 py-4 text-center">
          <p className="text-xs text-gray-400">
            Sistema de Gestión de Marketing &middot; <span className="text-[#00829a] font-medium">CAFÉ QUINDÍO</span>
          </p>
        </div>
      </div>
    </div>
  );
}
