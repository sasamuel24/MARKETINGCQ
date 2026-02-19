"use client";
import { useEffect } from "react";
import { CheckCircle, XCircle, X } from "lucide-react";

export interface ToastData {
  id: number;
  message: string;
  type: "success" | "error";
}

interface ToastProps {
  toasts: ToastData[];
  onRemove: (id: number) => void;
}

export function ToastContainer({ toasts, onRemove }: ToastProps) {
  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 pointer-events-none">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onRemove={onRemove} />
      ))}
    </div>
  );
}

function ToastItem({ toast, onRemove }: { toast: ToastData; onRemove: (id: number) => void }) {
  useEffect(() => {
    const timer = setTimeout(() => onRemove(toast.id), 4000);
    return () => clearTimeout(timer);
  }, [toast.id, onRemove]);

  const isSuccess = toast.type === "success";

  return (
    <div
      className={`pointer-events-auto flex items-start gap-3 rounded-lg px-4 py-3 shadow-lg text-white text-sm max-w-sm animate-in slide-in-from-right-5 fade-in-0 duration-300 ${
        isSuccess ? "bg-green-600" : "bg-red-600"
      }`}
    >
      {isSuccess ? (
        <CheckCircle className="h-5 w-5 flex-shrink-0 mt-0.5" />
      ) : (
        <XCircle className="h-5 w-5 flex-shrink-0 mt-0.5" />
      )}
      <span className="flex-1">{toast.message}</span>
      <button
        onClick={() => onRemove(toast.id)}
        className="ml-2 opacity-70 hover:opacity-100 flex-shrink-0"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}
