"use client";
import React, { useEffect, useRef, useState } from "react";
import { Bell, X, CheckCheck } from "lucide-react";
import { useRouter } from "next/navigation";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Notificacion {
  id: number;
  tipo: string;
  titulo: string;
  mensaje: string;
  leida: boolean;
  iniciativa_id?: number;
  solicitud_id?: number;
  created_at: string;
}

export function NotificationBell() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [notificaciones, setNotificaciones] = useState<Notificacion[]>([]);
  const [noLeidas, setNoLeidas] = useState(0);
  const panelRef = useRef<HTMLDivElement>(null);

  const fetchNotificaciones = async () => {
    const token = localStorage.getItem("access_token");
    if (!token) return;
    try {
      const res = await fetch(`${API_URL}/api/v1/notificaciones?page_size=20`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setNotificaciones(data.notificaciones || []);
        setNoLeidas(data.no_leidas || 0);
      }
    } catch {}
  };

  useEffect(() => {
    fetchNotificaciones();
    const interval = setInterval(fetchNotificaciones, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    if (open) document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [open]);

  const marcarLeida = async (notif: Notificacion) => {
    const token = localStorage.getItem("access_token");
    if (!token || notif.leida) return;
    await fetch(`${API_URL}/api/v1/notificaciones/${notif.id}/marcar-leida`, {
      method: "PUT",
      headers: { Authorization: `Bearer ${token}` },
    });
    setNotificaciones((prev) =>
      prev.map((n) => (n.id === notif.id ? { ...n, leida: true } : n))
    );
    setNoLeidas((prev) => Math.max(0, prev - 1));
  };

  const marcarTodasLeidas = async () => {
    const token = localStorage.getItem("access_token");
    if (!token) return;
    await fetch(`${API_URL}/api/v1/notificaciones/marcar-todas-leidas`, {
      method: "PUT",
      headers: { Authorization: `Bearer ${token}` },
    });
    setNotificaciones((prev) => prev.map((n) => ({ ...n, leida: true })));
    setNoLeidas(0);
  };

  const handleClick = async (notif: Notificacion) => {
    await marcarLeida(notif);
    setOpen(false);
    // Priorizar solicitud_id para ir directo al flujo de trabajo
    if (notif.solicitud_id) {
      router.push(`/solicitudes/${notif.solicitud_id}`);
    } else if (notif.iniciativa_id) {
      router.push(`/iniciativas/${notif.iniciativa_id}`);
    }
  };

  const formatTime = (dateStr: string) => {
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 60) return `${mins}m`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h`;
    return `${Math.floor(hrs / 24)}d`;
  };

  return (
    <div className="relative" ref={panelRef}>
      <button
        onClick={() => setOpen((o) => !o)}
        className="relative p-2 rounded-full bg-white/20 hover:bg-white/30 transition-colors"
        aria-label="Notificaciones"
      >
        <Bell className="h-5 w-5 text-white" />
        {noLeidas > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-[10px] font-bold rounded-full min-w-[18px] h-[18px] flex items-center justify-center px-1">
            {noLeidas > 9 ? "9+" : noLeidas}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-12 w-80 bg-white rounded-xl shadow-2xl border border-gray-100 z-50 overflow-hidden">
          {/* Header panel */}
          <div className="flex items-center justify-between px-4 py-3 border-b bg-gray-50">
            <span className="font-semibold text-sm text-gray-700">
              Notificaciones {noLeidas > 0 && <span className="text-[#00829a]">({noLeidas} nuevas)</span>}
            </span>
            <div className="flex items-center gap-2">
              {noLeidas > 0 && (
                <button
                  onClick={marcarTodasLeidas}
                  className="text-xs text-[#00829a] hover:text-[#006d82] flex items-center gap-1"
                  title="Marcar todas como leídas"
                >
                  <CheckCheck className="h-3.5 w-3.5" />
                </button>
              )}
              <button onClick={() => setOpen(false)} className="text-gray-400 hover:text-gray-600">
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Lista */}
          <div className="max-h-80 overflow-y-auto divide-y divide-gray-50">
            {notificaciones.length === 0 ? (
              <div className="py-8 text-center text-sm text-gray-400">
                Sin notificaciones
              </div>
            ) : (
              notificaciones.map((n) => (
                <button
                  key={n.id}
                  onClick={() => handleClick(n)}
                  className={`w-full text-left px-4 py-3 hover:bg-gray-50 transition-colors ${
                    !n.leida ? "bg-blue-50/50" : ""
                  }`}
                >
                  <div className="flex items-start gap-2">
                    {!n.leida && (
                      <span className="mt-1.5 h-2 w-2 rounded-full bg-[#00829a] flex-shrink-0" />
                    )}
                    <div className={!n.leida ? "" : "pl-4"}>
                      <p className="text-xs font-semibold text-gray-800 leading-snug">{n.titulo}</p>
                      <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{n.mensaje}</p>
                      <p className="text-[10px] text-gray-400 mt-1">{formatTime(n.created_at)}</p>
                    </div>
                  </div>
                </button>
              ))
            )}
          </div>

          {/* Footer */}
          {notificaciones.length > 0 && (
            <div className="border-t px-4 py-2 bg-gray-50">
              <button
                onClick={() => { setOpen(false); router.push("/dashboard"); }}
                className="text-xs text-[#00829a] hover:text-[#006d82] font-medium"
              >
                Ir al dashboard →
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
