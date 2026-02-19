"use client";
import React, { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, Download, FileText, Calendar, User, Building2, Workflow, Eye } from "lucide-react";
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
      
      // Cargar eventos/comentarios
      fetchEventos(token);
    } catch (err) {
      console.error("Error fetching solicitud:", err);
      setError(err instanceof Error ? err.message : "Error desconocido");
    } finally {
      setLoading(false);
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
      alert("Error al descargar el archivo. Por favor, intenta nuevamente.");
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
      alert("Error al cargar la vista previa. Por favor, intenta nuevamente.");
    } finally {
      setLoadingPreview(false);
    }
  };

  const handleSolicitarAjustes = async () => {
    if (!ajustesComment.trim()) {
      alert("Por favor, escribe un comentario explicando los ajustes necesarios");
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
      
      alert("Ajustes solicitados exitosamente. El creador ha sido notificado.");

    } catch (err) {
      console.error("Error solicitando ajustes:", err);
      alert(err instanceof Error ? err.message : "Error al solicitar ajustes");
    } finally {
      setSubmittingAjustes(false);
    }
  };

  const handleAprobar = async () => {
    setSubmittingAprobar(true);
    const token = localStorage.getItem("access_token");

    try {
      const res = await fetch(`${API_URL}/api/v1/solicitudes/${solicitudId}/aprobar`, {
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
      
      // Recargar eventos para mostrar el nuevo comentario
      fetchEventos(token!);
      
      // Mensaje según el nuevo estado
      if (updatedSolicitud.state.code === "APROBADO_FINAL") {
        alert("Solicitud aprobada exitosamente. La solicitud ha completado todas las etapas.");
      } else {
        alert(`Solicitud aprobada y avanzada a la siguiente etapa: ${updatedSolicitud.stage.label}`);
      }

    } catch (err) {
      console.error("Error aprobando solicitud:", err);
      alert(err instanceof Error ? err.message : "Error al aprobar solicitud");
    } finally {
      setSubmittingAprobar(false);
    }
  };

  const handleRechazar = async () => {
    if (!rechazarComment.trim()) {
      alert("Por favor, escribe el motivo del rechazo");
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
      
      alert("Solicitud rechazada. El creador ha sido notificado.");

    } catch (err) {
      console.error("Error rechazando solicitud:", err);
      alert(err instanceof Error ? err.message : "Error al rechazar solicitud");
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
      </div>
    </div>
  );
}
