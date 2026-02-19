"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { FileText, Calendar, Layers, GitBranch } from "lucide-react";

interface Arte {
  id: number;
  nombre: string;
  fecha_creacion: string;
  estado: { id: number; nombre: string } | null;
  etapa: { id: number; nombre: string } | null;
  area: { id: number; nombre: string } | null;
}

interface ArtesTableProps {
  artes: Arte[];
}

function formatDate(dateString: string) {
  return new Date(dateString).toLocaleDateString("es-ES", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function getEstadoBadgeVariant(estado: string | undefined) {
  switch (estado?.toUpperCase()) {
    case "PENDIENTE":
      return "default";
    case "APROBADO":
      return "secondary";
    case "RECHAZADO":
      return "destructive";
    default:
      return "outline";
  }
}

function getAreaBadgeVariant(area: string | undefined) {
  if (area?.includes("Innovación") || area?.includes("Innovacion")) {
    return "default";
  }
  if (area?.includes("Operaciones") || area?.includes("Calidad")) {
    return "secondary";
  }
  return "outline";
}

export function ArtesTable({ artes }: ArtesTableProps) {
  if (artes.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <FileText className="h-12 w-12 text-muted-foreground/50 mb-4" />
        <h3 className="text-lg font-medium">No hay artes pendientes</h3>
        <p className="text-sm text-muted-foreground mt-1">
          Todas las solicitudes han sido procesadas
        </p>
      </div>
    );
  }

  return (
    <>
      {/* Vista de tabla para pantallas grandes */}
      <div className="hidden md:block">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nombre del Arte</TableHead>
              <TableHead>Fecha Creación</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead>Etapa Actual</TableHead>
              <TableHead>Área/Flujo</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {artes.map((arte) => (
              <TableRow key={arte.id} className="cursor-pointer hover:bg-muted/50">
                <TableCell className="font-medium">{arte.nombre}</TableCell>
                <TableCell>{formatDate(arte.fecha_creacion)}</TableCell>
                <TableCell>
                  <Badge variant={getEstadoBadgeVariant(arte.estado?.nombre)}>
                    {arte.estado?.nombre || "Sin estado"}
                  </Badge>
                </TableCell>
                <TableCell>{arte.etapa?.nombre || "Sin etapa"}</TableCell>
                <TableCell>
                  <Badge variant={getAreaBadgeVariant(arte.area?.nombre)}>
                    {arte.area?.nombre || "Sin área"}
                  </Badge>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Vista de cards para móvil */}
      <div className="md:hidden space-y-4">
        {artes.map((arte) => (
          <Card key={arte.id} className="p-4">
            <div className="space-y-3">
              <div className="flex items-start justify-between">
                <h3 className="font-medium leading-tight">{arte.nombre}</h3>
                <Badge variant={getEstadoBadgeVariant(arte.estado?.nombre)}>
                  {arte.estado?.nombre || "Sin estado"}
                </Badge>
              </div>

              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Calendar className="h-4 w-4" />
                  <span>{formatDate(arte.fecha_creacion)}</span>
                </div>
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Layers className="h-4 w-4" />
                  <span>{arte.etapa?.nombre || "Sin etapa"}</span>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <GitBranch className="h-4 w-4 text-muted-foreground" />
                <Badge variant={getAreaBadgeVariant(arte.area?.nombre)}>
                  {arte.area?.nombre || "Sin área"}
                </Badge>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </>
  );
}
