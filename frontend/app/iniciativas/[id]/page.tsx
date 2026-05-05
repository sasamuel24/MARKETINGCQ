"use client";
import React, { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ArrowLeft, Send, CheckCircle, XCircle, Link2, PlayCircle, ThumbsUp, FileText, Upload, Download, Copy, ExternalLink, X as XIcon } from "lucide-react";
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { ToastContainer, ToastData } from "@/components/ui/toast-simple";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface IniciativaDetail {
  id: number;
  titulo: string;
  producto_propuesto: string;
  analisis_competencia?: string;
  descripcion?: string;
  business_case_path?: string;
  status: string;
  luisa_approved: boolean;
  gerente_tiendas_approved: boolean;
  solicitud_id?: number;
  solicitud_innovacion_id?: number;
  created_at: string;
  updated_at: string;
  created_by?: { id: number; full_name: string; email: string };
  approved_by_gg?: { id: number; full_name: string };
}

interface CurrentUser {
  id: string | number;
  rol_id: number;
  area_id?: number;
  full_name: string;
}

const STATUS_CONFIG: Record<string, { label: string; color: string; description: string }> = {
  BORRADOR:                  { label: "Borrador",              color: "bg-gray-100 text-gray-700 border-gray-200",    description: "En redacción" },
  PENDIENTE_GG:              { label: "Pendiente GG",          color: "bg-yellow-100 text-yellow-700 border-yellow-200", description: "Esperando aprobación de Gerencia General" },
  APROBADA_GG:               { label: "Aprobada GG",           color: "bg-blue-100 text-blue-700 border-blue-200",    description: "GG aprobó. Área 4 debe iniciar prototipado" },
  RECHAZADA_GG:              { label: "Rechazada",             color: "bg-red-100 text-red-700 border-red-200",       description: "Gerencia General rechazó la iniciativa" },
  EN_PROTOTIPADO:            { label: "En Prototipado",        color: "bg-purple-100 text-purple-700 border-purple-200", description: "Área 4 está desarrollando el prototipo" },
  PENDIENTE_APROBACION_DUAL: { label: "Aprobación Dual",       color: "bg-orange-100 text-orange-700 border-orange-200", description: "Esperando aprobación de Luisa y Gerente de Tiendas" },
  PENDIENTE_JD:              { label: "Pendiente JD",          color: "bg-indigo-100 text-indigo-700 border-indigo-200", description: "Esperando aprobación de Junta Directiva" },
  APROBADA_JD:               { label: "Aprobada",              color: "bg-green-100 text-green-700 border-green-200", description: "Aprobada por Junta Directiva. Solicitud de Innovación creada" },
  RECHAZADA_JD:              { label: "Rechazada JD",          color: "bg-red-100 text-red-700 border-red-200",       description: "Junta Directiva rechazó la iniciativa" },
};

const LUISA_USER_ID = 8;

