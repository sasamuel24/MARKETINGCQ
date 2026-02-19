"use client";
import React, { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ArrowLeft, Upload, X, FileText } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface SolicitudBasic {
  id: number;
  title: string;
  state: {
    code: string;
    label: string;
  };
}

export default function UploadNewVersionPage() {
  const router = useRouter();
  const params = useParams();
  const solicitudId = params?.id as string;

  const [solicitud, setSolicitud] = useState<SolicitudBasic | null>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/login");
      return;
    }

    // Fetch solicitud básica
    fetch(`${API_URL}/api/v1/solicitudes/${solicitudId}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => {
        if (!res.ok) throw new Error("Error al cargar solicitud");
        return res.json();
      })
      .then((data) => {
        setSolicitud(data);
        
        // Verificar que esté en estado de ajustes solicitados
        if (data.state.code !== "AJUSTES_SOLICITADOS") {
          setError("Esta solicitud no está en estado de ajustes solicitados");
        }
      })
      .catch((err) => {
        console.error(err);
        setError("Error al cargar la solicitud");
      });
  }, [solicitudId, router]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const newFiles = Array.from(e.target.files);
      setFiles((prev) => [...prev, ...newFiles]);
    }
  };

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async () => {
    if (files.length === 0) {
      alert("Por favor selecciona al menos un archivo");
      return;
    }

    setUploading(true);
    const token = localStorage.getItem("access_token");

    try {
      // 1. Subir archivos directamente a S3 con presigned URLs (evita límite 10MB de API Gateway)
      const { uploadFilesWithPresignedUrl } = await import("@/lib/uploadFiles");
      await uploadFilesWithPresignedUrl(API_URL, token!, parseInt(solicitudId), files, "ARTE");

      // 2. Cambiar estado de vuelta a EN_REVISION
      const updateRes = await fetch(`${API_URL}/api/v1/solicitudes/${solicitudId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          status_id: 1, // EN_REVISION
        }),
      });

      if (!updateRes.ok) {
        throw new Error("Error al actualizar estado");
      }

      alert("Archivos subidos exitosamente. La solicitud ha sido enviada nuevamente para revisión.");
      router.push(`/solicitudes/${solicitudId}`);

    } catch (err) {
      console.error("Error:", err);
      alert(err instanceof Error ? err.message : "Error al subir archivos");
    } finally {
      setUploading(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  if (error) {
    return (
      <div className="flex w-full flex-col bg-muted/40 p-4 md:p-10">
        <div className="flex flex-col gap-6 max-w-3xl mx-auto w-full">
          <Button
            variant="ghost"
            onClick={() => router.push(`/solicitudes/${solicitudId}`)}
            className="w-fit"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Volver
          </Button>
          <Card>
            <CardHeader>
              <CardTitle>Error</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-red-500">{error}</p>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  if (!solicitud) {
    return (
      <div className="flex w-full flex-col bg-muted/40 p-4 md:p-10">
        <div className="p-8 text-center">Cargando...</div>
      </div>
    );
  }

  return (
    <div className="flex w-full flex-col bg-muted/40 p-4 md:p-10">
      <div className="flex flex-col gap-6 max-w-3xl mx-auto w-full">
        {/* Header */}
        <Button
          variant="ghost"
          onClick={() => router.push(`/solicitudes/${solicitudId}`)}
          className="w-fit"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Volver
        </Button>

        {/* Main Card */}
        <Card>
          <CardHeader>
            <CardTitle>Subir nueva versión</CardTitle>
            <CardDescription>
              {solicitud.title} - Solicitud #{solicitud.id}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="p-4 rounded-lg bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-900">
              <p className="text-sm text-blue-900 dark:text-blue-100">
                Esta solicitud tiene ajustes pendientes. Sube los archivos corregidos y la solicitud será enviada automáticamente para revisión nuevamente.
              </p>
            </div>

            {/* File Upload Area */}
            <div>
              <label
                htmlFor="file-upload"
                className="flex flex-col items-center justify-center w-full h-48 border-2 border-dashed rounded-lg cursor-pointer hover:bg-muted/50 transition-colors"
              >
                <div className="flex flex-col items-center justify-center pt-5 pb-6">
                  <Upload className="h-10 w-10 mb-3 text-muted-foreground" />
                  <p className="mb-2 text-sm text-muted-foreground">
                    <span className="font-semibold">Click para seleccionar archivos</span> o arrastra y suelta
                  </p>
                  <p className="text-xs text-muted-foreground">
                    PDF, PNG, JPG (Max 50MB por archivo)
                  </p>
                </div>
                <input
                  id="file-upload"
                  type="file"
                  className="hidden"
                  multiple
                  accept=".pdf,.png,.jpg,.jpeg"
                  onChange={handleFileChange}
                  disabled={uploading}
                />
              </label>
            </div>

            {/* File List */}
            {files.length > 0 && (
              <div className="space-y-2">
                <h3 className="text-sm font-medium">
                  Archivos seleccionados ({files.length})
                </h3>
                {files.map((file, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 rounded-lg border bg-card"
                  >
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      <FileText className="h-5 w-5 text-muted-foreground flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">{file.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {formatFileSize(file.size)}
                        </p>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeFile(index)}
                      disabled={uploading}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-3 pt-4">
              <Button
                variant="outline"
                onClick={() => router.push(`/solicitudes/${solicitudId}`)}
                disabled={uploading}
                className="flex-1"
              >
                Cancelar
              </Button>
              <Button
                onClick={handleSubmit}
                disabled={files.length === 0 || uploading}
                className="flex-1"
              >
                {uploading ? "Subiendo..." : "Subir y enviar para revisión"}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
