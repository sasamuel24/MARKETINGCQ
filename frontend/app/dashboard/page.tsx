"use client";
import React, { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Upload, FileText, X, Lightbulb, Plus, Search, ChevronRight } from "lucide-react";
import { ToastContainer, ToastData } from "@/components/ui/toast-simple";
import { NotificationBell } from "@/components/ui/notification-bell";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  rol_id: number;
  area_id?: number;
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

interface Iniciativa {
  id: number;
  titulo: string;
  producto_propuesto: string;
  analisis_competencia?: string;
  business_case_path?: string;
  status: string;
  solicitud_id?: number;
  solicitud_innovacion_id?: number;
  created_at: string;
  updated_at: string;
  created_by?: { id: number; full_name: string };
}

const INI_STATUS_CONFIG: Record<string, { label: string; color: string; step: number }> = {
  BORRADOR:                  { label: "Borrador",          color: "bg-gray-100 text-gray-600 border-gray-200",      step: 1 },
  APROBADA_GG:               { label: "En Prototipado",    color: "bg-purple-100 text-purple-700 border-purple-200", step: 2 },
  EN_PROTOTIPADO:            { label: "En Prototipado",    color: "bg-purple-100 text-purple-700 border-purple-200", step: 2 },
  PENDIENTE_APROBACION_DUAL: { label: "Aprobación Dual",   color: "bg-orange-100 text-orange-700 border-orange-200", step: 3 },
  PENDIENTE_JD:              { label: "Junta Directiva",   color: "bg-indigo-100 text-indigo-700 border-indigo-200", step: 4 },
  APROBADA_JD:               { label: "Aprobada",          color: "bg-green-100 text-green-700 border-green-200",    step: 5 },
  RECHAZADA_JD:              { label: "Rechazada",         color: "bg-red-100 text-red-700 border-red-200",          step: 0 },
};

const INI_STEPS = ["Borrador", "Prototipado", "Aprobación Dual", "Junta Directiva", "Aprobada"];

interface NewSolicitudForm {
  nombre_arte: string;
  descripcion: string;
  area_id: string;
  es_para_cafe: "" | "si" | "no";
  es_para_exportacion: "" | "si" | "no";
  files: File[];
  categoria: "" | "reposteria" | "bebidas";
}