export default function IniciativaDetailPage() {
  const router = useRouter();
  const params = useParams();
  const iniciativaId = params?.id as string;

  const [user, setUser] = useState<CurrentUser | null>(null);
  const [iniciativa, setIniciativa] = useState<IniciativaDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [toasts, setToasts] = useState<ToastData[]>([]);

  // Business Case upload
  const [bcFile, setBcFile] = useState<File | null>(null);
  const [uploadingBC, setUploadingBC] = useState(false);

  // Dialogs
  const [showRechazarJD, setShowRechazarJD] = useState(false);
  const [showVincular, setShowVincular] = useState(false);
  const [showMagicLink, setShowMagicLink] = useState(false);
  const [magicLink, setMagicLink] = useState<{ approve_url: string; reject_url: string; expires_at: string; gerente_email: string } | null>(null);
  const [loadingMagicLink, setLoadingMagicLink] = useState(false);
  const [comment, setComment] = useState("");
  const [solicitudIdInput, setSolicitudIdInput] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // Inline form para crear solicitud desde vincular
  const [showCrearForm, setShowCrearForm] = useState(false);
  const [crearForm, setCrearForm] = useState({ titulo: "", descripcion: "", categoria: "" as "" | "reposteria" | "bebidas" });
  const [crearFiles, setCrearFiles] = useState<File[]>([]);
  const [crearErrors, setCrearErrors] = useState<Record<string, string>>({});
  const [crearSubmitting, setCrearSubmitting] = useState(false);
  const [etapas, setEtapas] = useState<{ id: number; order: number; area_id: number }[]>([]);
  const [estados, setEstados] = useState<{ id: number; code: string; order: number }[]>([]);

  // Solicitud de Innovación vinculada
  const [solicitudInno, setSolicitudInno] = useState<{
    id: number; stage: { id: number; code: string; label: string };
    state: { code: string; label: string }; files: { id: number }[];
  } | null>(null);
  const [innoApprovers, setInnoApprovers] = useState<number[]>([]);
  const [innoAlreadyApproved, setInnoAlreadyApproved] = useState(false);
  const [showAprobarInno, setShowAprobarInno] = useState(false);
  const [showAjustesInno, setShowAjustesInno] = useState(false);
  const [showRechazarInno, setShowRechazarInno] = useState(false);
  const [innoComment, setInnoComment] = useState("");
  const [submittingInno, setSubmittingInno] = useState(false);

  const showToast = (message: string, type: "success" | "error" = "success") => {
    const id = Date.now();
    setToasts((prev) => [...prev, { id, message, type }]);
  };

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) { router.push("/login"); return; }
    // Cargar usuario e iniciativa en paralelo
    Promise.all([
      fetch(`${API_URL}/api/v1/auth/me`, { headers: { Authorization: `Bearer ${token}` } }).then((r) => r.json()),
      fetch(`${API_URL}/api/v1/iniciativas/${iniciativaId}`, { headers: { Authorization: `Bearer ${token}` } }).then((r) => {
        if (!r.ok) throw new Error("No encontrada");
        return r.json();
      }),
      fetch(`${API_URL}/api/v1/etapas?page_size=100`, { headers: { Authorization: `Bearer ${token}` } }).then((r) => r.json()),
      fetch(`${API_URL}/api/v1/estados`, { headers: { Authorization: `Bearer ${token}` } }).then((r) => r.json()),
    ])
      .then(([userData, iniData, etapasData, estadosData]) => {
        setUser(userData);
        setIniciativa(iniData);
        setEtapas(etapasData?.etapas || etapasData?.items || (Array.isArray(etapasData) ? etapasData : []));
        setEstados(estadosData?.estados || estadosData?.items || (Array.isArray(estadosData) ? estadosData : []));
        // Si hay solicitud de innovación vinculada, cargar sus datos + aprobadores
        if (iniData.solicitud_innovacion_id) {
          fetchSolicitudInnovacion(token, iniData.solicitud_innovacion_id, userData);
        }
      })
      .catch(() => router.push("/iniciativas"))
      .finally(() => setLoading(false));
  }, [iniciativaId, router]);

  const callApi = async (endpoint: string, body?: object) => {
    const token = localStorage.getItem("access_token");
    const res = await fetch(`${API_URL}/api/v1/iniciativas/${iniciativaId}/${endpoint}`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      body: JSON.stringify(body || {}),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Error en la operación");
    }
    return res.json();
  };

  const uploadBusinessCase = async () => {
    if (!bcFile) return;
    const token = localStorage.getItem("access_token");
    setUploadingBC(true);
    try {
      const formData = new FormData();
      formData.append("file", bcFile);
      const res = await fetch(`${API_URL}/api/v1/iniciativas/${iniciativaId}/upload-business-case`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });
      if (!res.ok) throw new Error("Error al subir el Business Case");
      const updated: IniciativaDetail = await res.json();
      setIniciativa(updated);
      setBcFile(null);
      showToast("Business Case subido exitosamente");
    } catch (err: unknown) {
      showToast(err instanceof Error ? err.message : "Error al subir", "error");
    } finally {
      setUploadingBC(false);
    }
  };

  const handleAction = async (action: () => Promise<IniciativaDetail>) => {
    setSubmitting(true);
    try {
      const updated = await action();
      setIniciativa(updated);
      setComment("");
      setShowRechazarJD(false);
      setShowVincular(false);
      showToast("Acción realizada exitosamente");
    } catch (err: unknown) {
      showToast(err instanceof Error ? err.message : "Error inesperado", "error");
    } finally {
      setSubmitting(false);
    }
  };

  const fetchSolicitudInnovacion = async (token: string, solId: number, currentUser: CurrentUser) => {
    try {
      const [solRes, evRes] = await Promise.all([
        fetch(`${API_URL}/api/v1/solicitudes/${solId}`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API_URL}/api/v1/solicitudes/${solId}/eventos`, { headers: { Authorization: `Bearer ${token}` } }),
      ]);
      if (!solRes.ok) return;
      const sol = await solRes.json();
      setSolicitudInno(sol);

      // Cargar aprobadores de la etapa actual de la solicitud
      const apRes = await fetch(`${API_URL}/api/v1/etapa-aprobadores/etapa/${sol.stage.id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (apRes.ok) {
        const apData: Array<{ user: { id: number } }> = await apRes.json();
        setInnoApprovers(apData.map((a) => a.user.id));
      }

      // Verificar si el usuario ya aprobó en la etapa actual
      if (evRes.ok) {
        const eventos = await evRes.json();
        const yaAprobó = eventos.some(
          (ev: { action: string; stage: { id: number }; actor: { id: number } }) =>
            ev.action === "APPROVED" &&
            ev.stage?.id === sol.stage.id &&
            ev.actor?.id === Number(currentUser.id)
        );
        setInnoAlreadyApproved(yaAprobó);
      }
    } catch {}
  };

  const handleInnoAction = async (endpoint: string, body: object, successMsg: string) => {
    setSubmittingInno(true);
    const token = localStorage.getItem("access_token");
    try {
      const res = await fetch(`${API_URL}/api/v1/solicitudes/${solicitudInno?.id}/${endpoint}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || "Error");
      const updatedSol = await res.json();
      setSolicitudInno(updatedSol);
      setInnoComment("");
      setShowAprobarInno(false);
      setShowAjustesInno(false);
      setShowRechazarInno(false);
      // Recargar aprobadores de la nueva etapa
      if (token && updatedSol.stage?.id) {
        const ap = await fetch(`${API_URL}/api/v1/etapa-aprobadores/etapa/${updatedSol.stage.id}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (ap.ok) {
          const apData: Array<{ user: { id: number } }> = await ap.json();
          setInnoApprovers(apData.map((a) => a.user.id));
          setInnoAlreadyApproved(false);
        }
      }
      showToast(successMsg);
    } catch (err: unknown) {
      showToast(err instanceof Error ? err.message : "Error", "error");
    } finally {
      setSubmittingInno(false);
    }
  };

  if (loading) return <div className="p-8 text-center">Cargando...</div>;
  if (!iniciativa || !user) return null;

  const cfg = STATUS_CONFIG[iniciativa.status] || { label: iniciativa.status, color: "bg-gray-100 text-gray-600", description: "" };
  const isCreator = user.rol_id === 2;
  const isApprover = user.rol_id === 3;
  const isOwner = Number(iniciativa.created_by?.id) === Number(user.id);
  const isLuisa = Number(user.id) === LUISA_USER_ID;
  const canAprobarJD = Number(user.id) === 15; // Solo Directora de Mercadeo (id=15) aprueba paso a Innovación
  const isDirectorRole = user.rol_id === 4;
  const isArea4 = user.area_id === 4 && !isDirectorRole;

  // Pasos del flujo para visualización (sin GG — va directo a Prototipado)
  const steps = [
    { key: "BORRADOR",                  label: "Borrador" },
    { key: "APROBADA_GG",               label: "Prototipado" },
    { key: "PENDIENTE_APROBACION_DUAL", label: "Aprobación Dual" },
    { key: "PENDIENTE_JD",              label: "Junta Directiva" },
    { key: "APROBADA_JD",               label: "Innovación" },
  ];
  const statusOrder = ["BORRADOR","APROBADA_GG","EN_PROTOTIPADO","PENDIENTE_APROBACION_DUAL","PENDIENTE_JD","APROBADA_JD","RECHAZADA_JD"];
  const currentIdx = statusOrder.indexOf(iniciativa.status);

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
              <p className="text-white/90 text-sm mt-1">Detalle de Iniciativa #{iniciativaId}</p>
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

      <div className="flex-1 bg-gradient-to-br from-gray-50 to-gray-100 p-4 md:p-10">
        <div className="max-w-3xl mx-auto flex flex-col gap-6">

          {/* Stepper del flujo */}
          <div className="bg-white rounded-xl shadow-sm border p-5">
            <div className="flex items-center justify-between gap-1 overflow-x-auto">
              {steps.map((step, i) => {
                const isActive = iniciativa.status === step.key ||
                  (step.key === "APROBADA_GG" && iniciativa.status === "EN_PROTOTIPADO");
                const isPast = statusOrder.indexOf(step.key) < currentIdx &&
                  !["RECHAZADA_GG","RECHAZADA_JD"].includes(iniciativa.status);
                return (
                  <React.Fragment key={step.key}>
                    <div className="flex flex-col items-center min-w-[60px]">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold border-2 ${
                        isActive ? "border-[#00829a] bg-[#00829a] text-white" :
                        isPast ? "border-[#96c121] bg-[#96c121] text-white" :
                        "border-gray-200 bg-gray-100 text-gray-400"
                      }`}>
                        {isPast ? "✓" : i + 1}
                      </div>
                      <p className={`text-[10px] mt-1 text-center leading-tight ${isActive ? "text-[#00829a] font-semibold" : "text-gray-400"}`}>
                        {step.label}
                      </p>
                    </div>
                    {i < steps.length - 1 && (
                      <div className={`flex-1 h-0.5 mb-4 ${isPast ? "bg-[#96c121]" : "bg-gray-200"}`} />
                    )}
                  </React.Fragment>
                );
              })}
            </div>
          </div>

          {/* Info card */}
          <Card className="shadow-lg border-0 overflow-hidden">
            <div className="bg-gradient-to-r from-[#00829a] to-[#00a3b4] px-6 py-4 flex items-center justify-between">
              <h2 className="text-white text-xl font-bold">{iniciativa.titulo}</h2>
              <span className={`inline-flex items-center rounded-md border px-2.5 py-1 text-xs font-semibold ${cfg.color}`}>
                {cfg.label}
              </span>
            </div>
            <CardContent className="pt-6 space-y-5">
              <div className="bg-blue-50 border border-blue-100 rounded-lg p-3 text-sm text-blue-700">
                {cfg.description}
              </div>

              <div className="grid md:grid-cols-2 gap-5">
                <div>
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1">Producto Propuesto</p>
                  <p className="text-sm text-gray-700">{iniciativa.producto_propuesto}</p>
                </div>
                <div>
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1">Creado por</p>
                  <p className="text-sm text-gray-700">{iniciativa.created_by?.full_name || "—"}</p>
                </div>
                {iniciativa.analisis_competencia && (
                  <div className="md:col-span-2">
                    <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1">Análisis de Competencia</p>
                    <p className="text-sm text-gray-700 whitespace-pre-line">{iniciativa.analisis_competencia}</p>
                  </div>
                )}
                {iniciativa.descripcion && (
                  <div className="md:col-span-2">
                    <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-1">Descripción</p>
                    <p className="text-sm text-gray-700 whitespace-pre-line">{iniciativa.descripcion}</p>
                  </div>
                )}
              </div>

              {/* Aprobación dual: indicadores */}
              {["PENDIENTE_APROBACION_DUAL", "PENDIENTE_JD", "APROBADA_JD"].includes(iniciativa.status) && (
                <div className="border rounded-lg p-4 bg-orange-50 border-orange-100">
                  <p className="text-sm font-semibold text-orange-800 mb-3">Aprobaciones del Prototipado</p>
                  <div className="flex gap-6">
                    <div className="flex items-center gap-2">
                      {iniciativa.luisa_approved
                        ? <CheckCircle className="h-5 w-5 text-green-500" />
                        : <XCircle className="h-5 w-5 text-gray-300" />}
                      <span className="text-sm">Luisa Ibañez</span>
                    </div>
                    <div className="flex items-center gap-2">
                      {iniciativa.gerente_tiendas_approved
                        ? <CheckCircle className="h-5 w-5 text-green-500" />
                        : <XCircle className="h-5 w-5 text-gray-300" />}
                      <span className="text-sm">Gerente de Tiendas</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Business Case */}
              <div className="border rounded-lg p-4 bg-gray-50">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <FileText className="h-5 w-5 text-[#00829a]" />
                    <p className="text-sm font-semibold text-gray-800">Business Case</p>
                    {!iniciativa.business_case_path && (
                      <span className="text-[10px] bg-red-100 text-red-600 border border-red-200 rounded px-1.5 py-0.5 font-medium">
                        Requerido
                      </span>
                    )}
                  </div>
                  {iniciativa.business_case_path && (
                    <a
                      href={`${API_URL}/api/v1/iniciativas/${iniciativaId}/download-business-case`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1 text-xs text-[#00829a] hover:text-[#006d82] font-medium"
                    >
                      <Download className="h-3.5 w-3.5" />
                      Descargar
                    </a>
                  )}
                </div>

                {iniciativa.business_case_path ? (
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <CheckCircle className="h-4 w-4 text-green-500 flex-shrink-0" />
                    <span className="truncate">{iniciativa.business_case_path.split("/").pop()}</span>
                  </div>
                ) : (
                  <p className="text-xs text-gray-500 mb-3">
                    El Business Case es obligatorio antes de enviar a Prototipado.
                  </p>
                )}

                {/* Upload solo si es la directora y no está en estado terminal */}
                {isOwner && !["APROBADA_JD", "RECHAZADA_JD"].includes(iniciativa.status) && (
                  <div className="mt-3 flex items-center gap-2">
                    <label className="flex-1 cursor-pointer">
                      <div className={`flex items-center gap-2 border-2 border-dashed rounded-lg px-3 py-2 text-sm transition-colors ${
                        bcFile ? "border-[#00829a] bg-[#00829a]/5" : "border-gray-200 hover:border-gray-300"
                      }`}>
                        <Upload className="h-4 w-4 text-gray-400 flex-shrink-0" />
                        <span className="truncate text-gray-500">
                          {bcFile ? bcFile.name : "Subir Business Case (PDF)"}
                        </span>
                      </div>
                      <input
                        type="file"
                        accept=".pdf,.doc,.docx,.pptx"
                        className="hidden"
                        onChange={(e) => setBcFile(e.target.files?.[0] || null)}
                      />
                    </label>
                    {bcFile && (
                      <Button
                        size="sm"
                        className="bg-[#00829a] hover:bg-[#006d82] text-white flex-shrink-0"
                        onClick={uploadBusinessCase}
                        disabled={uploadingBC}
                      >
                        {uploadingBC ? "Subiendo..." : "Subir"}
                      </Button>
                    )}
                  </div>
                )}
              </div>

              {/* Links a solicitudes */}
              {iniciativa.solicitud_id && (
                <div className="flex items-center gap-2 text-sm text-[#00829a]">
                  <Link2 className="h-4 w-4" />
                  <button onClick={() => router.push(`/solicitudes/${iniciativa.solicitud_id}`)}
                    className="hover:underline font-medium">
                    Ver solicitud de prototipado #{iniciativa.solicitud_id}
                  </button>
                </div>
              )}
              {iniciativa.solicitud_innovacion_id && (
                <div className="mt-2 flex flex-col gap-3">
                  <div className="flex items-center gap-2 text-sm text-[#96c121]">
                    <Link2 className="h-4 w-4" />
                    <button onClick={() => router.push(`/solicitudes/${iniciativa.solicitud_innovacion_id}`)}
                      className="hover:underline font-medium">
                      Ver solicitud de Innovación #{iniciativa.solicitud_innovacion_id}
                    </button>
                  </div>

                  {/* Panel de acción para aprobadores de la solicitud de innovación */}
                  {solicitudInno && (() => {
                    const isCurrentApprover = innoApprovers.includes(Number(user.id));
                    const isTerminal = ["APROBADO_FINAL","RECHAZADO"].includes(solicitudInno.state.code);
                    const isAjustes = solicitudInno.state.code === "AJUSTES_SOLICITADOS";
                    if (!isCurrentApprover || isTerminal || innoAlreadyApproved) return null;
                    return (
                      <div className="rounded-xl border border-[#00829a]/30 bg-[#00829a]/5 p-4">
                        <p className="text-sm font-semibold text-[#00829a] mb-1">
                          Solicitud de Innovación — Etapa: {solicitudInno.stage.label}
                        </p>
                        <p className="text-xs text-gray-500 mb-3">
                          Esta solicitud requiere tu revisión. Puedes aprobarla, pedir ajustes o rechazarla.
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {!isAjustes && (
                            <Button
                              size="sm"
                              className="bg-[#00829a] hover:bg-[#006d82] text-white"
                              onClick={() => setShowAprobarInno(true)}
                              disabled={submittingInno}
                            >
                              <CheckCircle className="h-4 w-4 mr-1" /> Dar visto bueno
                            </Button>
                          )}
                          <Button
                            size="sm"
                            variant="outline"
                            className="border-amber-400 text-amber-700 hover:bg-amber-50"
                            onClick={() => setShowAjustesInno(true)}
                            disabled={submittingInno}
                          >
                            Solicitar ajustes
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            className="border-red-400 text-red-600 hover:bg-red-50"
                            onClick={() => setShowRechazarInno(true)}
                            disabled={submittingInno}
                          >
                            <XCircle className="h-4 w-4 mr-1" /> Rechazar
                          </Button>
                        </div>
                      </div>
                    );
                  })()}

                  {/* Ya aprobaste en esta etapa */}
                  {solicitudInno && innoApprovers.includes(Number(user.id)) && innoAlreadyApproved && (
                    <div className="rounded-xl border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
                      Tu aprobación fue registrada en la etapa <strong>{solicitudInno.stage.label}</strong>. Esperando otros aprobadores si aplica.
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Acciones */}
          <div className="flex flex-wrap gap-3">
            {/* Director: enviar directamente a Prototipado (Área 4) */}
            {isOwner && iniciativa.status === "BORRADOR" && (
              <Button
                className="bg-[#00829a] hover:bg-[#006d82] text-white disabled:opacity-50"
                onClick={() => handleAction(() => callApi("enviar-a-gg"))}
                disabled={submitting || !iniciativa.business_case_path}
                title={!iniciativa.business_case_path ? "Debes subir el Business Case primero" : undefined}
              >
                <Send className="h-4 w-4 mr-2" /> Enviar a Prototipado
              </Button>
            )}

            {/* Área 4: vincular prototipado */}
            {isArea4 && iniciativa.status === "APROBADA_GG" && !iniciativa.solicitud_id && (
              <Button className="bg-purple-600 hover:bg-purple-700 text-white" onClick={() => setShowVincular(true)}>
                <Link2 className="h-4 w-4 mr-2" /> Vincular solicitud de prototipado
              </Button>
            )}


            {/* Owner: obtener magic link del Gerente de Tiendas */}
            {isOwner && iniciativa.status === "PENDIENTE_APROBACION_DUAL" && !iniciativa.gerente_tiendas_approved && (
              <Button
                variant="outline"
                className="border-orange-300 text-orange-700 hover:bg-orange-50"
                disabled={loadingMagicLink}
                onClick={async () => {
                  setLoadingMagicLink(true);
                  try {
                    const token = localStorage.getItem("access_token");
                    const res = await fetch(`${API_URL}/api/v1/iniciativas/${iniciativaId}/magic-link`, {
                      headers: { Authorization: `Bearer ${token}` },
                    });
                    if (!res.ok) throw new Error((await res.json()).detail || "Error");
                    const data = await res.json();
                    setMagicLink(data);
                    setShowMagicLink(true);
                  } catch (err: unknown) {
                    showToast(err instanceof Error ? err.message : "Error al obtener enlace", "error");
                  } finally {
                    setLoadingMagicLink(false);
                  }
                }}
              >
                <Link2 className="h-4 w-4 mr-2" />
                {loadingMagicLink ? "Obteniendo..." : "Ver enlace del Gerente de Tiendas"}
              </Button>
            )}

            {/* Luisa: aprobar dual */}
            {isLuisa && iniciativa.status === "PENDIENTE_APROBACION_DUAL" && !iniciativa.luisa_approved && (
              <Button
                className="bg-green-600 hover:bg-green-700 text-white"
                onClick={() => handleAction(() => callApi("aprobar-dual", { comment: "" }))}
                disabled={submitting}
              >
                <ThumbsUp className="h-4 w-4 mr-2" /> Aprobar prototipado
              </Button>
            )}

            {/* Directora: aprobar paso a Innovación (solo user id=15) */}
            {canAprobarJD && iniciativa.status === "PENDIENTE_JD" && (
              <>
                <Button
                  className="bg-green-600 hover:bg-green-700 text-white"
                  onClick={() => handleAction(() => callApi("aprobar-jd", { comment: "" }))}
                  disabled={submitting}
                >
                  <CheckCircle className="h-4 w-4 mr-2" /> Aprobar — Generar solicitud Innovación
                </Button>
                <Button variant="destructive" onClick={() => setShowRechazarJD(true)}>
                  <XCircle className="h-4 w-4 mr-2" /> Rechazar
                </Button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Dialog: Rechazar JD */}
      <Dialog open={showRechazarJD} onOpenChange={setShowRechazarJD}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Rechazar (Junta Directiva)</DialogTitle>
            <DialogDescription>Indica el motivo del rechazo de la Junta Directiva.</DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <Label>Motivo <span className="text-red-500">*</span></Label>
            <Textarea value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Motivo..." rows={3} />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRechazarJD(false)}>Cancelar</Button>
            <Button
              variant="destructive"
              disabled={submitting || !comment.trim()}
              onClick={() => handleAction(() => callApi("rechazar-jd", { comment }))}
            >
              {submitting ? "Rechazando..." : "Confirmar rechazo"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Dialog: Magic Link del Gerente de Tiendas */}
      <Dialog open={showMagicLink} onOpenChange={setShowMagicLink}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Enlace de aprobación — Gerente de Tiendas</DialogTitle>
            <DialogDescription>
              El correo falló. Comparte estos enlaces manualmente con {magicLink?.gerente_email}.
            </DialogDescription>
          </DialogHeader>
          {magicLink && (
            <div className="space-y-4">
              <div className="text-xs text-gray-500">
                Vence: {new Date(magicLink.expires_at).toLocaleString("es-CO")}
              </div>
              <div className="space-y-2">
                <p className="text-xs font-semibold text-gray-600 uppercase tracking-wide">Enlace para APROBAR</p>
                <div className="flex items-center gap-2">
                  <code className="flex-1 text-xs bg-green-50 border border-green-200 rounded px-3 py-2 text-green-800 truncate">
                    {magicLink.approve_url}
                  </code>
                  <Button size="sm" variant="outline" className="flex-shrink-0"
                    onClick={() => { navigator.clipboard.writeText(magicLink.approve_url); showToast("Enlace de aprobación copiado"); }}>
                    <Copy className="h-3.5 w-3.5" />
                  </Button>
                  <a href={magicLink.approve_url} target="_blank" rel="noopener noreferrer">
                    <Button size="sm" variant="outline" className="flex-shrink-0"><ExternalLink className="h-3.5 w-3.5" /></Button>
                  </a>
                </div>
              </div>
              <div className="space-y-2">
                <p className="text-xs font-semibold text-gray-600 uppercase tracking-wide">Enlace para RECHAZAR</p>
                <div className="flex items-center gap-2">
                  <code className="flex-1 text-xs bg-red-50 border border-red-200 rounded px-3 py-2 text-red-800 truncate">
                    {magicLink.reject_url}
                  </code>
                  <Button size="sm" variant="outline" className="flex-shrink-0"
                    onClick={() => { navigator.clipboard.writeText(magicLink.reject_url); showToast("Enlace de rechazo copiado"); }}>
                    <Copy className="h-3.5 w-3.5" />
                  </Button>
                </div>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowMagicLink(false)}>Cerrar</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Dialog: Vincular solicitud prototipado */}
      <Dialog open={showVincular} onOpenChange={(open) => { setShowVincular(open); if (!open) { setShowCrearForm(false); setCrearForm({ titulo: "", descripcion: "", categoria: "" }); setCrearFiles([]); setCrearErrors({}); } }}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Vincular solicitud de prototipado</DialogTitle>
            {!showCrearForm && (
              <DialogDescription>Crea una nueva solicitud o vincula una existente por ID.</DialogDescription>
            )}
          </DialogHeader>

          {!showCrearForm ? (
            <>
              {/* Opción principal: crear nueva */}
              <div className="rounded-lg border-2 border-purple-200 bg-purple-50 p-4">
                <p className="text-sm font-semibold text-purple-800 mb-1">Crear nueva solicitud</p>
                <p className="text-xs text-purple-600 mb-3">Se creará y vinculará automáticamente a esta iniciativa.</p>
                <Button
                  className="w-full bg-purple-600 hover:bg-purple-700 text-white"
                  onClick={() => setShowCrearForm(true)}
                >
                  <Link2 className="h-4 w-4 mr-2" /> Crear y vincular solicitud
                </Button>
              </div>

              <div className="flex items-center gap-2">
                <div className="flex-1 h-px bg-gray-200" />
                <span className="text-xs text-gray-400">o vincular una existente</span>
                <div className="flex-1 h-px bg-gray-200" />
              </div>

              <div className="space-y-2">
                <Label>ID de solicitud existente</Label>
                <Input type="number" placeholder="Ej: 42" value={solicitudIdInput} onChange={(e) => setSolicitudIdInput(e.target.value)} />
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowVincular(false)}>Cancelar</Button>
                <Button
                  className="bg-purple-600 hover:bg-purple-700 text-white"
                  disabled={submitting || !solicitudIdInput}
                  onClick={() => {
                    const token = localStorage.getItem("access_token");
                    handleAction(() =>
                      fetch(`${API_URL}/api/v1/iniciativas/${iniciativaId}/vincular-prototipado?solicitud_id=${solicitudIdInput}`, {
                        method: "POST", headers: { Authorization: `Bearer ${token}` },
                      }).then((r) => r.json())
                    );
                  }}
                >
                  {submitting ? "Vinculando..." : "Vincular por ID"}
                </Button>
              </DialogFooter>
            </>
          ) : (
            /* ── Formulario inline ── */
            <div className="space-y-4">
              <div className="space-y-1">
                <Label>Nombre de la solicitud <span className="text-red-500">*</span></Label>
                <Input
                  placeholder="Ej: Prototipo bebida especial"
                  maxLength={80}
                  value={crearForm.titulo}
                  onChange={(e) => setCrearForm((p) => ({ ...p, titulo: e.target.value }))}
                  className={crearErrors.titulo ? "border-red-500" : ""}
                />
                {crearErrors.titulo && <p className="text-xs text-red-500">{crearErrors.titulo}</p>}
                <p className="text-xs text-muted-foreground">{crearForm.titulo.length}/80</p>
              </div>

              <div className="space-y-1">
                <Label>Categoría <span className="text-red-500">*</span></Label>
                <select
                  value={crearForm.categoria}
                  onChange={(e) => setCrearForm((p) => ({ ...p, categoria: e.target.value as "" | "reposteria" | "bebidas" }))}
                  className={`h-10 w-full rounded-md border bg-background px-3 py-2 text-sm ${crearErrors.categoria ? "border-red-500" : "border-input"}`}
                >
                  <option value="">Seleccionar categoría</option>
                  <option value="reposteria">Repostería</option>
                  <option value="bebidas">Bebidas</option>
                </select>
                {crearErrors.categoria && <p className="text-xs text-red-500">{crearErrors.categoria}</p>}
              </div>

              <div className="space-y-1">
                <Label>Descripción</Label>
                <textarea
                  placeholder="Detalles adicionales..."
                  rows={3}
                  maxLength={900}
                  value={crearForm.descripcion}
                  onChange={(e) => setCrearForm((p) => ({ ...p, descripcion: e.target.value }))}
                  className="w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/30"
                />
                <p className="text-xs text-muted-foreground">{crearForm.descripcion.length}/900</p>
              </div>

              <div className="space-y-1">
                <Label>Archivos adjuntos <span className="text-red-500">*</span></Label>
                <label className="block cursor-pointer">
                  <div className="flex items-center justify-center gap-2 rounded-lg border-2 border-dashed border-purple-300 bg-purple-50 px-4 py-3 hover:bg-purple-100 transition-colors">
                    <Upload className="h-4 w-4 text-purple-500" />
                    <span className="text-sm text-purple-700 font-medium">Seleccionar archivos</span>
                  </div>
                  <input type="file" multiple accept="image/*,.pdf,.xlsx,.xls" className="hidden"
                    onChange={(e) => setCrearFiles((p) => [...p, ...Array.from(e.target.files || [])])}
                  />
                </label>
                {crearErrors.files && <p className="text-xs text-red-500">{crearErrors.files}</p>}
                {crearFiles.length > 0 && (
                  <div className="space-y-1 mt-2">
                    {crearFiles.map((f, i) => (
                      <div key={i} className="flex items-center justify-between rounded border px-3 py-1.5 text-sm bg-white">
                        <span className="truncate text-gray-700">{f.name}</span>
                        <button type="button" onClick={() => setCrearFiles((p) => p.filter((_, idx) => idx !== i))}>
                          <XIcon className="h-3.5 w-3.5 text-gray-400 hover:text-red-500" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="flex gap-2 pt-1">
                <Button variant="outline" className="flex-1" onClick={() => { setShowCrearForm(false); setCrearErrors({}); }} disabled={crearSubmitting}>
                  Volver
                </Button>
                <Button
                  className="flex-1 bg-purple-600 hover:bg-purple-700 text-white"
                  disabled={crearSubmitting}
                  onClick={async () => {
                    const errors: Record<string, string> = {};
                    if (!crearForm.titulo.trim()) errors.titulo = "El nombre es obligatorio";
                    if (!crearForm.categoria) errors.categoria = "La categoría es obligatoria";
                    if (crearFiles.length === 0) errors.files = "Adjunta al menos un archivo";
                    setCrearErrors(errors);
                    if (Object.keys(errors).length > 0) return;

                    setCrearSubmitting(true);
                    const token = localStorage.getItem("access_token");
                    try {
                      const firstEtapa = etapas.find((e) => e.area_id === 4 && e.order === 1);
                      const firstEstado = estados.find((e) => e.code === "EN_REVISION" || e.code === "PENDIENTE" || e.order === 1) || estados[0];
                      if (!firstEtapa || !firstEstado) throw new Error("Configuración de etapas no encontrada");

                      const res = await fetch(`${API_URL}/api/v1/solicitudes`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
                        body: JSON.stringify({
                          title: crearForm.titulo,
                          description: crearForm.descripcion || undefined,
                          area_id: 4,
                          stage_id: firstEtapa.id,
                          status_id: firstEstado.id,
                          es_para_cafe: crearForm.categoria === "bebidas",
                        }),
                      });
                      if (!res.ok) { const e = await res.json(); throw new Error(e.detail || "Error al crear"); }
                      const sol = await res.json();

                      // Subir archivos
                      if (crearFiles.length > 0) {
                        const { uploadFilesWithPresignedUrl } = await import("@/lib/uploadFiles");
                        await uploadFilesWithPresignedUrl(API_URL, token!, sol.id, crearFiles, "ARTE");
                      }

                      // Vincular a la iniciativa
                      await fetch(`${API_URL}/api/v1/iniciativas/${iniciativaId}/vincular-prototipado?solicitud_id=${sol.id}`, {
                        method: "POST", headers: { Authorization: `Bearer ${token}` },
                      });

                      // Recargar iniciativa
                      const updated = await fetch(`${API_URL}/api/v1/iniciativas/${iniciativaId}`, {
                        headers: { Authorization: `Bearer ${token}` },
                      }).then((r) => r.json());
                      setIniciativa(updated);
                      setShowVincular(false);
                      setShowCrearForm(false);
                      setCrearForm({ titulo: "", descripcion: "", categoria: "" });
                      setCrearFiles([]);
                      showToast(`Solicitud #${sol.id} creada y vinculada exitosamente`);
                    } catch (err: unknown) {
                      showToast(err instanceof Error ? err.message : "Error inesperado", "error");
                    } finally {
                      setCrearSubmitting(false);
                    }
                  }}
                >
                  {crearSubmitting ? "Creando..." : "Crear y vincular"}
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Dialog: Dar visto bueno solicitud Innovación */}
      <Dialog open={showAprobarInno} onOpenChange={setShowAprobarInno}>
        <DialogContent className="sm:max-w-[480px]">
          <DialogHeader>
            <DialogTitle>Dar visto bueno — {solicitudInno?.stage.label}</DialogTitle>
            <DialogDescription>La solicitud avanzará a la siguiente etapa. Opcionalmente agrega un comentario.</DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Textarea
              placeholder="Ej: Revisado y aprobado para continuar..."
              value={innoComment}
              onChange={(e) => setInnoComment(e.target.value)}
              rows={3}
              className="resize-none"
              disabled={submittingInno}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => { setShowAprobarInno(false); setInnoComment(""); }} disabled={submittingInno}>Cancelar</Button>
            <Button
              className="bg-[#00829a] hover:bg-[#006d82] text-white"
              onClick={() => handleInnoAction("aprobar", { comment: innoComment || null }, "Visto bueno registrado. Solicitud avanzada.")}
              disabled={submittingInno}
            >
              {submittingInno ? "Procesando..." : "Confirmar aprobación"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Dialog: Solicitar ajustes solicitud Innovación */}
      <Dialog open={showAjustesInno} onOpenChange={setShowAjustesInno}>
        <DialogContent className="sm:max-w-[480px]">
          <DialogHeader>
            <DialogTitle>Solicitar ajustes</DialogTitle>
            <DialogDescription>Describe los cambios necesarios. El equipo de Innovación recibirá la notificación.</DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Textarea
              placeholder="Describe los ajustes requeridos..."
              value={innoComment}
              onChange={(e) => setInnoComment(e.target.value)}
              rows={3}
              className="resize-none"
              disabled={submittingInno}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => { setShowAjustesInno(false); setInnoComment(""); }} disabled={submittingInno}>Cancelar</Button>
            <Button
              variant="outline"
              className="border-amber-400 text-amber-700 hover:bg-amber-50"
              onClick={() => { if (!innoComment.trim()) { showToast("Escribe el motivo de los ajustes", "error"); return; } handleInnoAction("solicitar-ajustes", { comment: innoComment }, "Ajustes solicitados. El equipo fue notificado."); }}
              disabled={submittingInno}
            >
              {submittingInno ? "Enviando..." : "Solicitar ajustes"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Dialog: Rechazar solicitud Innovación */}
      <Dialog open={showRechazarInno} onOpenChange={setShowRechazarInno}>
        <DialogContent className="sm:max-w-[480px]">
          <DialogHeader>
            <DialogTitle>Rechazar solicitud</DialogTitle>
            <DialogDescription>Esta acción rechazará la solicitud de Innovación. Escribe el motivo.</DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Textarea
              placeholder="Motivo del rechazo..."
              value={innoComment}
              onChange={(e) => setInnoComment(e.target.value)}
              rows={3}
              className="resize-none"
              disabled={submittingInno}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => { setShowRechazarInno(false); setInnoComment(""); }} disabled={submittingInno}>Cancelar</Button>
            <Button
              variant="destructive"
              onClick={() => { if (!innoComment.trim()) { showToast("Escribe el motivo del rechazo", "error"); return; } handleInnoAction("rechazar", { comment: innoComment }, "Solicitud rechazada."); }}
              disabled={submittingInno}
            >
              {submittingInno ? "Procesando..." : "Confirmar rechazo"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
