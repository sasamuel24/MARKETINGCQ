"use client";
import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Upload, FileText, X } from "lucide-react";
import { ToastContainer, ToastData } from "@/components/ui/toast-simple";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  rol_id: number;
}

interface Estado {
  id: number;
  code: string;
  label: string;
  order: number;
}

interface Area {
  id: number;
  nombre: string;
}

interface Solicitud {
  id: number;
  title: string;
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
  };
  area: {
    id: number;
    nombre: string;
  };
}

interface Etapa {
  id: number;
  code: string;
  label: string;
  order: number;
  area_id: number;
}

interface NewSolicitudForm {
  nombre_arte: string;
  descripcion: string;
  area_id: string;
  files: File[];
}

export default function Dashboard() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [solicitudes, setSolicitudes] = useState<Solicitud[]>([]);
  const [allSolicitudes, setAllSolicitudes] = useState<Solicitud[]>([]); // Para APPROVERS: todas las solicitudes
  const [areas, setAreas] = useState<Area[]>([]);
  const [estados, setEstados] = useState<Estado[]>([]);
  const [etapas, setEtapas] = useState<Etapa[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [areaFilter, setAreaFilter] = useState("ALL");
  
  // Filtros para tabla global de seguimiento
  const [globalSearchTerm, setGlobalSearchTerm] = useState("");
  const [globalStatusFilter, setGlobalStatusFilter] = useState("ALL");
  const [globalAreaFilter, setGlobalAreaFilter] = useState("ALL");
  
  // Form state for CREATOR
  const [formData, setFormData] = useState<NewSolicitudForm>({
    nombre_arte: "",
    descripcion: "",
    area_id: "",
    files: []
  });
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [toasts, setToasts] = useState<ToastData[]>([]);

  const showToast = (message: string, type: "success" | "error" = "success") => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message, type }]);
  };

  const removeToast = (id: number) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  };

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/login");
      return;
    }
    fetch(`${API_URL}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => {
        if (!res.ok) throw new Error("Unauthorized");
        return res.json();
      })
      .then((userData) => {
        setUser(userData);
        fetchSolicitudes(userData, token);
        fetchAreas(token);
        fetchEstados(token);
        fetchEtapas(token);
      })
      .catch(() => router.push("/login"));
  }, [router]);

  const fetchAreas = async (token: string) => {
    try {
      const res = await fetch(`${API_URL}/api/v1/areas`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setAreas(data.areas || []);
      }
    } catch (err) {
      console.error("Error fetching areas:", err);
    }
  };

  const fetchEstados = async (token: string) => {
    try {
      const res = await fetch(`${API_URL}/api/v1/estados`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setEstados(data.estados || []);
      }
    } catch (err) {
      console.error("Error fetching estados:", err);
    }
  };

  const fetchEtapas = async (token: string) => {
    try {
      const res = await fetch(`${API_URL}/api/v1/etapas`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setEtapas(data.etapas || []);
      }
    } catch (err) {
      console.error("Error fetching etapas:", err);
    }
  };

  const fetchSolicitudes = async (currentUser: User, token: string, silent = false) => {
    if (!silent) setLoading(true);
    let url = `${API_URL}/api/v1/solicitudes?page=1&page_size=100`;
    if (currentUser.role === "APPROVER" || currentUser.rol_id === 3) {
      // Filtrar solo solicitudes pendientes de aprobación (no incluir APROBADO_FINAL ni RECHAZADO)
      url += "&check_approver=true&status_id=1";
      // También cargar todas las solicitudes para seguimiento global
      fetchAllSolicitudes(token);
    } else {
      url += `&created_by_user_id=${currentUser.id}`;
    }
    try {
      const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) {
        const data = await res.json();
        setSolicitudes(data.solicitudes || []);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchAllSolicitudes = async (token: string) => {
    try {
      const url = `${API_URL}/api/v1/solicitudes?page=1&page_size=100`;
      console.log("Fetching all solicitudes from:", url);
      const res = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` }
      });
      console.log("Response status:", res.status);
      if (res.ok) {
        const data = await res.json();
        console.log("Solicitudes loaded:", data.solicitudes?.length, "of", data.total);
        setAllSolicitudes(data.solicitudes || []);
      } else {
        const errorText = await res.text();
        console.error("Error response:", errorText);
      }
    } catch (err) {
      console.error("Error fetching all solicitudes:", err);
    }
  };

  const filteredSolicitudes = solicitudes.filter((sol) => {
    const matchesSearch = sol.title.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === "ALL" || sol.state.id === parseInt(statusFilter);
    const matchesArea = areaFilter === "ALL" || sol.area.id === parseInt(areaFilter);
    return matchesSearch && matchesStatus && matchesArea;
  });

  const filteredAllSolicitudes = allSolicitudes.filter((sol) => {
    const matchesSearch = sol.title.toLowerCase().includes(globalSearchTerm.toLowerCase());
    const matchesStatus = globalStatusFilter === "ALL" || sol.state.id === parseInt(globalStatusFilter);
    const matchesArea = globalAreaFilter === "ALL" || sol.area.id === parseInt(globalAreaFilter);
    return matchesSearch && matchesStatus && matchesArea;
  });

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("es-ES", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  };

  const getStatusVariant = (code: string): "default" | "secondary" | "destructive" | "outline" => {
    if (code === "APROBADO" || code === "APPROVED") return "default";
    if (code === "RECHAZADO" || code === "REJECTED") return "destructive";
    if (code === "PENDIENTE" || code === "PENDING") return "secondary";
    return "outline";
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    const errors: Record<string, string> = {};
    
    // Validate file size (max 10MB per file)
    const invalidFiles = files.filter(f => f.size > 10 * 1024 * 1024);
    if (invalidFiles.length > 0) {
      errors.files = "Algunos archivos exceden el límite de 10MB";
      setFormErrors(errors);
      return;
    }
    
    setFormData(prev => ({ ...prev, files }));
    setFormErrors(prev => ({ ...prev, files: "" }));
  };

  const removeFile = (index: number) => {
    setFormData(prev => ({
      ...prev,
      files: prev.files.filter((_, i) => i !== index)
    }));
  };

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};
    
    if (!formData.nombre_arte.trim()) {
      errors.nombre_arte = "El nombre del arte es requerido";
    } else if (formData.nombre_arte.length > 80) {
      errors.nombre_arte = "El nombre no puede exceder 80 caracteres";
    }
    
    if (!formData.area_id) {
      errors.area_id = "Debe seleccionar un área";
    }
    
    if (formData.descripcion.length > 500) {
      errors.descripcion = "La descripción no puede exceder 500 caracteres";
    }
    
    if (formData.files.length === 0) {
      errors.files = "Debe adjuntar al menos un archivo";
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) return;
    
    setSubmitting(true);
    const token = localStorage.getItem("access_token");
    
    try {
      // Get first etapa by order for the selected area
      const areaId = parseInt(formData.area_id);
      const firstEtapa = etapas.find(etapa => 
        etapa.area_id === areaId && etapa.order === 1
      );
      
      // Get pending estado (try multiple codes)
      const pendingEstado = estados.find(estado => 
        estado.code === "PENDIENTE" || 
        estado.code === "EN_REVISION" ||
        estado.code === "PENDING" ||
        estado.order === 1
      ) || estados[0];
      
      console.log("Etapas disponibles:", etapas);
      console.log("Estados disponibles:", estados);
      console.log("Área seleccionada:", areaId);
      console.log("Primera etapa encontrada:", firstEtapa);
      console.log("Estado pendiente encontrado:", pendingEstado);
      
      if (!firstEtapa || !pendingEstado) {
        showToast("Error: No se encontró la configuración inicial. Verifica que existan etapas y estados en el sistema.", "error");
        setSubmitting(false);
        return;
      }
      
      // Create solicitud
      const solicitudData = {
        title: formData.nombre_arte,
        description: formData.descripcion || undefined,
        area_id: areaId,
        stage_id: firstEtapa.id,
        status_id: pendingEstado.id
      };
      
      console.log("Enviando solicitud:", solicitudData);
      
      const res = await fetch(`${API_URL}/api/v1/solicitudes`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(solicitudData)
      });
      
      console.log("Respuesta del servidor:", res.status, res.statusText);
      
      if (!res.ok) {
        const errorData = await res.json();
        console.error("Error del servidor:", errorData);
        throw new Error(errorData.detail || "Error al crear solicitud");
      }
      
      const newSolicitud = await res.json();
      console.log("Solicitud creada exitosamente:", newSolicitud);
      
      // Upload files directamente a S3 con presigned URLs (evita límite 10MB de API Gateway)
      if (formData.files.length > 0) {
        console.log("Subiendo archivos a S3 via presigned URL...");
        const { uploadFilesWithPresignedUrl } = await import("@/lib/uploadFiles");
        await uploadFilesWithPresignedUrl(API_URL, token!, newSolicitud.id, formData.files, "ARTE");
        console.log("Archivos subidos exitosamente");
      }
      
      // Refresh solicitudes list (silent: no mostrar pantalla en blanco)
      if (user) {
        await fetchSolicitudes(user, token!, true);
      }
      
      // Reset form including file input
      setFormData({
        nombre_arte: "",
        descripcion: "",
        area_id: "",
        files: []
      });
      
      // Reset file input element
      const fileInput = document.getElementById("files") as HTMLInputElement;
      if (fileInput) fileInput.value = "";
      
      showToast(`✓ Solicitud #${newSolicitud.id} creada — "${newSolicitud.title}" · ${formData.files.length} archivo(s) subido(s)`);
      
    } catch (error) {
      console.error("Error creating solicitud:", error);
      showToast(error instanceof Error ? error.message : "Error al crear la solicitud", "error");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <div className="p-8">Cargando...</div>;
  if (!user) return null;

  // Debug: Log user data to console
  console.log("User data:", user);

  const isApprover = user.role === "APPROVER" || user.rol_id === 3;
  const isCreator = user.role === "CREATOR" || user.rol_id === 2;

  return (
    <div className="flex w-full flex-col min-h-screen">
      {/* Header con fondo de marca */}
      <div 
        className="relative w-full"
        style={{
          backgroundImage: 'url(/plameras%20beige.jpg)',
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundRepeat: 'no-repeat'
        }}
      >
        <div className="absolute inset-0 bg-gradient-to-br from-[#00829a]/85 via-[#00a3b4]/75 to-[#90cde3]/65"></div>
        <div className="relative z-10 px-4 md:px-10 py-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl md:text-4xl font-bold text-white drop-shadow-lg">
                CAFÉ QUINDÍO
              </h1>
              <p className="text-white/90 text-sm md:text-base mt-1">
                Sistema de Gestión de Marketing
              </p>
              <div className="mt-4 flex items-center gap-3">
                <div className="bg-white/20 backdrop-blur-sm rounded-full px-4 py-1.5">
                  <p className="text-white text-sm font-medium">
                    {user.full_name}
                  </p>
                </div>
                <div className="bg-[#96c121] rounded-full px-4 py-1.5">
                  <p className="text-white text-sm font-semibold">
                    {isApprover ? "Aprobador" : "Creador"}
                  </p>
                </div>
              </div>
            </div>
            <Button 
              className="bg-white/20 hover:bg-white/30 text-white border-white/30 backdrop-blur-sm"
              variant="outline" 
              onClick={() => {
                localStorage.clear();
                router.push("/login");
              }}
            >
              Cerrar sesión
            </Button>
          </div>
        </div>
      </div>

      {/* Contenido principal */}
      <div className="flex-1 bg-gradient-to-br from-gray-50 to-gray-100 p-4 md:p-10">
        <div className="flex flex-col gap-6">
          {isCreator ? (
          <>
            {/* CREATOR VIEW: New Solicitud Form */}
            <Card className="shadow-lg border-0 overflow-hidden">
              <div className="bg-gradient-to-r from-[#00829a] to-[#00a3b4] px-6 py-4">
                <CardTitle className="text-white text-xl font-bold">Nueva solicitud</CardTitle>
                <CardDescription className="text-white/90 font-normal">
                  Crear una nueva solicitud de arte
                </CardDescription>
              </div>
              <CardContent className="pt-6">
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="grid gap-4 md:grid-cols-2">
                    {/* Nombre del arte */}
                    <div className="space-y-2">
                      <Label htmlFor="nombre_arte" className="font-medium">Nombre del arte *</Label>
                      <Input
                        id="nombre_arte"
                        placeholder="Ej: Banner campaña verano 2026"
                        value={formData.nombre_arte}
                        onChange={(e) => setFormData(prev => ({ ...prev, nombre_arte: e.target.value }))}
                        maxLength={80}
                        className={formErrors.nombre_arte ? "border-red-500" : ""}
                      />
                      {formErrors.nombre_arte && (
                        <p className="text-sm text-red-500">{formErrors.nombre_arte}</p>
                      )}
                      <p className="text-xs text-muted-foreground">
                        {formData.nombre_arte.length}/80 caracteres
                      </p>
                    </div>

                    {/* Área */}
                    <div className="space-y-2">
                      <Label htmlFor="area_id" className="font-medium">Área *</Label>
                      <select
                        id="area_id"
                        value={formData.area_id}
                        onChange={(e) => setFormData(prev => ({ ...prev, area_id: e.target.value }))}
                        className={`h-10 w-full rounded-md border-2 ${formErrors.area_id ? "border-red-500" : "border-input"} bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/20 transition-colors appearance-none cursor-pointer`}
                        style={{
                          backgroundImage: `url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%2300829a' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e")`,
                          backgroundPosition: 'right 0.5rem center',
                          backgroundRepeat: 'no-repeat',
                          backgroundSize: '1.5em 1.5em',
                          paddingRight: '2.5rem'
                        }}
                      >
                        <option value="" style={{ backgroundColor: 'white' }}>Seleccionar área</option>
                        {areas.map((area) => (
                          <option 
                            key={area.id} 
                            value={area.id.toString()} 
                            className="py-2"
                            style={{ 
                              backgroundColor: 'white',
                            }}
                          >
                            {area.nombre}
                          </option>
                        ))}
                      </select>
                      {formErrors.area_id && (
                        <p className="text-sm text-red-500">{formErrors.area_id}</p>
                      )}
                    </div>
                  </div>

                  {/* Descripción */}
                  <div className="space-y-2">
                    <Label htmlFor="descripcion" className="font-medium">Descripción</Label>
                    <textarea
                      id="descripcion"
                      placeholder="Detalles adicionales sobre la solicitud..."
                      value={formData.descripcion}
                      onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setFormData(prev => ({ ...prev, descripcion: e.target.value }))}
                      maxLength={500}
                      rows={4}
                      className={`w-full min-w-0 rounded-md border bg-transparent px-3 py-2 text-base shadow-xs transition-[color,box-shadow] outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] disabled:cursor-not-allowed disabled:opacity-50 md:text-sm ${formErrors.descripcion ? "border-red-500" : "border-input"}`}
                    />
                    {formErrors.descripcion && (
                      <p className="text-sm text-red-500">{formErrors.descripcion}</p>
                    )}
                    <p className="text-xs text-muted-foreground">
                      {formData.descripcion.length}/500 caracteres
                    </p>
                  </div>

                  {/* File Upload */}
                  <div className="space-y-2">
                    <Label htmlFor="files" className="font-medium">Archivos adjuntos *</Label>
                    <div className="flex items-center gap-2">
                      <Input
                        id="files"
                        type="file"
                        multiple
                        accept="image/*,.pdf"
                        onChange={handleFileChange}
                        className="hidden"
                      />
                      <Button
                        type="button"
                        onClick={() => document.getElementById("files")?.click()}
                        className="w-full bg-secondary hover:bg-secondary/90 text-white"
                      >
                        <Upload className="mr-2 h-4 w-4" />
                        Seleccionar archivos
                      </Button>
                    </div>
                    {formErrors.files && (
                      <p className="text-sm text-red-500">{formErrors.files}</p>
                    )}
                    <p className="text-xs text-muted-foreground">
                      Imágenes o PDF. Máximo 10MB por archivo.
                    </p>

                    {/* File list */}
                    {formData.files.length > 0 && (
                      <div className="mt-2 space-y-2">
                        {formData.files.map((file, index) => (
                          <div
                            key={index}
                            className="flex items-center justify-between rounded-md border p-2"
                          >
                            <div className="flex items-center gap-2">
                              <FileText className="h-4 w-4 text-muted-foreground" />
                              <span className="text-sm">{file.name}</span>
                              <span className="text-xs text-muted-foreground">
                                ({(file.size / 1024).toFixed(1)} KB)
                              </span>
                            </div>
                            <Button
                              type="button"
                              variant="ghost"
                              size="sm"
                              onClick={() => removeFile(index)}
                            >
                              <X className="h-4 w-4" />
                            </Button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  <Button 
                    type="submit" 
                    disabled={submitting} 
                    className="w-full bg-primary hover:bg-primary/90 text-white font-bold py-5 shadow-lg hover:shadow-xl transition-all duration-200"
                  >
                    {submitting ? "Creando solicitud..." : "Crear solicitud"}
                  </Button>
                </form>
              </CardContent>
            </Card>

            {/* CREATOR VIEW: My Solicitudes Table */}
            <Card className="shadow-lg border-0 overflow-hidden">
              <div className="bg-[#00829a] px-6 py-4">
                <CardTitle className="text-white text-xl font-bold">Mis solicitudes</CardTitle>
                <CardDescription className="text-white/90 font-normal">
                  {solicitudes.length === 0
                    ? "No tienes solicitudes creadas."
                    : `Tienes ${solicitudes.length} solicitudes.`}
                </CardDescription>
              </div>
              <CardContent className="pt-6">
                {solicitudes.length > 0 ? (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>ID</TableHead>
                        <TableHead>Nombre del arte</TableHead>
                        <TableHead>Estado</TableHead>
                        <TableHead>Etapa actual</TableHead>
                        <TableHead>Última actualización</TableHead>
                        <TableHead className="text-right">Acciones</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {solicitudes
                        .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
                        .map((sol) => {
                          const isAjustesSolicitados = sol.state.code === "AJUSTES_SOLICITADOS" || 
                                                       sol.state.label === "Ajustes solicitados";
                          
                          return (
                            <TableRow key={sol.id}>
                              <TableCell className="font-mono text-sm">{sol.id}</TableCell>
                              <TableCell className="font-medium">{sol.title}</TableCell>
                              <TableCell>
                                <Badge variant={getStatusVariant(sol.state.code)}>
                                  {sol.state.label}
                                </Badge>
                              </TableCell>
                              <TableCell>{sol.stage.label}</TableCell>
                              <TableCell>{formatDate(sol.updated_at)}</TableCell>
                              <TableCell className="text-right">
                                <div className="flex justify-end gap-2">
                                  <Button
                                    className="bg-primary hover:bg-primary/90 text-white"
                                    size="sm"
                                    onClick={() => router.push(`/solicitudes/${sol.id}`)}
                                  >
                                    Ver detalle
                                  </Button>
                                  {isAjustesSolicitados && (
                                    <Button
                                      className="bg-[#96c121] hover:bg-[#96c121]/90 text-white"
                                      size="sm"
                                      onClick={() => router.push(`/solicitudes/${sol.id}/upload`)}
                                    >
                                      Subir nueva versión
                                    </Button>
                                  )}
                                </div>
                              </TableCell>
                            </TableRow>
                          );
                        })}
                    </TableBody>
                  </Table>
                ) : (
                  <div className="flex h-40 items-center justify-center text-muted-foreground">
                    No tienes solicitudes creadas aún. Usa el formulario de arriba para crear una.
                  </div>
                )}
              </CardContent>
            </Card>
          </>
        ) : isApprover ? (
          <>
            <Card className="shadow-lg border-0 overflow-hidden">
              <div className="bg-gradient-to-r from-[#00829a] to-[#00a3b4] px-6 py-4">
                <CardTitle className="text-white text-xl font-bold">Solicitudes por aprobar</CardTitle>
                <CardDescription className="text-white/90 font-normal">
                  {solicitudes.length === 0
                    ? "No tienes aprobaciones pendientes."
                    : `Tienes ${solicitudes.length} solicitudes pendientes.`}
                </CardDescription>
              </div>
              <CardContent className="pt-6">
                {solicitudes.length > 0 ? (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Nombre del arte</TableHead>
                        <TableHead>Fecha creación</TableHead>
                        <TableHead>Área</TableHead>
                        <TableHead>Etapa actual</TableHead>
                        <TableHead>Estado</TableHead>
                        <TableHead className="text-right">Acciones</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {solicitudes.map((sol) => (
                        <TableRow key={sol.id}>
                          <TableCell className="font-medium">{sol.title}</TableCell>
                          <TableCell>{formatDate(sol.created_at)}</TableCell>
                          <TableCell>{sol.area.nombre}</TableCell>
                          <TableCell>{sol.stage.label}</TableCell>
                          <TableCell>
                            <Badge variant={getStatusVariant(sol.state.code)}>
                              {sol.state.label}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-right">
                            <Button 
                              className="bg-primary hover:bg-primary/90 text-white" 
                              size="sm" 
                              onClick={() => router.push(`/solicitudes/${sol.id}`)}
                            >
                              Ver detalle
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                ) : (
                  <div className="flex h-40 items-center justify-center text-muted-foreground">
                    No se encontraron resultados
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Tabla global de seguimiento para APPROVERS */}
            <Card className="shadow-lg border-0 overflow-hidden">
              <div className="bg-[#00829a] px-6 py-4">
                <CardTitle className="text-white text-xl">Seguimiento global de solicitudes</CardTitle>
                <CardDescription className="text-white/90">
                  {allSolicitudes.length === 0
                    ? "No hay solicitudes en el sistema."
                    : `${filteredAllSolicitudes.length} de ${allSolicitudes.length} solicitudes.`}
                </CardDescription>
              </div>
              <CardContent className="pt-6">
                <div className="flex flex-col md:flex-row gap-4 mb-4">
                  <Input
                    className="md:w-1/3"
                    placeholder="Buscar por nombre..."
                    value={globalSearchTerm}
                    onChange={(e) => setGlobalSearchTerm(e.target.value)}
                  />
                  <select
                    className="md:w-1/4 h-10 rounded-md border-2 border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/20 transition-colors appearance-none cursor-pointer"
                    value={globalStatusFilter}
                    onChange={(e) => setGlobalStatusFilter(e.target.value)}
                    style={{
                      backgroundImage: `url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%2300829a' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e")`,
                      backgroundPosition: 'right 0.5rem center',
                      backgroundRepeat: 'no-repeat',
                      backgroundSize: '1.5em 1.5em',
                      paddingRight: '2.5rem'
                    }}
                  >
                    <option value="ALL" style={{ backgroundColor: 'white' }}>Todos los estados</option>
                    {estados.map((estado) => (
                      <option key={estado.id} value={estado.id} style={{ backgroundColor: 'white' }}>
                        {estado.label}
                      </option>
                    ))}
                  </select>
                  <select
                    className="md:w-1/4 h-10 rounded-md border-2 border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/20 transition-colors appearance-none cursor-pointer"
                    value={globalAreaFilter}
                    onChange={(e) => setGlobalAreaFilter(e.target.value)}
                    style={{
                      backgroundImage: `url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%2300829a' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3e%3c/svg%3e")`,
                      backgroundPosition: 'right 0.5rem center',
                      backgroundRepeat: 'no-repeat',
                      backgroundSize: '1.5em 1.5em',
                      paddingRight: '2.5rem'
                    }}
                  >
                    <option value="ALL" style={{ backgroundColor: 'white' }}>Todas las áreas</option>
                    {areas.map((area) => (
                      <option key={area.id} value={area.id} style={{ backgroundColor: 'white' }}>
                        {area.nombre}
                      </option>
                    ))}
                  </select>
                </div>

                {filteredAllSolicitudes.length > 0 ? (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>ID</TableHead>
                        <TableHead>Nombre del arte</TableHead>
                        <TableHead>Estado</TableHead>
                        <TableHead>Etapa actual</TableHead>
                        <TableHead>Área</TableHead>
                        <TableHead>Última actualización</TableHead>
                        <TableHead className="text-right">Acciones</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredAllSolicitudes
                        .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
                        .map((sol) => (
                        <TableRow key={sol.id}>
                          <TableCell className="font-mono text-sm">{sol.id}</TableCell>
                          <TableCell className="font-medium">{sol.title}</TableCell>
                          <TableCell>
                            <Badge variant={getStatusVariant(sol.state.code)}>
                              {sol.state.label}
                            </Badge>
                          </TableCell>
                          <TableCell>{sol.stage.label}</TableCell>
                          <TableCell>{sol.area.nombre}</TableCell>
                          <TableCell>{formatDate(sol.updated_at)}</TableCell>
                          <TableCell className="text-right">
                            <Button 
                              className="bg-primary hover:bg-primary/90 text-white" 
                              size="sm" 
                              onClick={() => router.push(`/solicitudes/${sol.id}`)}
                            >
                              Ver detalle
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                ) : (
                  <div className="flex h-40 items-center justify-center text-muted-foreground">
                    No se encontraron resultados
                  </div>
                )}
              </CardContent>
            </Card>
          </>
        ) : (
          <Card>
            <CardHeader>
              <CardTitle>Hola, {user.full_name}</CardTitle>
              <CardDescription>Rol no reconocido</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                Tu rol actual: {user.role} (ID: {user.rol_id})
              </p>
            </CardContent>
          </Card>
        )}
        </div>
      </div>
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </div>
  );
}
