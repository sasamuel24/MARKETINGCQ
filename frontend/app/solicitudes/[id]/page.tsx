"use client";
import React, { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, Download, FileText, Calendar, User, Building2, Workflow, Eye, Upload, X } from "lucide-react";
import { ToastContainer, ToastData } from "@/components/ui/toast-simple";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} 
from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  rol_id: number;
}

interface SolicitudDetail {
  id: number;
  title: string;
  description: string | null;
  created_at: string;
  updated_at: string;
  state: {
    id: number;
    label: string;
    code: string;
  };
  stage: {
    id: number;
    label: string;
    code: string;
  };
  area: {
    id: number;
    nombre: string;
  };
  created_by: {
    id: number;
    full_name: string;
    email: string;
  };
  files: Array<{
    id: number;
    filename: string;
    content_type: string;
    size_bytes: number;
    doc_type: string;
    storage_path: string;
    created_at: string;
  }>;
}

export default function SolicitudDetailPage() {
  const router = useRouter();
  const params = useParams();
  const solicitudId = params?.id as string;

  const [user, setUser] = useState<User | null>(null);
  const [solicitud, setSolicitud] = useState<SolicitudDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Estados para el diálogo de solicitar ajustes
  const [showAjustesDialog, setShowAjustesDialog] = useState(false);
  const [ajustesComment, setAjustesComment] = useState("");
  const [submittingAjustes, setSubmittingAjustes] = useState(false);
  
  // Estados para el diálogo de aprobar
  const [showAprobarDialog, setShowAprobarDialog] = useState(false);
  const [aprobarComment, setAprobarComment] = useState("");
  const [submittingAprobar, setSubmittingAprobar] = useState(false);
  
  // Estados para el diálogo de rechazar
  const [showRechazarDialog, setShowRechazarDialog] = useState(false);
  const [rechazarComment, setRechazarComment] = useState("");
  const [submittingRechazar, setSubmittingRechazar] = useState(false);
  
  // Estados para vista previa de archivos
  const [showPreviewDialog, setShowPreviewDialog] = useState(false);
  const [previewFile, setPreviewFile] = useState<{url: string, filename: string, type: string} | null>(null);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [imageError, setImageError] = useState(false);
  
  // Estados para eventos/comentarios
  const [eventos, setEventos] = useState<any[]>([]);

  // Toast notifications
  const [toasts, setToasts] = useState<ToastData[]>([]);
  const showToast = (message: string, type: "success" | "error" = "success") => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message, type }]);
  };
  const removeToast = (id: number) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  };

  const [comentarioFilter, setComentarioFilter] = useState<"feedback" | "ajustes">("feedback");
  const [productImageUrl, setProductImageUrl] = useState<string | null>(null);

  // Upload de documentos (área 4)
  const [showUploadPanel, setShowUploadPanel] = useState(false);
  const [uploadFiles, setUploadFiles] = useState<File[]>([]);
  const [uploadDocType, setUploadDocType] = useState<"ARTE" | "EVIDENCIA" | "CONSOLIDADO">("EVIDENCIA");
  const [uploading, setUploading] = useState(false);

  // Comentario libre (área 4)
  const [newComment, setNewComment] = useState("");
  const [submittingComment, setSubmittingComment] = useState(false);

  // Eliminar archivo (área 4)
  const [confirmDeleteFileId, setConfirmDeleteFileId] = useState<number | null>(null);
  const [deletingFileId, setDeletingFileId] = useState<number | null>(null);

  // Card expandida por tipo de documento (área 4)
  const [expandedDocType, setExpandedDocType] = useState<"ARTE" | "EVIDENCIA" | "CONSOLIDADO" | null>(null);

  // IDs de aprobadores registrados para la etapa actual
  const [currentStageApproverIds, setCurrentStageApproverIds] = useState<number[]>([]);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/login");
      return;
    }

    // Fetch current user
    fetch(`${API_URL}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => {
        if (!res.ok) throw new Error("Unauthorized");
        return res.json();
      })
      .then((userData) => {
        setUser(userData);
        return fetchSolicitud(token);
      })
      .catch((err) => {
        console.error("Error fetching user:", err);
        router.push("/login");
      });
  }, [solicitudId, router]);

  const fetchSolicitud = async (token: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const res = await fetch(`${API_URL}/api/v1/solicitudes/${solicitudId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (!res.ok) {
        if (res.status === 404) {
          throw new Error("Solicitud no encontrada");
        }
        throw new Error("Error al cargar la solicitud");
      }

      const data = await res.json();
      setSolicitud(data);

      // Para área 4, cargar imagen del producto como blob (requiere auth)
      if (data.area?.id === 4) {
        const imgFile = data.files?.find((f: { content_type: string; id: number }) =>
          f.content_type.startsWith("image/")
        );
        if (imgFile) {
          fetch(`${API_URL}/api/v1/solicitudes/${solicitudId}/files/${imgFile.id}/preview`, {
            headers: { Authorization: `Bearer ${token}` },
          })
            .then((r) => (r.ok ? r.blob() : null))
            .then((blob) => {
              if (blob) setProductImageUrl(URL.createObjectURL(blob));
            })
            .catch(() => {});
        }
      }

      // Cargar eventos/comentarios
      fetchEventos(token);

      // Cargar aprobadores de la etapa actual
      if (data.stage?.id) {
        fetchCurrentStageApprovers(token, data.stage.id);
      }
    } catch (err) {
      console.error("Error fetching solicitud:", err);
      setError(err instanceof Error ? err.message : "Error desconocido");
    } finally {
      setLoading(false);
    }
  };

  const fetchCurrentStageApprovers = async (token: string, stageId: number) => {
    try {
      const res = await fetch(`${API_URL}/api/v1/etapa-aprobadores/etapa/${stageId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data: Array<{ user: { id: number } }> = await res.json();
        setCurrentStageApproverIds(data.map((a) => a.user.id));
      }
    } catch (err) {
      console.error("Error fetching stage approvers:", err);
    }
  };

  const fetchEventos = async (token: string) => {
    try {
      const res = await fetch(`${API_URL}/api/v1/solicitudes/${solicitudId}/eventos`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (res.ok) {
        const data = await res.json();
        setEventos(data);
      }
    } catch (err) {
      console.error("Error fetching eventos:", err);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("es-ES", {
      day: "2-digit",
      month: "long",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    });
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getStatusVariant = (code: string): "default" | "secondary" | "destructive" | "outline" => {
    if (code === "APROBADO" || code === "APPROVED") return "default";
    if (code === "RECHAZADO" || code === "REJECTED") return "destructive";
    if (code === "PENDIENTE" || code === "PENDING") return "secondary";
    return "outline";
  };

  const handleDownloadFile = async (fileId: number, filename: string) => {
    const token = localStorage.getItem("access_token");
    
    try {
      // Descargar archivo directamente desde el backend
      const res = await fetch(`${API_URL}/api/v1/solicitudes/${solicitudId}/files/${fileId}/download`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (!res.ok) {
        throw new Error("Error al descargar archivo");
      }

      // Obtener el archivo como blob
      const blob = await res.blob();
      
      // Crear URL temporal del blob
      const blobUrl = window.URL.createObjectURL(blob);
      
      // Crear enlace de descarga
      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      
      // Limpiar
      document.body.removeChild(link);
      window.URL.revokeObjectURL(blobUrl);
      
    } catch (err) {
      console.error("Error downloading file:", err);
      showToast("Error al descargar el archivo. Por favor, intenta nuevamente.", "error");
    }
  };

  const handlePreviewFile = async (fileId: number, filename: string, contentType: string) => {
    const token = localStorage.getItem("access_token");
    setLoadingPreview(true);
    setImageError(false);
    
    try {
      // Limpiar preview anterior si existe
      if (previewFile) {
        window.URL.revokeObjectURL(previewFile.url);
      }
      
      // Usar endpoint de preview optimizado (thumbnails pre-generados en S3)
      const endpoint = contentType.startsWith('image/') 
        ? `${API_URL}/api/v1/solicitudes/${solicitudId}/files/${fileId}/preview`
        : `${API_URL}/api/v1/solicitudes/${solicitudId}/files/${fileId}/download`;
        
      const res = await fetch(endpoint, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (!res.ok) {
        throw new Error("Error al cargar vista previa");
      }

      // Obtener el archivo como blob
      const blob = await res.blob();
      
      // Crear URL temporal del blob
      const blobUrl = window.URL.createObjectURL(blob);
      
      // Abrir en modal
      setPreviewFile({
        url: blobUrl,
        filename: filename,
        type: contentType
      });
      setShowPreviewDialog(true);
      
    } catch (err) {
      console.error("Error loading preview:", err);
      showToast("Error al cargar la vista previa. Por favor, intenta nuevamente.", "error");
    } finally {
      setLoadingPreview(false);
    }
  };

  const handleSolicitarAjustes = async () => {
    if (!ajustesComment.trim()) {
      showToast("Por favor, escribe un comentario explicando los ajustes necesarios", "error");
      return;
    }

    setSubmittingAjustes(true);
    const token = localStorage.getItem("access_token");

    try {
      const res = await fetch(`${API_URL}/api/v1/solicitudes/${solicitudId}/solicitar-ajustes`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ comment: ajustesComment })
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Error al solicitar ajustes");
      }

      const updatedSolicitud = await res.json();
      setSolicitud(updatedSolicitud);
      setShowAjustesDialog(false);
      setAjustesComment("");
      
      // Recargar eventos para mostrar el nuevo comentario
      fetchEventos(token!);
      
      showToast("Ajustes solicitados. El creador ha sido notificado.", "success");

    } catch (err) {
      console.error("Error solicitando ajustes:", err);
      showToast(err instanceof Error ? err.message : "Error al solicitar ajustes", "error");
    } finally {
      setSubmittingAjustes(false);
    }
  };

  const handleAprobar = async () => {
    setSubmittingAprobar(true);
    const token = localStorage.getItem("access_token");

    // Área 4: creador usa cerrar-diagnostico; aprobador registrado usa /aprobar (con lógica multi-aprobador)
    const endpoint = solicitud?.area.id === 4 && !isApprover
      ? `${API_URL}/api/v1/solicitudes/${solicitudId}/cerrar-diagnostico`
      : `${API_URL}/api/v1/solicitudes/${solicitudId}/aprobar`;

    try {
      const res = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ comment: aprobarComment || null })
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Error al aprobar solicitud");
      }

      const updatedSolicitud = await res.json();
      setSolicitud(updatedSolicitud);
      setShowAprobarDialog(false);
      setAprobarComment("");

      // Recargar eventos y aprobadores de la nueva etapa
      fetchEventos(token!);
      fetchCurrentStageApprovers(token!, updatedSolicitud.stage.id);
      
      // Mensaje según el nuevo estado
      if (updatedSolicitud.state.code === "APROBADO_FINAL") {
        showToast("✓ Solicitud aprobada. Ha completado todas las etapas.", "success");
      } else {
        showToast(`✓ Aprobado — avanzó a etapa: ${updatedSolicitud.stage.label}`, "success");
      }

    } catch (err) {
      console.error("Error aprobando solicitud:", err);
      showToast(err instanceof Error ? err.message : "Error al aprobar solicitud", "error");
    } finally {
      setSubmittingAprobar(false);
    }
  };

  const handleRechazar = async () => {
    if (!rechazarComment.trim()) {
      showToast("Por favor, escribe el motivo del rechazo", "error");
      return;
    }

    setSubmittingRechazar(true);
    const token = localStorage.getItem("access_token");

    try {
      const res = await fetch(`${API_URL}/api/v1/solicitudes/${solicitudId}/rechazar`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ comment: rechazarComment })
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Error al rechazar solicitud");
      }

      const updatedSolicitud = await res.json();
      setSolicitud(updatedSolicitud);
      setShowRechazarDialog(false);
      setRechazarComment("");
      
      // Recargar eventos para mostrar el nuevo comentario
      fetchEventos(token!);
      
      showToast("Solicitud rechazada. El creador ha sido notificado.", "success");

    } catch (err) {
      console.error("Error rechazando solicitud:", err);
      showToast(err instanceof Error ? err.message : "Error al rechazar solicitud", "error");
    } finally {
      setSubmittingRechazar(false);
    }
  };

  if (loading) {
    return (
      <div className="flex w-full flex-col bg-muted/40 p-4 md:p-10">
        <div className="p-8 text-center">Cargando solicitud...</div>
      </div>
    );
  }

  if (error || !solicitud) {
    return (
      <div className="flex w-full flex-col bg-muted/40 p-4 md:p-10">
        <div className="flex flex-col gap-6">
          <Button
            variant="ghost"
            onClick={() => router.push("/dashboard")}
            className="w-fit"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Volver al dashboard
          </Button>
          <Card>
            <CardHeader>
              <CardTitle>Error</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-red-500">{error || "Solicitud no encontrada"}</p>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  const isCreator = user?.id === solicitud.created_by.id.toString();
  const isApprover = user?.role === "APPROVER" || user?.rol_id === 3;
  const isAjustesSolicitados = solicitud.state.code === "AJUSTES_SOLICITADOS" || 
                                solicitud.state.label === "Ajustes solicitados";
  const isAprobadoFinal = solicitud.state.code === "APROBADO_FINAL" || 
                          solicitud.state.label === "Aprobado final";
  const isRechazado = solicitud.state.code === "RECHAZADO" || 
                      solicitud.state.label === "Rechazado";
  
  // Verificar si el usuario actual ya aprobó en la etapa actual
  const userAlreadyApproved = eventos.some(evento =>
    evento.action === "APPROVED" &&
    evento.stage.id === solicitud.stage.id &&
    evento.actor.id.toString() === user?.id
  );

  const handleUploadNewFiles = async () => {
    if (uploadFiles.length === 0) {
      showToast("Selecciona al menos un archivo", "error");
      return;
    }
    const existingCount = solicitud?.files.filter((f) => f.doc_type === uploadDocType).length ?? 0;
    if (uploadDocType !== "EVIDENCIA" && existingCount + uploadFiles.length > 3) {
      showToast(`Solo se permiten 3 archivos por tipo. Ya hay ${existingCount} en "${uploadDocType}".`, "error");
      return;
    }
    setUploading(true);
    const token = localStorage.getItem("access_token");
    try {
      const { uploadFilesWithPresignedUrl } = await import("@/lib/uploadFiles");
      await uploadFilesWithPresignedUrl(API_URL, token!, solicitud.id, uploadFiles, uploadDocType);
      setUploadFiles([]);
      setShowUploadPanel(false);
      await fetchSolicitud(token!);
      showToast(`${uploadFiles.length} archivo(s) subido(s) correctamente`);
    } catch {
      showToast("Error al subir los archivos", "error");
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteFile = async (fileId: number) => {
    setDeletingFileId(fileId);
    const token = localStorage.getItem("access_token");
    try {
      const res = await fetch(`${API_URL}/api/v1/solicitud-files/${fileId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Error al eliminar");
      setConfirmDeleteFileId(null);
      await fetchSolicitud(token!);
      showToast("Archivo eliminado correctamente");
    } catch {
      showToast("Error al eliminar el archivo", "error");
    } finally {
      setDeletingFileId(null);
    }
  };

  const handleAddComment = async () => {
    if (!newComment.trim()) return;
    setSubmittingComment(true);
    const token = localStorage.getItem("access_token");
    try {
      const res = await fetch(`${API_URL}/api/v1/solicitudes/${solicitudId}/comentar`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ comment: newComment, categoria: comentarioFilter }),
      });
      if (!res.ok) throw new Error("Error al guardar el comentario");
      setNewComment("");
      await fetchEventos(token!);
      showToast("Comentario registrado");
    } catch {
      showToast("Error al agregar el comentario", "error");
    } finally {
      setSubmittingComment(false);
    }
  };

  // ─────────────────────────────────────────────────────────────
  // PRODUCCION_BEBIDAS_PASTELERIA (area_id = 4) – Vista Figma
  // ─────────────────────────────────────────────────────────────
  if (solicitud.area.id === 4) {
    const feedbackEventos = eventos.filter((e) => e.action === "APPROVED" || e.action === "COMMENTED" || e.action === "SUBMITTED");
    const ajustesEventos  = eventos.filter((e) => e.action === "REQUEST_CHANGES" || e.action === "REJECTED");
    const filteredEventos  = comentarioFilter === "feedback" ? feedbackEventos : ajustesEventos;

    // El usuario es aprobador de la etapa ACTUAL (no de una etapa ya superada)
    const isCurrentStageApprover = user ? currentStageApproverIds.includes(parseInt(user.id)) : false;
    // El usuario ya aprobó en la etapa actual
    const alreadyApprovedCurrentStage = userAlreadyApproved;
    // El usuario aprobó en alguna etapa anterior (la etapa ya avanzó)
    const approvedInPreviousStage = !isCurrentStageApprover && eventos.some(
      (e) => e.action === "APPROVED" && e.actor.id.toString() === user?.id
    );

    // Creador: puede "Cerrar Diagnóstico" para enviar al aprobador (siempre que no esté en estado terminal ni ajustes pendientes)
    // Aprobador de la etapa actual: puede aprobar mientras no haya ya aprobado
    const canCerrar = !isAprobadoFinal && !isRechazado &&
      (isCreator || (isCurrentStageApprover && !alreadyApprovedCurrentStage && !isAjustesSolicitados));

    const getDocTypeLabel = (docType: string) => {
      if (docType === "ARTE")        return "Hoja de Producto";
      if (docType === "EVIDENCIA")   return "Evidencia Fotográfica";
      if (docType === "CONSOLIDADO") return "Documento consolidado versión final";
      return docType;
    };

    const getDocTypeDesc = (docType: string) => {
      if (docType === "ARTE")        return "Archivo principal del producto";
      if (docType === "EVIDENCIA")   return "→ Fotos de los prototipos físicos realizados";
      if (docType === "CONSOLIDADO") return "Versión final (cuando aplique)";
      return "";
    };

    return (
      <div className="min-h-screen" style={{ background: "#daeef0" }}>
        <div className="max-w-2xl mx-auto px-4 py-6 flex flex-col gap-4">

          {/* Volver */}
          <button
            onClick={() => router.push("/dashboard")}
            className="flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900 w-fit"
          >
            <ArrowLeft className="h-4 w-4" />
            Volver
          </button>

          {/* Tarjeta principal del producto */}
          <div className="bg-white rounded-2xl p-5 shadow-sm">
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1 min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <h1 className="text-xl font-bold">{solicitud.title}</h1>
                  <span
                    className="text-xs rounded-full px-3 py-1 font-medium border"
                    style={{ background: "#e8f5f4", color: "#339b92", borderColor: "#c0e0de" }}
                  >
                    {solicitud.state.label}
                  </span>
                </div>
                <p className="text-sm text-gray-500 mt-1">Solicitud #{solicitud.id}</p>
              </div>
              {productImageUrl && (
                <img
                  src={productImageUrl}
                  alt={solicitud.title}
                  className="w-40 h-40 rounded-xl object-cover flex-shrink-0 shadow-sm"
                />
              )}
            </div>

            {solicitud.description && (
              <div className="mt-4">
                <h3 className="font-semibold text-sm mb-1">Descripción</h3>
                <p className="text-sm text-gray-600 whitespace-pre-wrap">{solicitud.description}</p>
              </div>
            )}

            {/* Grid de metadatos */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-5">
              <div className="rounded-xl p-4 flex items-start gap-3" style={{ background: "#e8f5f4" }}>
                <Building2 className="h-5 w-5 mt-0.5 flex-shrink-0" style={{ color: "#339b92" }} />
                <div>
                  <p className="text-xs text-gray-500 uppercase font-semibold tracking-wide">Área</p>
                  <p className="text-sm font-medium mt-0.5">{solicitud.area.nombre}</p>
                </div>
              </div>
              <div className="rounded-xl p-4 flex items-start gap-3" style={{ background: "#e8f5f4" }}>
                <Workflow className="h-5 w-5 mt-0.5 flex-shrink-0" style={{ color: "#339b92" }} />
                <div>
                  <p className="text-xs text-gray-500 uppercase font-semibold tracking-wide">Etapa actual</p>
                  <p className="text-sm font-medium mt-0.5">{solicitud.stage.label}</p>
                </div>
              </div>
              <div className="rounded-xl p-4 flex items-start gap-3" style={{ background: "#e8f5f4" }}>
                <User className="h-5 w-5 mt-0.5 flex-shrink-0" style={{ color: "#339b92" }} />
                <div>
                  <p className="text-xs text-gray-500 uppercase font-semibold tracking-wide">Creado por</p>
                  <p className="text-sm font-medium mt-0.5">{solicitud.created_by.full_name}</p>
                  <p className="text-xs text-gray-500">{solicitud.created_by.email}</p>
                </div>
              </div>
              <div className="rounded-xl p-4 flex items-start gap-3" style={{ background: "#e8f5f4" }}>
                <Calendar className="h-5 w-5 mt-0.5 flex-shrink-0" style={{ color: "#339b92" }} />
                <div>
                  <p className="text-xs text-gray-500 uppercase font-semibold tracking-wide">Fechas</p>
                  <p className="text-xs text-gray-600 mt-0.5">Creado: {formatDate(solicitud.created_at)}</p>
                  <p className="text-xs text-gray-600">Última actualización: {formatDate(solicitud.updated_at)}</p>
                </div>
              </div>
            </div>
          </div>

          {/* Archivos – 3 tarjetas fijas por tipo, expandibles */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {(["ARTE", "EVIDENCIA", "CONSOLIDADO"] as const).map((tipo) => {
              const tipoFiles = solicitud.files.filter((f) => f.doc_type === tipo);
              const isExpanded = expandedDocType === tipo;
              const atLimit = tipo !== "EVIDENCIA" && tipoFiles.length >= 3;

              return (
                <div key={tipo} className="bg-white rounded-2xl shadow-sm overflow-hidden flex flex-col">
                  {/* Cabecera clickable */}
                  <button
                    className="w-full flex items-start justify-between p-4 text-left hover:bg-gray-50 transition-colors"
                    onClick={() => setExpandedDocType(isExpanded ? null : tipo)}
                  >
                    <div className="flex items-start gap-2 flex-1 min-w-0">
                      <FileText className="h-5 w-5 flex-shrink-0 mt-0.5" style={{ color: "#339b92" }} />
                      <div className="min-w-0">
                        <p className="text-sm font-semibold leading-snug">{getDocTypeLabel(tipo)}</p>
                        <p className="text-xs text-gray-500 mt-0.5">{getDocTypeDesc(tipo)}</p>
                        <div className="flex items-center gap-1.5 mt-1.5">
                          <span
                            className="text-xs font-semibold px-2 py-0.5 rounded-full"
                            style={{
                              background: tipoFiles.length === 0 ? "#f3f4f6" : atLimit ? "#fef3c7" : "#e8f5f4",
                              color: tipoFiles.length === 0 ? "#9ca3af" : atLimit ? "#92400e" : "#339b92",
                            }}
                          >
                            {tipoFiles.length === 0
                              ? "Sin archivos"
                              : tipo === "EVIDENCIA"
                              ? `${tipoFiles.length} archivo${tipoFiles.length > 1 ? "s" : ""}`
                              : `${tipoFiles.length}/3 archivo${tipoFiles.length > 1 ? "s" : ""}`}
                          </span>
                        </div>
                      </div>
                    </div>
                    <span className="text-gray-400 text-lg leading-none ml-2 flex-shrink-0">
                      {isExpanded ? "−" : "+"}
                    </span>
                  </button>

                  {/* Lista expandida */}
                  {isExpanded && (
                    <div className="border-t border-gray-100 px-3 pb-3">
                      {tipoFiles.length === 0 ? (
                        <p className="text-xs text-gray-400 py-4 text-center">
                          No hay archivos de este tipo
                        </p>
                      ) : (
                        <div className="space-y-1.5 pt-2">
                          {tipoFiles.map((file) => (
                            <div
                              key={file.id}
                              className="rounded-lg border border-gray-100 bg-gray-50"
                            >
                              {/* Nombre del archivo */}
                              <div className="flex items-center gap-2 px-3 pt-2 pb-1 min-w-0">
                                <FileText className="h-3.5 w-3.5 text-gray-400 flex-shrink-0" />
                                <span className="text-xs text-gray-600 truncate">{file.filename}</span>
                              </div>

                              {/* Acciones */}
                              {confirmDeleteFileId === file.id ? (
                                <div className="flex items-center justify-between px-3 pb-2">
                                  <p className="text-xs text-red-500 font-medium">¿Eliminar?</p>
                                  <div className="flex gap-1.5">
                                    <button
                                      onClick={() => setConfirmDeleteFileId(null)}
                                      className="text-xs px-2 py-0.5 rounded border text-gray-500"
                                      disabled={deletingFileId === file.id}
                                    >
                                      No
                                    </button>
                                    <button
                                      onClick={() => handleDeleteFile(file.id)}
                                      className="text-xs px-2 py-0.5 rounded text-white font-medium"
                                      style={{ background: "#dc2626" }}
                                      disabled={deletingFileId === file.id}
                                    >
                                      {deletingFileId === file.id ? "…" : "Sí"}
                                    </button>
                                  </div>
                                </div>
                              ) : (
                                <div className="flex items-center justify-end gap-3 px-3 pb-2">
                                  {(file.content_type.startsWith("image/") ||
                                    file.content_type === "application/pdf") && (
                                    <button
                                      onClick={() =>
                                        handlePreviewFile(file.id, file.filename, file.content_type)
                                      }
                                      disabled={loadingPreview}
                                      className="text-gray-400 hover:text-[#339b92] transition-colors"
                                      title="Vista previa"
                                    >
                                      <Eye className="h-4 w-4" />
                                    </button>
                                  )}
                                  <button
                                    onClick={() => handleDownloadFile(file.id, file.filename)}
                                    className="text-gray-400 hover:text-[#339b92] transition-colors"
                                    title="Descargar"
                                  >
                                    <Download className="h-4 w-4" />
                                  </button>
                                  <button
                                    onClick={() => setConfirmDeleteFileId(file.id)}
                                    className="text-gray-300 hover:text-red-400 transition-colors"
                                    title="Eliminar"
                                  >
                                    <X className="h-4 w-4" />
                                  </button>
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      )}

                      {atLimit && (
                        <p className="text-xs text-amber-600 font-medium text-center mt-2 pb-1">
                          Límite de 3 archivos alcanzado para este tipo
                        </p>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* ── Panel: Agregar documentos ── */}
          <div className="bg-white rounded-2xl shadow-sm overflow-hidden">
            <button
              className="w-full flex items-center justify-between px-5 py-4 text-left"
              onClick={() => setShowUploadPanel((v) => !v)}
            >
              <div className="flex items-center gap-2">
                <Upload className="h-5 w-5" style={{ color: "#339b92" }} />
                <span className="font-semibold text-sm">Agregar documentos a la ficha</span>
              </div>
              <span className="text-gray-400 text-lg leading-none">{showUploadPanel ? "−" : "+"}</span>
            </button>

            {showUploadPanel && (
              <div className="px-5 pb-5 flex flex-col gap-3 border-t border-gray-100">
                {/* Selector de tipo con contador */}
                <div className="flex gap-2 flex-wrap pt-3">
                  {(["ARTE", "EVIDENCIA", "CONSOLIDADO"] as const).map((tipo) => {
                    const count = solicitud.files.filter((f) => f.doc_type === tipo).length;
                    const full = tipo !== "EVIDENCIA" && count >= 3;
                    return (
                      <button
                        key={tipo}
                        onClick={() => { if (!full) setUploadDocType(tipo); }}
                        disabled={full}
                        className="px-3 py-1.5 rounded-lg text-xs font-semibold border transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                        style={{
                          background: uploadDocType === tipo ? "#339b92" : "white",
                          color: uploadDocType === tipo ? "white" : "#339b92",
                          borderColor: "#339b92",
                        }}
                      >
                        {tipo === "ARTE" ? "Hoja de Producto" : tipo === "EVIDENCIA" ? "Evidencia Fotográfica" : "Doc. Consolidado"}
                        {" "}
                        <span className="opacity-75">({tipo === "EVIDENCIA" ? count : `${count}/3`})</span>
                      </button>
                    );
                  })}
                </div>

                {/* Aviso si el tipo seleccionado está lleno */}
                {solicitud.files.filter((f) => f.doc_type === uploadDocType).length >= 3 && (
                  <p className="text-xs text-amber-600 font-medium">
                    Este tipo ya tiene 3 archivos. Elimina uno antes de agregar otro.
                  </p>
                )}

                {/* Zona de drop */}
                <label
                  htmlFor="area4-file-upload"
                  className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed rounded-xl cursor-pointer transition-colors"
                  style={{ borderColor: "#339b92" }}
                >
                  <Upload className="h-8 w-8 mb-1" style={{ color: "#339b92" }} />
                  <p className="text-sm text-gray-500">
                    <span className="font-semibold" style={{ color: "#339b92" }}>Seleccionar archivos</span>
                    {" "}o arrastra aquí
                  </p>
                  <p className="text-xs text-gray-400 mt-0.5">PDF, imagen, Excel — máx. 50 MB</p>
                  <input
                    id="area4-file-upload"
                    type="file"
                    className="hidden"
                    multiple
                    accept=".pdf,.png,.jpg,.jpeg,.xlsx,.xls"
                    onChange={(e) => {
                      if (e.target.files)
                        setUploadFiles((prev) => [...prev, ...Array.from(e.target.files!)]);
                    }}
                    disabled={uploading}
                  />
                </label>

                {/* Lista de archivos seleccionados */}
                {uploadFiles.length > 0 && (
                  <div className="space-y-2">
                    {uploadFiles.map((file, i) => (
                      <div key={i} className="flex items-center justify-between border rounded-lg px-3 py-2">
                        <div className="flex items-center gap-2 min-w-0">
                          <FileText className="h-4 w-4 flex-shrink-0 text-gray-400" />
                          <span className="text-sm truncate">{file.name}</span>
                          <span className="text-xs text-gray-400 flex-shrink-0">
                            ({(file.size / 1024).toFixed(0)} KB)
                          </span>
                        </div>
                        <button
                          onClick={() => setUploadFiles((prev) => prev.filter((_, j) => j !== i))}
                          className="text-gray-400 hover:text-red-500 ml-2 flex-shrink-0"
                        >
                          <X className="h-4 w-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}

                {/* Botones */}
                <div className="flex gap-2 justify-end pt-1">
                  <button
                    onClick={() => { setShowUploadPanel(false); setUploadFiles([]); }}
                    className="px-4 py-2 text-sm rounded-xl border text-gray-500"
                    disabled={uploading}
                  >
                    Cancelar
                  </button>
                  <button
                    onClick={handleUploadNewFiles}
                    disabled={uploadFiles.length === 0 || uploading}
                    className="px-4 py-2 text-sm font-semibold rounded-xl text-white transition-colors disabled:opacity-50"
                    style={{ background: "#339b92" }}
                  >
                    {uploading ? "Subiendo..." : `Subir ${uploadFiles.length > 0 ? `(${uploadFiles.length})` : ""}`}
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Historial de comentarios */}
          <div className="bg-white rounded-2xl p-5 shadow-sm">
            <h3 className="font-semibold text-base">Historial de comentarios</h3>
            <p className="text-xs text-gray-500 mb-4">Registro de ajustes solicitados y comentarios</p>

            {/* Filtros */}
            <div className="flex justify-end gap-2 mb-4 flex-wrap">
              <button
                className="px-4 py-2 rounded-xl text-sm font-semibold transition-colors"
                style={{
                  background: comentarioFilter === "feedback" ? "#339b92" : "#d9d9d9",
                  color: comentarioFilter === "feedback" ? "white" : "#333",
                }}
                onClick={() => setComentarioFilter("feedback")}
              >
                Registro de Feedback
              </button>
              <button
                className="px-4 py-2 rounded-xl text-sm font-semibold transition-colors"
                style={{
                  background: comentarioFilter === "ajustes" ? "#339b92" : "#d9d9d9",
                  color: comentarioFilter === "ajustes" ? "white" : "#333",
                }}
                onClick={() => setComentarioFilter("ajustes")}
              >
                Ajustes Realizados
              </button>
            </div>

            {filteredEventos.length === 0 ? (
              <p className="text-sm text-gray-400 text-center py-6">No hay registros en esta categoría</p>
            ) : (
              <div className="space-y-3">
                {filteredEventos
                  .slice()
                  .reverse()
                  .map((evento) => (
                    <div key={evento.id} className="border rounded-xl p-4">
                      <div className="flex items-start justify-between gap-2 flex-wrap">
                        <div className="flex items-start gap-2">
                          <div className="h-8 w-8 rounded-full bg-gray-100 flex items-center justify-center flex-shrink-0">
                            <User className="h-4 w-4 text-gray-400" />
                          </div>
                          <div>
                            <p className="text-sm font-semibold">{evento.actor.full_name}</p>
                            <p className="text-xs text-gray-500">{evento.actor.email}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <span
                            className="text-xs px-3 py-1 rounded-full font-semibold"
                            style={{
                              background:
                                evento.action === "APPROVED"
                                  ? "#1a5c38"
                                  : evento.action === "REJECTED"
                                  ? "#fee2e2"
                                  : evento.action === "SUBMITTED"
                                  ? "#e8f5f4"
                                  : evento.action === "COMMENTED"
                                  ? "#e8f5f4"
                                  : "#fef3c7",
                              color:
                                evento.action === "APPROVED"
                                  ? "white"
                                  : evento.action === "REJECTED"
                                  ? "#dc2626"
                                  : evento.action === "SUBMITTED"
                                  ? "#339b92"
                                  : evento.action === "COMMENTED"
                                  ? "#339b92"
                                  : "#92400e",
                            }}
                          >
                            {evento.action === "REQUEST_CHANGES"
                              ? "Ajustes solicitados"
                              : evento.action === "APPROVED"
                              ? `Aprobado en ${evento.stage.label}`
                              : evento.action === "REJECTED"
                              ? "Rechazado"
                              : evento.action === "COMMENTED"
                              ? "Comentario"
                              : evento.action === "SUBMITTED"
                              ? "Diagnóstico cerrado"
                              : evento.action}
                          </span>
                          <p className="text-xs text-gray-400 mt-1 whitespace-nowrap">
                            {formatDate(evento.created_at)}
                          </p>
                        </div>
                      </div>
                      {evento.comment && (
                        <div className="mt-3 bg-gray-50 rounded-lg p-3">
                          <p className="text-sm whitespace-pre-wrap">{evento.comment}</p>
                        </div>
                      )}
                    </div>
                  ))}
              </div>
            )}

            {/* Campo para agregar comentario */}
            <div className="mt-4 pt-4 border-t border-gray-100">
              <p className="text-sm font-semibold mb-2">Agregar comentario</p>
              <textarea
                rows={3}
                placeholder={
                  comentarioFilter === "feedback"
                    ? "Escribe un comentario de feedback o nota de seguimiento..."
                    : "Describe el ajuste realizado al producto..."
                }
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                disabled={submittingComment}
                className="w-full rounded-xl border px-3 py-2 text-sm resize-none outline-none focus:border-[#339b92] transition-colors"
                style={{ borderColor: "#d1d5db" }}
              />
              <div className="flex justify-end mt-2">
                <button
                  onClick={handleAddComment}
                  disabled={!newComment.trim() || submittingComment}
                  className="px-5 py-2 rounded-xl text-sm font-semibold text-white transition-colors disabled:opacity-50"
                  style={{ background: "#339b92" }}
                >
                  {submittingComment ? "Enviando..." : "Enviar comentario"}
                </button>
              </div>
            </div>
          </div>

          {/* Subir nueva versión — no aplica en área 4, el creador usa "Cerrar Diagnóstico" directamente */}

          {/* Cerrar Diagnóstico Técnico */}
          {canCerrar && (
            <button
              onClick={() => setShowAprobarDialog(true)}
              className="w-full py-4 font-semibold text-base text-white rounded-2xl transition-colors"
              style={{ background: "#339b92" }}
            >
              {solicitud.stage.code === "PROD_E3" ? "Aprobar" : "Cerrar Diagnóstico Técnico"}
            </button>
          )}

          {/* Solicitar ajustes / Rechazar (aprobadores de la etapa actual — oculto en PROD_E3 "Filtro por Gerencias") */}
          {isCurrentStageApprover && !alreadyApprovedCurrentStage && !isAjustesSolicitados && !isAprobadoFinal && !isRechazado && solicitud.stage.code !== "PROD_E3" && (
            <div className="flex gap-3">
              <button
                onClick={() => setShowAjustesDialog(true)}
                className="flex-1 py-3 font-semibold text-sm rounded-2xl border-2 transition-colors"
                style={{ borderColor: "#339b92", color: "#339b92" }}
              >
                Solicitar ajustes
              </button>
              <button
                onClick={() => setShowRechazarDialog(true)}
                className="flex-1 py-3 font-semibold text-sm rounded-2xl border-2 border-red-400 text-red-500 transition-colors"
              >
                Rechazar
              </button>
            </div>
          )}

          {/* Estado ya aprobado por este usuario en la etapa actual */}
          {isCurrentStageApprover && !isAjustesSolicitados && !isAprobadoFinal && !isRechazado && alreadyApprovedCurrentStage && (
            <div className="bg-white rounded-2xl p-4 text-sm text-gray-500 text-center shadow-sm">
              Tu aprobación ha sido registrada para esta etapa. La solicitud avanzará cuando todos los aprobadores hayan dado su visto bueno.
            </div>
          )}

          {/* El usuario aprobó en una etapa anterior (la solicitud ya avanzó) */}
          {approvedInPreviousStage && !isAprobadoFinal && !isRechazado && (
            <div className="bg-white rounded-2xl p-4 text-sm text-gray-500 text-center shadow-sm">
              Ya registraste tu aprobación en esta solicitud. La solicitud está siendo procesada en la siguiente etapa.
            </div>
          )}

          {isAprobadoFinal && (
            <div
              className="rounded-2xl p-4 text-sm font-semibold text-center"
              style={{ background: "#1a5c38", color: "white" }}
            >
              Diagnóstico técnico cerrado — solicitud aprobada en todas las etapas
            </div>
          )}

          {isRechazado && (
            <div className="rounded-2xl p-4 text-sm font-semibold text-center bg-red-50 text-red-600 border border-red-200">
              Solicitud rechazada. Revisa el historial de comentarios.
            </div>
          )}
        </div>

        {/* ── Dialogs (reutilizados del flujo general) ── */}
        <Dialog open={showAprobarDialog} onOpenChange={setShowAprobarDialog}>
          <DialogContent className="sm:max-w-[525px]">
            <DialogHeader>
              <DialogTitle>Cerrar Diagnóstico Técnico</DialogTitle>
              <DialogDescription>
                La solicitud avanzará a la siguiente etapa o se marcará como aprobada final.
                Opcionalmente puedes agregar un comentario.
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="aprobar-comment-area4">Comentario (opcional)</Label>
                <Textarea
                  id="aprobar-comment-area4"
                  placeholder="Ej: Diagnóstico técnico verificado, aprobado para continuar..."
                  value={aprobarComment}
                  onChange={(e) => setAprobarComment(e.target.value)}
                  rows={4}
                  className="resize-none"
                  disabled={submittingAprobar}
                />
                <p className="text-xs text-muted-foreground">{aprobarComment.length}/1000 caracteres</p>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => { setShowAprobarDialog(false); setAprobarComment(""); }} disabled={submittingAprobar}>
                Cancelar
              </Button>
              <Button onClick={handleAprobar} disabled={submittingAprobar} style={{ background: "#339b92" }}>
                {submittingAprobar ? "Procesando..." : "Confirmar cierre"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        <Dialog open={showAjustesDialog} onOpenChange={setShowAjustesDialog}>
          <DialogContent className="sm:max-w-[525px]">
            <DialogHeader>
              <DialogTitle>Solicitar ajustes</DialogTitle>
              <DialogDescription>Explica los cambios necesarios para esta innovación.</DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="ajustes-comment-area4">Comentarios sobre los ajustes necesarios *</Label>
                <Textarea
                  id="ajustes-comment-area4"
                  placeholder="Ej: Ajustar la formulación del producto según observaciones..."
                  value={ajustesComment}
                  onChange={(e) => setAjustesComment(e.target.value)}
                  rows={5}
                  className="resize-none"
                  disabled={submittingAjustes}
                />
                <p className="text-xs text-muted-foreground">{ajustesComment.length}/1000 caracteres</p>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => { setShowAjustesDialog(false); setAjustesComment(""); }} disabled={submittingAjustes}>
                Cancelar
              </Button>
              <Button onClick={handleSolicitarAjustes} disabled={submittingAjustes || !ajustesComment.trim()}>
                {submittingAjustes ? "Enviando..." : "Solicitar ajustes"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        <Dialog open={showRechazarDialog} onOpenChange={setShowRechazarDialog}>
          <DialogContent className="sm:max-w-[525px]">
            <DialogHeader>
              <DialogTitle>Rechazar solicitud</DialogTitle>
              <DialogDescription>Explica el motivo por el cual esta innovación no cumple los requisitos.</DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="rechazar-comment-area4">Motivo del rechazo *</Label>
                <Textarea
                  id="rechazar-comment-area4"
                  placeholder="Ej: No cumple con los estándares de producción establecidos..."
                  value={rechazarComment}
                  onChange={(e) => setRechazarComment(e.target.value)}
                  rows={5}
                  className="resize-none"
                  disabled={submittingRechazar}
                />
                <p className="text-xs text-muted-foreground">{rechazarComment.length}/1000 caracteres</p>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => { setShowRechazarDialog(false); setRechazarComment(""); }} disabled={submittingRechazar}>
                Cancelar
              </Button>
              <Button variant="destructive" onClick={handleRechazar} disabled={submittingRechazar || !rechazarComment.trim()}>
                {submittingRechazar ? "Rechazando..." : "Rechazar solicitud"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        <Dialog open={showPreviewDialog} onOpenChange={(open) => {
          setShowPreviewDialog(open);
          if (!open) {
            if (previewFile) window.URL.revokeObjectURL(previewFile.url);
            setPreviewFile(null);
            setImageError(false);
          }
        }}>
          <DialogContent className="sm:max-w-[90vw] max-h-[90vh] overflow-auto">
            <DialogHeader>
              <DialogTitle>{previewFile?.filename}</DialogTitle>
              <DialogDescription>Vista previa del archivo</DialogDescription>
            </DialogHeader>
            <div className="flex items-center justify-center p-4 min-h-[400px]">
              {loadingPreview ? (
                <div className="flex flex-col items-center gap-4">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#339b92]"></div>
                  <p className="text-sm text-muted-foreground">Cargando vista previa...</p>
                </div>
              ) : previewFile ? (
                <>
                  {previewFile.type.startsWith("image/") ? (
                    imageError ? (
                      <div className="text-center text-muted-foreground">
                        <FileText className="h-16 w-16 mx-auto mb-4 opacity-50" />
                        <p>Error al cargar la imagen</p>
                      </div>
                    ) : (
                      <img
                        src={previewFile.url}
                        alt={previewFile.filename}
                        className="max-w-full max-h-[70vh] object-contain rounded-lg"
                        loading="eager"
                        onError={() => setImageError(true)}
                      />
                    )
                  ) : previewFile.type === "application/pdf" ? (
                    <iframe src={previewFile.url} className="w-full h-[70vh] rounded-lg border" title={previewFile.filename} />
                  ) : (
                    <div className="text-center text-muted-foreground">
                      <FileText className="h-16 w-16 mx-auto mb-4 opacity-50" />
                      <p>No se puede mostrar vista previa de este tipo de archivo</p>
                    </div>
                  )}
                </>
              ) : null}
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => {
                setShowPreviewDialog(false);
                if (previewFile) window.URL.revokeObjectURL(previewFile.url);
                setPreviewFile(null);
                setImageError(false);
              }}>
                Cerrar
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        <ToastContainer toasts={toasts} onRemove={removeToast} />
      </div>
    );
  }
  // ─────────────────────────────────────────────────────────────

  return (
    <div className="flex w-full flex-col bg-muted/40 p-4 md:p-10">
      <div className="flex flex-col gap-6 max-w-5xl mx-auto w-full">
        {/* Header */}
        <div className="flex items-center justify-between">
          <Button
            variant="ghost"
            onClick={() => router.push("/dashboard")}
            className="w-fit"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Volver
          </Button>

          {isCreator && isAjustesSolicitados && (
            <Button
              variant="default"
              onClick={() => router.push(`/solicitudes/${solicitud.id}/upload`)}
            >
              Subir nueva versión
            </Button>
          )}
        </div>

        {/* Main Info Card */}
        <Card>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <CardTitle className="text-2xl">{solicitud.title}</CardTitle>
                  <Badge variant={getStatusVariant(solicitud.state.code)}>
                    {solicitud.state.label}
                  </Badge>
                </div>
                <CardDescription className="text-sm text-muted-foreground">
                  Solicitud #{solicitud.id}
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Description */}
            {solicitud.description && (
              <div>
                <h3 className="font-semibold mb-2">Descripción</h3>
                <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                  {solicitud.description}
                </p>
              </div>
            )}

            {/* Info Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex items-start gap-3 p-3 rounded-lg bg-muted/50">
                <Building2 className="h-5 w-5 text-muted-foreground mt-0.5" />
                <div>
                  <p className="text-sm font-medium">Área</p>
                  <p className="text-sm text-muted-foreground">{solicitud.area.nombre}</p>
                </div>
              </div>

              <div className="flex items-start gap-3 p-3 rounded-lg bg-muted/50">
                <Workflow className="h-5 w-5 text-muted-foreground mt-0.5" />
                <div>
                  <p className="text-sm font-medium">Etapa actual</p>
                  <p className="text-sm text-muted-foreground">{solicitud.stage.label}</p>
                </div>
              </div>

              <div className="flex items-start gap-3 p-3 rounded-lg bg-muted/50">
                <User className="h-5 w-5 text-muted-foreground mt-0.5" />
                <div>
                  <p className="text-sm font-medium">Creado por</p>
                  <p className="text-sm text-muted-foreground">{solicitud.created_by.full_name}</p>
                  <p className="text-xs text-muted-foreground">{solicitud.created_by.email}</p>
                </div>
              </div>

              <div className="flex items-start gap-3 p-3 rounded-lg bg-muted/50">
                <Calendar className="h-5 w-5 text-muted-foreground mt-0.5" />
                <div>
                  <p className="text-sm font-medium">Fechas</p>
                  <p className="text-xs text-muted-foreground">
                    Creado: {formatDate(solicitud.created_at)}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Actualizado: {formatDate(solicitud.updated_at)}
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Files Card */}
        <Card>
          <CardHeader>
            <CardTitle>Archivos adjuntos</CardTitle>
            <CardDescription>
              {solicitud.files.length === 0 
                ? "No hay archivos adjuntos" 
                : `${solicitud.files.length} archivo${solicitud.files.length > 1 ? 's' : ''}`}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {solicitud.files.length > 0 ? (
              <div className="space-y-2">
                {solicitud.files.map((file) => (
                  <div
                    key={file.id}
                    className="flex items-center justify-between p-3 rounded-lg border bg-card hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      <FileText className="h-5 w-5 text-muted-foreground flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">{file.filename}</p>
                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                          <span>{formatFileSize(file.size_bytes)}</span>
                          <span>•</span>
                          <span>{file.content_type}</span>
                          {file.doc_type && (
                            <>
                              <span>•</span>
                              <span className="uppercase">{file.doc_type}</span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      {(file.content_type.startsWith('image/') || file.content_type === 'application/pdf') && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handlePreviewFile(file.id, file.filename, file.content_type)}
                          disabled={loadingPreview}
                          title="Vista previa"
                        >
                          {loadingPreview ? (
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current"></div>
                          ) : (
                            <Eye className="h-4 w-4" />
                          )}
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDownloadFile(file.id, file.filename)}
                        title="Descargar"
                      >
                        <Download className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <FileText className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>No hay archivos adjuntos en esta solicitud</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Historial de comentarios y ajustes */}
        {eventos.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Historial de comentarios</CardTitle>
              <CardDescription>
                Registro de ajustes solicitados y comentarios
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {eventos
                  .slice()
                  .reverse()
                  .map((evento) => (
                  <div
                    key={evento.id}
                    className="flex gap-3 p-4 rounded-lg border bg-muted/30"
                  >
                    <div className="flex-shrink-0">
                      <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                        <User className="h-4 w-4 text-primary" />
                      </div>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2 mb-1">
                        <div>
                          <p className="text-sm font-medium">{evento.actor.full_name}</p>
                          <p className="text-xs text-muted-foreground">{evento.actor.email}</p>
                        </div>
                        <div className="flex flex-col items-end gap-1">
                          <Badge 
                            variant={
                              evento.action === 'APPROVED' ? 'default' : 
                              evento.action === 'REQUEST_CHANGES' ? 'secondary' : 
                              evento.action === 'REJECTED' ? 'destructive' :
                              'outline'
                            } 
                            className="text-xs"
                          >
                            {evento.action === 'REQUEST_CHANGES' 
                              ? 'Ajustes solicitados' 
                              : evento.action === 'APPROVED' 
                              ? `Aprobado en ${evento.stage.label}` 
                              : evento.action === 'REJECTED'
                              ? 'Rechazado'
                              : evento.action}
                          </Badge>
                          <span className="text-xs text-muted-foreground whitespace-nowrap">
                            {formatDate(evento.created_at)}
                          </span>
                        </div>
                      </div>
                      {evento.comment && (
                        <div className="mt-2 p-3 rounded bg-background border">
                          <p className="text-sm whitespace-pre-wrap">{evento.comment}</p>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Actions/Comments Card - Solo mostrar si está en revisión (no ajustes, no aprobado, no rechazado) Y no ha aprobado ya */}
        {isApprover && !isAjustesSolicitados && !isAprobadoFinal && !isRechazado && !userAlreadyApproved && (
          <Card>
            <CardHeader>
              <CardTitle>Acciones de aprobación</CardTitle>
              <CardDescription>Revisa y aprueba o solicita ajustes</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-3">
                <Button 
                  variant="default" 
                  className="flex-1"
                  onClick={() => setShowAprobarDialog(true)}
                >
                  Aprobar solicitud
                </Button>
                <Button 
                  variant="outline" 
                  className="flex-1"
                  onClick={() => setShowAjustesDialog(true)}
                >
                  Solicitar ajustes
                </Button>
                <Button 
                  variant="destructive" 
                  className="flex-1"
                  onClick={() => setShowRechazarDialog(true)}
                >
                  Rechazar
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Mensaje cuando el usuario ya aprobó en esta etapa */}
        {isApprover && !isAjustesSolicitados && !isAprobadoFinal && !isRechazado && userAlreadyApproved && (
          <Card>
            <CardHeader>
              <CardTitle>Aprobación registrada</CardTitle>
              <CardDescription>Tu aprobación ha sido registrada para esta etapa</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-sm text-muted-foreground">
                <p>Ya has aprobado esta solicitud en la etapa actual. Si esta etapa requiere múltiples aprobaciones, la solicitud avanzará cuando todos los aprobadores hayan dado su visto bueno.</p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Mensaje cuando está en ajustes solicitados */}
        {isApprover && isAjustesSolicitados && !isAprobadoFinal && (
          <Card>
            <CardHeader>
              <CardTitle>Ajustes en proceso</CardTitle>
              <CardDescription>Esta solicitud está siendo corregida por el creador</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-sm text-muted-foreground">
                <p>La solicitud tiene ajustes pendientes. El creador debe subir una nueva versión antes de que puedas revisarla nuevamente.</p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Mensaje cuando está aprobada final */}
        {isApprover && isAprobadoFinal && (
          <Card>
            <CardHeader>
              <CardTitle>Solicitud aprobada</CardTitle>
              <CardDescription>Esta solicitud ha completado todas las etapas de aprobación</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-sm text-muted-foreground">
                <p>Esta solicitud ha sido aprobada exitosamente y ha completado todo el flujo de revisión. No requiere más acciones.</p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Mensaje cuando está rechazada */}
        {isApprover && isRechazado && (
          <Card>
            <CardHeader>
              <CardTitle>Solicitud rechazada</CardTitle>
              <CardDescription>Esta solicitud fue rechazada</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-sm text-muted-foreground">
                <p>Esta solicitud no cumplió con los requisitos y fue rechazada. Revisa el historial de comentarios para ver el motivo.</p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Diálogo para aprobar */}
        <Dialog open={showAprobarDialog} onOpenChange={setShowAprobarDialog}>
          <DialogContent className="sm:max-w-[525px]">
            <DialogHeader>
              <DialogTitle>Aprobar solicitud</DialogTitle>
              <DialogDescription>
                La solicitud avanzará a la siguiente etapa o se marcará como aprobada final.
                Opcionalmente puedes agregar un comentario.
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="aprobar-comment">
                  Comentario (opcional)
                </Label>
                <Textarea
                  id="aprobar-comment"
                  placeholder="Ej: Todo se ve bien, aprobado para continuar..."
                  value={aprobarComment}
                  onChange={(e) => setAprobarComment(e.target.value)}
                  rows={4}
                  className="resize-none"
                  disabled={submittingAprobar}
                />
                <p className="text-xs text-muted-foreground">
                  {aprobarComment.length}/1000 caracteres
                </p>
              </div>
            </div>
            <DialogFooter>
              <Button 
                variant="outline" 
                onClick={() => {
                  setShowAprobarDialog(false);
                  setAprobarComment("");
                }}
                disabled={submittingAprobar}
              >
                Cancelar
              </Button>
              <Button 
                onClick={handleAprobar}
                disabled={submittingAprobar}
              >
                {submittingAprobar ? "Aprobando..." : "Aprobar"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Diálogo para solicitar ajustes */}
        <Dialog open={showAjustesDialog} onOpenChange={setShowAjustesDialog}>
          <DialogContent className="sm:max-w-[525px]">
            <DialogHeader>
              <DialogTitle>Solicitar ajustes</DialogTitle>
              <DialogDescription>
                Explica los cambios que necesitas que el creador realice en esta solicitud.
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="ajustes-comment">
                  Comentarios sobre los ajustes necesarios *
                </Label>
                <Textarea
                  id="ajustes-comment"
                  placeholder="Ej: Por favor cambiar el color del logo a azul y ajustar el tamaño de la tipografía..."
                  value={ajustesComment}
                  onChange={(e) => setAjustesComment(e.target.value)}
                  rows={5}
                  className="resize-none"
                  disabled={submittingAjustes}
                />
                <p className="text-xs text-muted-foreground">
                  {ajustesComment.length}/1000 caracteres
                </p>
              </div>
            </div>
            <DialogFooter>
              <Button 
                variant="outline" 
                onClick={() => {
                  setShowAjustesDialog(false);
                  setAjustesComment("");
                }}
                disabled={submittingAjustes}
              >
                Cancelar
              </Button>
              <Button 
                onClick={handleSolicitarAjustes}
                disabled={submittingAjustes || !ajustesComment.trim()}
              >
                {submittingAjustes ? "Enviando..." : "Solicitar ajustes"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Diálogo para rechazar */}
        <Dialog open={showRechazarDialog} onOpenChange={setShowRechazarDialog}>
          <DialogContent className="sm:max-w-[525px]">
            <DialogHeader>
              <DialogTitle>Rechazar solicitud</DialogTitle>
              <DialogDescription>
                Explica el motivo por el cual esta solicitud no cumple con los requisitos.
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="rechazar-comment">
                  Motivo del rechazo *
                </Label>
                <Textarea
                  id="rechazar-comment"
                  placeholder="Ej: No cumple con los lineamientos de marca, colores incorrectos..."
                  value={rechazarComment}
                  onChange={(e) => setRechazarComment(e.target.value)}
                  rows={5}
                  className="resize-none"
                  disabled={submittingRechazar}
                />
                <p className="text-xs text-muted-foreground">
                  {rechazarComment.length}/1000 caracteres
                </p>
              </div>
            </div>
            <DialogFooter>
              <Button 
                variant="outline" 
                onClick={() => {
                  setShowRechazarDialog(false);
                  setRechazarComment("");
                }}
                disabled={submittingRechazar}
              >
                Cancelar
              </Button>
              <Button 
                variant="destructive"
                onClick={handleRechazar}
                disabled={submittingRechazar || !rechazarComment.trim()}
              >
                {submittingRechazar ? "Rechazando..." : "Rechazar solicitud"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Diálogo de vista previa */}
        <Dialog open={showPreviewDialog} onOpenChange={(open) => {
          setShowPreviewDialog(open);
          if (!open) {
            // Limpiar blob URL al cerrar
            if (previewFile) {
              window.URL.revokeObjectURL(previewFile.url);
            }
            setPreviewFile(null);
            setImageError(false);
          }
        }}>
          <DialogContent className="sm:max-w-[90vw] max-h-[90vh] overflow-auto">
            <DialogHeader>
              <DialogTitle>{previewFile?.filename}</DialogTitle>
              <DialogDescription>
                Vista previa del archivo
              </DialogDescription>
            </DialogHeader>
            <div className="flex items-center justify-center p-4 min-h-[400px]">
              {loadingPreview ? (
                <div className="flex flex-col items-center gap-4">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#00829a]"></div>
                  <p className="text-sm text-muted-foreground">Cargando vista previa...</p>
                </div>
              ) : previewFile ? (
                <>
                  {previewFile.type.startsWith('image/') ? (
                    imageError ? (
                      <div className="text-center text-muted-foreground">
                        <FileText className="h-16 w-16 mx-auto mb-4 opacity-50" />
                        <p>Error al cargar la imagen</p>
                        <p className="text-xs mt-2">Intenta descargar el archivo</p>
                      </div>
                    ) : (
                      <img 
                        src={previewFile.url} 
                        alt={previewFile.filename}
                        className="max-w-full max-h-[70vh] object-contain rounded-lg"
                        loading="eager"
                        onError={() => {
                          console.error("Error loading image:", previewFile.filename);
                          setImageError(true);
                        }}
                      />
                    )
                  ) : previewFile.type === 'application/pdf' ? (
                    <iframe
                      src={previewFile.url}
                      className="w-full h-[70vh] rounded-lg border"
                      title={previewFile.filename}
                    />
                  ) : (
                    <div className="text-center text-muted-foreground">
                      <FileText className="h-16 w-16 mx-auto mb-4 opacity-50" />
                      <p>No se puede mostrar vista previa de este tipo de archivo</p>
                    </div>
                  )}
                </>
              ) : null}
            </div>
            <DialogFooter>
              <Button 
                variant="outline" 
                onClick={() => {
                  setShowPreviewDialog(false);
                  // Limpiar blob URL
                  if (previewFile) {
                    window.URL.revokeObjectURL(previewFile.url);
                  }
                  setPreviewFile(null);
                  setImageError(false);
                }}
              >
                Cerrar
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      <ToastContainer toasts={toasts} onRemove={removeToast} />
      </div>
    </div>
  );
}