export default function Dashboard() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const vincularIniciativaId = searchParams?.get("vincular_iniciativa");
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

  // Director: iniciativas
  const [iniciativas, setIniciativas] = useState<Iniciativa[]>([]);
  const [iniSearch, setIniSearch] = useState("");
  const [iniStatusFilter, setIniStatusFilter] = useState("ALL");
  
  // Form state for CREATOR
  const [formData, setFormData] = useState<NewSolicitudForm>({
    nombre_arte: "",
    descripcion: "",
    area_id: "",
    es_para_cafe: "",
    es_para_exportacion: "",
    files: [],
    categoria: ""
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
    let currentUser: User | null = null;
    fetch(`${API_URL}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => {
        if (!res.ok) throw new Error("Unauthorized");
        return res.json();
      })
      .then((userData) => {
        currentUser = userData;
        setUser(userData);
        fetchSolicitudes(userData, token);
        fetchAreas(token);
        fetchEstados(token);
        fetchEtapas(token);
        if (userData.role === "DIRECTOR" || (userData.rol_id === 2 && userData.area_id === 4)) fetchIniciativas(token);
      })
      .catch(() => router.push("/login"));

    // Auto-refresh solicitudes cada 30s para recibir solicitudes auto-creadas (ej. desde Iniciativas)
    const interval = setInterval(() => {
      const t = localStorage.getItem("access_token");
      if (t && currentUser) fetchSolicitudes(currentUser, t, true);
    }, 30000);
    return () => clearInterval(interval);
  }, [router]);

  const fetchIniciativas = async (token: string) => {
    try {
      const res = await fetch(`${API_URL}/api/v1/iniciativas?page_size=100`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setIniciativas(data.iniciativas || []);
      }
    } catch (err) {
      console.error("Error fetching iniciativas:", err);
    }
  };

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
      const res = await fetch(`${API_URL}/api/v1/etapas?page_size=100`, {
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
      // check_approver filtra por etapa del aprobador; excluimos terminales en el frontend
      url += "&check_approver=true";
      // También cargar todas las solicitudes para seguimiento global
      fetchAllSolicitudes(token);
    } else {
      url += `&created_by_user_id=${currentUser.id}`;
      // Creadores de PRODUCCION_BEBIDAS_PASTELERIA también ven el seguimiento global
      if (currentUser.area_id === 4) {
        fetchAllSolicitudes(token);
      }
    }
    try {
      const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) {
        const data = await res.json();
        let solList: Solicitud[] = data.solicitudes || [];

        // Para CREATORs: también cargar solicitudes del área (incluye las auto-creadas desde Iniciativas)
        if (currentUser.rol_id === 2 && currentUser.area_id) {
          try {
            const areaRes = await fetch(`${API_URL}/api/v1/solicitudes/area/${currentUser.area_id}`, {
              headers: { Authorization: `Bearer ${token}` },
            });
            if (areaRes.ok) {
              const areaData = await areaRes.json();
              const areaSols: Solicitud[] = areaData.solicitudes || areaData || [];
              // Merge sin duplicados
              const ids = new Set(solList.map((s) => s.id));
              areaSols.forEach((s) => { if (!ids.has(s.id)) solList.push(s); });
            }
          } catch {}
        }

        setSolicitudes(solList);
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

  const TERMINAL_STATES = ["APROBADO_FINAL", "RECHAZADO"];
  const filteredSolicitudes = solicitudes.filter((sol) => {
    if (TERMINAL_STATES.includes(sol.state.code)) return false;
    const matchesSearch = sol.title.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === "ALL" || sol.state.id === parseInt(statusFilter);
    const matchesArea = areaFilter === "ALL" || sol.area.id === parseInt(areaFilter);
    return matchesSearch && matchesStatus && matchesArea;
  });

  const filteredAllSolicitudes = allSolicitudes.filter((sol) => {
    const matchesSearch = sol.title.toLowerCase().includes(globalSearchTerm.toLowerCase()) ||
                          sol.id.toString().includes(globalSearchTerm.trim());
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
    const isInnovacionForm = user?.area_id === 4 && (user?.role === "CREATOR" || user?.rol_id === 2);

    if (!formData.nombre_arte.trim()) {
      errors.nombre_arte = isInnovacionForm
        ? "El nombre de la innovación es requerido"
        : "El nombre del arte es requerido";
    } else if (formData.nombre_arte.length > 80) {
      errors.nombre_arte = "El nombre no puede exceder 80 caracteres";
    }

    if (isInnovacionForm) {
      if (!formData.categoria) {
        errors.categoria = "Debe seleccionar una categoría";
      }
    } else {
      if (!formData.area_id) {
        errors.area_id = "Debe seleccionar un área";
      }

      // Si es área de Operaciones y Calidad, se debe responder ambas preguntas
      const selectedArea = areas.find(a => a.id === parseInt(formData.area_id));
      const isOpCalidad = selectedArea?.nombre?.toLowerCase().includes("operacion");
      if (isOpCalidad && !formData.es_para_cafe) {
        errors.es_para_cafe = "Debe indicar si el producto es para café";
      }
      if (isOpCalidad && !formData.es_para_exportacion) {
        errors.es_para_exportacion = "Debe indicar si el arte va a exportación";
      }
    }

    const maxDesc = isInnovacionForm ? 900 : 500;
    if (formData.descripcion.length > maxDesc) {
      errors.descripcion = `La descripción no puede exceder ${maxDesc} caracteres`;
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
      const isInnovacionForm = user?.area_id === 4 && (user?.role === "CREATOR" || user?.rol_id === 2);
      const areaId = isInnovacionForm ? 4 : parseInt(formData.area_id);
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
      const solicitudData: Record<string, unknown> = {
        title: formData.nombre_arte,
        description: formData.descripcion || undefined,
        area_id: areaId,
        stage_id: firstEtapa.id,
        status_id: pendingEstado.id
      };

      // Incluir es_para_cafe y es_para_exportacion solo si el área es Operaciones y Calidad
      // Para el formulario de innovación (área 4), usar categoria para es_para_cafe
      const selectedArea = areas.find(a => a.id === areaId);
      if (isInnovacionForm) {
        solicitudData.es_para_cafe = formData.categoria === "bebidas";
      } else if (selectedArea?.nombre?.toLowerCase().includes("operacion")) {
        solicitudData.es_para_cafe = formData.es_para_cafe === "si";
        solicitudData.es_para_exportacion = formData.es_para_exportacion === "si";
      }
      
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

      // Si venimos desde una iniciativa, vincular automáticamente
      if (vincularIniciativaId) {
        try {
          await fetch(
            `${API_URL}/api/v1/iniciativas/${vincularIniciativaId}/vincular-prototipado?solicitud_id=${newSolicitud.id}`,
            { method: "POST", headers: { Authorization: `Bearer ${token}` } }
          );
          showToast(`✓ Solicitud #${newSolicitud.id} creada y vinculada a la iniciativa`);
          router.push(`/iniciativas/${vincularIniciativaId}`);
          return;
        } catch {
          showToast("Solicitud creada pero no se pudo vincular automáticamente", "error");
        }
      }
      
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
        es_para_cafe: "",
        es_para_exportacion: "",
        files: [],
        categoria: ""
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
  const isDirector = user.role === "DIRECTOR";
  const isInnovacionCreator = isCreator && user.area_id === 4;       // Área 4: Prototipado/Bebidas
  const isInnovacionArea = isCreator && user.area_id === 2;          // Área 2: INNOVACION (recibe solicitudes automáticas)

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
                    {isDirector ? "Directora de Mercadeo" : isApprover ? "Aprobador" : "Creador"}
                  </p>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <NotificationBell />
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
      </div>

      {/* Contenido principal */}
      <div className="flex-1 bg-gradient-to-br from-gray-50 to-gray-100 p-4 md:p-10">
        <div className="flex flex-col gap-6">
          {isDirector ? (
            /* ── VISTA DIRECTORA DE MERCADEO ── */
            <Card className="shadow-lg border-0 overflow-hidden">
              <div className="bg-gradient-to-r from-[#00829a] to-[#00a3b4] px-6 py-4 flex items-center justify-between">
                <div>
                  <CardTitle className="text-white text-xl font-bold uppercase tracking-wide">
                    Mis Iniciativas de Producto
                  </CardTitle>
                  <CardDescription className="text-white/90 font-normal">
                    Trazabilidad completa del flujo de aprobación
                  </CardDescription>
                </div>
                <Button
                  className="bg-white/20 hover:bg-white/30 text-white border-white/30 backdrop-blur-sm"
                  variant="outline"
                  onClick={() => router.push("/iniciativas/nueva")}
                >
                  <Plus className="h-4 w-4 mr-2" /> Nueva Iniciativa
                </Button>
              </div>
              <CardContent className="pt-6">
                {/* Filtros */}
                <div className="flex flex-col sm:flex-row gap-3 mb-5">
                  <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="Buscar por título o producto..."
                      value={iniSearch}
                      onChange={(e) => setIniSearch(e.target.value)}
                      className="pl-9"
                    />
                  </div>
                  <select
                    value={iniStatusFilter}
                    onChange={(e) => setIniStatusFilter(e.target.value)}
                    className="border rounded-md px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-[#00829a]/40"
                  >
                    <option value="ALL">Todos los estados</option>
                    {Object.entries(INI_STATUS_CONFIG).map(([key, cfg]) => (
                      <option key={key} value={key}>{cfg.label}</option>
                    ))}
                  </select>
                </div>

                {(() => {
                  const filtered = iniciativas.filter((i) => {
                    const matchSearch =
                      i.titulo.toLowerCase().includes(iniSearch.toLowerCase()) ||
                      i.producto_propuesto.toLowerCase().includes(iniSearch.toLowerCase());
                    const matchStatus = iniStatusFilter === "ALL" || i.status === iniStatusFilter;
                    return matchSearch && matchStatus;
                  });

                  if (filtered.length === 0) {
                    return (
                      <div className="py-14 flex flex-col items-center gap-4 text-center">
                        <div className="bg-[#00829a]/10 rounded-full p-5">
                          <Lightbulb className="h-10 w-10 text-[#00829a]" />
                        </div>
                        <div>
                          <p className="font-semibold text-gray-700">No hay iniciativas aún</p>
                          <p className="text-sm text-muted-foreground mt-1">Crea tu primera iniciativa de producto</p>
                        </div>
                        <Button
                          className="bg-[#00829a] hover:bg-[#006d82] text-white"
                          onClick={() => router.push("/iniciativas/nueva")}
                        >
                          <Plus className="h-4 w-4 mr-2" /> Nueva Iniciativa
                        </Button>
                      </div>
                    );
                  }

                  return (
                    <div className="flex flex-col gap-4">
                      {filtered.map((ini) => {
                        const cfg = INI_STATUS_CONFIG[ini.status] || { label: ini.status, color: "bg-gray-100 text-gray-600 border-gray-200", step: 0 };
                        const currentStep = cfg.step;
                        return (
                          <div
                            key={ini.id}
                            className="border rounded-xl p-5 hover:shadow-md transition-shadow cursor-pointer bg-white"
                            onClick={() => router.push(`/iniciativas/${ini.id}`)}
                          >
                            <div className="flex items-start justify-between gap-3 mb-4">
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 mb-1">
                                  <span className="text-xs font-mono text-muted-foreground">#{ini.id}</span>
                                  <span className={`inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium ${cfg.color}`}>
                                    {cfg.label}
                                  </span>
                                  {!ini.business_case_path && ini.status === "BORRADOR" && (
                                    <span className="inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium bg-red-50 text-red-600 border-red-200">
                                      Sin Business Case
                                    </span>
                                  )}
                                </div>
                                <h3 className="font-semibold text-gray-900 truncate">{ini.titulo}</h3>
                                <p className="text-sm text-muted-foreground truncate mt-0.5">{ini.producto_propuesto}</p>
                              </div>
                              <ChevronRight className="h-5 w-5 text-muted-foreground shrink-0 mt-1" />
                            </div>

                            {/* Stepper de trazabilidad */}
                            <div className="flex items-center gap-1">
                              {INI_STEPS.map((step, i) => {
                                const stepNum = i + 1;
                                const done = ini.status !== "RECHAZADA_JD" && currentStep > stepNum;
                                const active = currentStep === stepNum || (stepNum === 2 && (ini.status === "APROBADA_GG" || ini.status === "EN_PROTOTIPADO"));
                                const rejected = ini.status === "RECHAZADA_JD";
                                return (
                                  <React.Fragment key={step}>
                                    <div className="flex flex-col items-center" style={{ minWidth: 52 }}>
                                      <div className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold border-2 ${
                                        rejected && i === 0 ? "border-red-400 bg-red-400 text-white" :
                                        done ? "border-[#96c121] bg-[#96c121] text-white" :
                                        active ? "border-[#00829a] bg-[#00829a] text-white" :
                                        "border-gray-200 bg-gray-100 text-gray-400"
                                      }`}>
                                        {done ? "✓" : stepNum}
                                      </div>
                                      <span className={`text-[9px] mt-0.5 text-center leading-tight ${
                                        active ? "text-[#00829a] font-semibold" : "text-gray-400"
                                      }`}>{step}</span>
                                    </div>
                                    {i < INI_STEPS.length - 1 && (
                                      <div className={`flex-1 h-0.5 mb-4 ${done ? "bg-[#96c121]" : "bg-gray-200"}`} />
                                    )}
                                  </React.Fragment>
                                );
                              })}
                            </div>

                            {/* Links rápidos */}
                            {(ini.solicitud_id || ini.solicitud_innovacion_id) && (
                              <div className="mt-3 pt-3 border-t flex gap-4">
                                {ini.solicitud_id && (
                                  <button
                                    className="text-xs text-[#00829a] hover:underline font-medium"
                                    onClick={(e) => { e.stopPropagation(); router.push(`/solicitudes/${ini.solicitud_id}`); }}
                                  >
                                    → Solicitud prototipado #{ini.solicitud_id}
                                  </button>
                                )}
                                {ini.solicitud_innovacion_id && (
                                  <button
                                    className="text-xs text-[#96c121] hover:underline font-medium"
                                    onClick={(e) => { e.stopPropagation(); router.push(`/solicitudes/${ini.solicitud_innovacion_id}`); }}
                                  >
                                    → Solicitud innovación #{ini.solicitud_innovacion_id}
                                  </button>
                                )}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  );
                })()}
              </CardContent>
            </Card>
          ) : isCreator ? (
          <>
            {isInnovacionArea ? (
            <>
              {/* ── VISTA INNOVACION: sin formulario, solo tabla de solicitudes recibidas ── */}
              <Card className="shadow-lg border-0 overflow-hidden">
                <div className="bg-gradient-to-r from-[#00829a] to-[#00a3b4] px-6 py-4 flex items-center justify-between">
                  <div>
                    <CardTitle className="text-white text-xl font-bold uppercase tracking-wide">
                      Solicitudes de Innovación
                    </CardTitle>
                    <CardDescription className="text-white/90 font-normal">
                      {solicitudes.length === 0
                        ? "Aún no hay solicitudes asignadas a tu área."
                        : `${solicitudes.length} solicitud${solicitudes.length !== 1 ? "es" : ""} en tu área.`}
                    </CardDescription>
                  </div>
                </div>
                <CardContent className="pt-6">
                  {/* Banner informativo */}
                  <div className="mb-5 flex items-start gap-3 rounded-xl border border-[#00829a]/20 bg-[#00829a]/5 px-4 py-3">
                    <Lightbulb className="h-5 w-5 text-[#00829a] mt-0.5 shrink-0" />
                    <p className="text-sm text-[#00829a]">
                      Las solicitudes de Innovación se generan automáticamente cuando la Directora de Mercadeo aprueba una Iniciativa de Producto. Recibirás una notificación en la campana cada vez que llegue una nueva.
                    </p>
                  </div>

                  {solicitudes.length === 0 ? (
                    <div className="py-14 flex flex-col items-center gap-4 text-center">
                      <div className="bg-[#00829a]/10 rounded-full p-5">
                        <Lightbulb className="h-10 w-10 text-[#00829a]" />
                      </div>
                      <div>
                        <p className="font-semibold text-gray-700">Sin solicitudes por ahora</p>
                        <p className="text-sm text-muted-foreground mt-1">
                          Cuando se apruebe una Iniciativa de Producto, aparecerá aquí automáticamente.
                        </p>
                      </div>
                    </div>
                  ) : (
                    <div className="overflow-auto rounded-md border" style={{ maxHeight: 420 }}>
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead className="sticky top-0 bg-background z-10">ID</TableHead>
                            <TableHead className="sticky top-0 bg-background z-10">Nombre</TableHead>
                            <TableHead className="sticky top-0 bg-background z-10">Estado</TableHead>
                            <TableHead className="sticky top-0 bg-background z-10">Etapa actual</TableHead>
                            <TableHead className="sticky top-0 bg-background z-10">Última actualización</TableHead>
                            <TableHead className="sticky top-0 bg-background z-10 text-right">Acciones</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {solicitudes
                            .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
                            .map((sol) => (
                              <TableRow key={sol.id}>
                                <TableCell className="font-mono text-sm">{sol.id}</TableCell>
                                <TableCell className="font-medium max-w-xs truncate">{sol.title}</TableCell>
                                <TableCell>
                                  <Badge variant="outline" className="text-xs">{sol.state?.label || sol.state?.code}</Badge>
                                </TableCell>
                                <TableCell className="text-sm text-[#00829a] font-medium">
                                  {sol.stage?.label || "—"}
                                </TableCell>
                                <TableCell className="text-sm text-muted-foreground">
                                  {new Date(sol.updated_at).toLocaleDateString("es-CO", { day: "2-digit", month: "short", year: "numeric" })}
                                </TableCell>
                                <TableCell className="text-right">
                                  <Button
                                    size="sm"
                                    className="bg-[#00829a] hover:bg-[#006d82] text-white"
                                    onClick={() => router.push(`/solicitudes/${sol.id}`)}
                                  >
                                    Ver detalle
                                  </Button>
                                </TableCell>
                              </TableRow>
                            ))}
                        </TableBody>
                      </Table>
                    </div>
                  )}
                </CardContent>
              </Card>
            </>
            ) : isInnovacionCreator ? (
            <>
              {/* INNOVACIÓN CREATOR VIEW: Iniciativas pendientes de su acción */}
              <Card className="shadow-lg border-0 overflow-hidden">
                <div className="bg-gradient-to-r from-[#00829a] to-[#00a3b4] px-6 py-4">
                  <CardTitle className="text-white text-xl font-bold uppercase tracking-wide">Iniciativas de Prototipado</CardTitle>
                  <CardDescription className="text-white/90 font-normal">
                    Iniciativas asignadas a tu área para desarrollar
                  </CardDescription>
                </div>
                <CardContent className="pt-6">
                  {(() => {
                    const pendientes = iniciativas.filter(i =>
                      ["APROBADA_GG", "EN_PROTOTIPADO", "PENDIENTE_APROBACION_DUAL"].includes(i.status)
                    );
                    if (iniciativas.length === 0) {
                      return (
                        <div className="py-14 flex flex-col items-center gap-3 text-center">
                          <div className="bg-purple-100 rounded-full p-5">
                            <Lightbulb className="h-10 w-10 text-purple-500" />
                          </div>
                          <p className="font-semibold text-gray-700">No hay iniciativas asignadas</p>
                          <p className="text-sm text-muted-foreground">Cuando la Directora envíe una iniciativa a prototipado, aparecerá aquí.</p>
                        </div>
                      );
                    }
                    const grupos: { label: string; color: string; badge: string; items: typeof iniciativas } [] = [
                      {
                        label: "Pendientes de vincular",
                        color: "border-l-purple-400 bg-purple-50",
                        badge: "bg-purple-100 text-purple-700 border-purple-200",
                        items: iniciativas.filter(i => i.status === "APROBADA_GG" && !i.solicitud_id),
                      },
                      {
                        label: "En desarrollo",
                        color: "border-l-blue-400 bg-blue-50",
                        badge: "bg-blue-100 text-blue-700 border-blue-200",
                        items: iniciativas.filter(i => i.status === "EN_PROTOTIPADO"),
                      },
                      {
                        label: "Aprobación dual en curso",
                        color: "border-l-orange-400 bg-orange-50",
                        badge: "bg-orange-100 text-orange-700 border-orange-200",
                        items: iniciativas.filter(i => i.status === "PENDIENTE_APROBACION_DUAL"),
                      },
                    ];
                    return (
                      <div className="flex flex-col gap-6">
                        {grupos.map((grupo) => grupo.items.length > 0 && (
                          <div key={grupo.label}>
                            <div className="flex items-center gap-2 mb-3">
                              <h3 className="text-sm font-semibold text-gray-700">{grupo.label}</h3>
                              <span className="text-xs bg-gray-100 text-gray-500 rounded-full px-2 py-0.5">{grupo.items.length}</span>
                            </div>
                            <div className="flex flex-col gap-3">
                              {grupo.items.map((ini) => (
                                <div
                                  key={ini.id}
                                  className={`border-l-4 rounded-r-xl p-4 flex items-center justify-between gap-4 cursor-pointer hover:shadow-sm transition-shadow ${grupo.color}`}
                                  onClick={() => router.push(`/iniciativas/${ini.id}`)}
                                >
                                  <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2 mb-0.5">
                                      <span className="text-xs font-mono text-muted-foreground">#{ini.id}</span>
                                      <span className={`inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium ${grupo.badge}`}>
                                        {grupo.label}
                                      </span>
                                    </div>
                                    <p className="font-semibold text-gray-900 truncate">{ini.titulo}</p>
                                    <p className="text-sm text-muted-foreground truncate">{ini.producto_propuesto}</p>
                                  </div>
                                  <div className="flex items-center gap-2 shrink-0">
                                    {ini.solicitud_id && (
                                      <button
                                        className="text-xs text-[#00829a] hover:underline font-medium"
                                        onClick={(e) => { e.stopPropagation(); router.push(`/solicitudes/${ini.solicitud_id}`); }}
                                      >
                                        Solicitud #{ini.solicitud_id}
                                      </button>
                                    )}
                                    <ChevronRight className="h-5 w-5 text-muted-foreground" />
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        ))}
                        {pendientes.length === 0 && (
                          <div className="py-8 text-center text-sm text-muted-foreground">
                            No hay iniciativas activas en este momento.
                          </div>
                        )}
                      </div>
                    );
                  })()}
                </CardContent>
              </Card>
            </>
            ) : (
            <>
            {/* STANDARD CREATOR VIEW: New Solicitud Form */}
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
                        onChange={(e) => setFormData(prev => ({ ...prev, area_id: e.target.value, es_para_cafe: "", es_para_exportacion: "" }))}
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

                  {/* Pregunta de Café: solo aparece cuando el área es Operaciones y Calidad */}
                  {(() => {
                    const selectedArea = areas.find(a => a.id === parseInt(formData.area_id));
                    const isOpCalidad = selectedArea?.nombre?.toLowerCase().includes("operacion");
                    if (!isOpCalidad) return null;
                    return (
                      <div className="space-y-3 rounded-lg border-2 border-[#00829a]/30 bg-[#00829a]/5 p-4">
                        <Label className="font-semibold text-[#00829a]">
                          ¿El producto es para Café? *
                        </Label>
                        <p className="text-xs text-muted-foreground -mt-1">
                          Esto determina si se requiere la aprobación del responsable de control de calidad de café.
                        </p>
                        <div className="flex gap-4">
                          <label className="flex items-center gap-2 cursor-pointer">
                            <input
                              type="radio"
                              name="es_para_cafe"
                              value="si"
                              checked={formData.es_para_cafe === "si"}
                              onChange={() => setFormData(prev => ({ ...prev, es_para_cafe: "si" }))}
                              className="accent-[#00829a] w-4 h-4"
                            />
                            <span className="font-medium text-sm">Sí, es para Café</span>
                          </label>
                          <label className="flex items-center gap-2 cursor-pointer">
                            <input
                              type="radio"
                              name="es_para_cafe"
                              value="no"
                              checked={formData.es_para_cafe === "no"}
                              onChange={() => setFormData(prev => ({ ...prev, es_para_cafe: "no" }))}
                              className="accent-[#00829a] w-4 h-4"
                            />
                            <span className="font-medium text-sm">No, no es para Café</span>
                          </label>
                        </div>
                        {formErrors.es_para_cafe && (
                          <p className="text-sm text-red-500">{formErrors.es_para_cafe}</p>
                        )}
                      </div>
                    );
                  })()}

                  {/* Pregunta de Exportación: solo aparece cuando el área es Operaciones y Calidad */}
                  {(() => {
                    const selectedArea = areas.find(a => a.id === parseInt(formData.area_id));
                    const isOpCalidad = selectedArea?.nombre?.toLowerCase().includes("operacion");
                    if (!isOpCalidad) return null;
                    return (
                      <div className="space-y-3 rounded-lg border-2 border-[#96c121]/30 bg-[#96c121]/5 p-4">
                        <Label className="font-semibold text-[#5a7a10]">
                          ¿El arte va a exportación? *
                        </Label>
                        <p className="text-xs text-muted-foreground -mt-1">
                          Esto determina si se requiere la aprobación del responsable de exportaciones.
                        </p>
                        <div className="flex gap-4">
                          <label className="flex items-center gap-2 cursor-pointer">
                            <input
                              type="radio"
                              name="es_para_exportacion"
                              value="si"
                              checked={formData.es_para_exportacion === "si"}
                              onChange={() => setFormData(prev => ({ ...prev, es_para_exportacion: "si" }))}
                              className="accent-[#96c121] w-4 h-4"
                            />
                            <span className="font-medium text-sm">Sí, va a exportación</span>
                          </label>
                          <label className="flex items-center gap-2 cursor-pointer">
                            <input
                              type="radio"
                              name="es_para_exportacion"
                              value="no"
                              checked={formData.es_para_exportacion === "no"}
                              onChange={() => setFormData(prev => ({ ...prev, es_para_exportacion: "no" }))}
                              className="accent-[#96c121] w-4 h-4"
                            />
                            <span className="font-medium text-sm">No, no va a exportación</span>
                          </label>
                        </div>
                        {formErrors.es_para_exportacion && (
                          <p className="text-sm text-red-500">{formErrors.es_para_exportacion}</p>
                        )}
                      </div>
                    );
                  })()}

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
                  <div className="overflow-auto rounded-md border" style={{ maxHeight: 420 }}>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="sticky top-0 bg-background z-10">ID</TableHead>
                        <TableHead className="sticky top-0 bg-background z-10">Nombre del arte</TableHead>
                        <TableHead className="sticky top-0 bg-background z-10">Estado</TableHead>
                        <TableHead className="sticky top-0 bg-background z-10">Etapa actual</TableHead>
                        <TableHead className="sticky top-0 bg-background z-10">Última actualización</TableHead>
                        <TableHead className="sticky top-0 bg-background z-10 text-right">Acciones</TableHead>
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
                  </div>
                ) : (
                  <div className="flex h-40 items-center justify-center text-muted-foreground">
                    No tienes solicitudes creadas aún. Usa el formulario de arriba para crear una.
                  </div>
                )}
              </CardContent>
            </Card>
            </>
            )} {/* fin isInnovacionCreator */}
          </>
        ) : isApprover ? (
          <>
            <Card className="shadow-lg border-0 overflow-hidden">
              <div className="bg-gradient-to-r from-[#00829a] to-[#00a3b4] px-6 py-4">
                <CardTitle className="text-white text-xl font-bold">Solicitudes por aprobar</CardTitle>
                <CardDescription className="text-white/90 font-normal">
                  {filteredSolicitudes.length === 0
                    ? "No tienes aprobaciones pendientes."
                    : `Tienes ${filteredSolicitudes.length} solicitudes pendientes.`}
                </CardDescription>
              </div>
              <CardContent className="pt-6">
                {filteredSolicitudes.length > 0 ? (
                  <div className="overflow-auto rounded-md border" style={{ maxHeight: 420 }}>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="sticky top-0 bg-background z-10">Nombre del arte</TableHead>
                        <TableHead className="sticky top-0 bg-background z-10">Fecha creación</TableHead>
                        <TableHead className="sticky top-0 bg-background z-10">Área</TableHead>
                        <TableHead className="sticky top-0 bg-background z-10">Etapa actual</TableHead>
                        <TableHead className="sticky top-0 bg-background z-10">Estado</TableHead>
                        <TableHead className="sticky top-0 bg-background z-10 text-right">Acciones</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredSolicitudes.map((sol) => (
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
                  </div>
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
                    placeholder="Buscar por nombre o ID..."
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
                  <div className="overflow-auto rounded-md border" style={{ maxHeight: 420 }}>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="sticky top-0 bg-background z-10">ID</TableHead>
                        <TableHead className="sticky top-0 bg-background z-10">Nombre del arte</TableHead>
                        <TableHead className="sticky top-0 bg-background z-10">Estado</TableHead>
                        <TableHead className="sticky top-0 bg-background z-10">Etapa actual</TableHead>
                        <TableHead className="sticky top-0 bg-background z-10">Área</TableHead>
                        <TableHead className="sticky top-0 bg-background z-10">Última actualización</TableHead>
                        <TableHead className="sticky top-0 bg-background z-10 text-right">Acciones</TableHead>
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
                  </Table>                  </div>                ) : (
                  <div className="flex h-40 items-center justify-center text-muted-foreground">
                    No se encontraron resultados
                  </div>
                )}
              </CardContent>
            </Card>
          </>
        ) : !isDirector ? (
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
        ) : null}
        </div>
      </div>
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </div>
  );
}
