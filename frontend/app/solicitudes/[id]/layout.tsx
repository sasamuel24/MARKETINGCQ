export function generateStaticParams() {
  // Genera rutas estáticas placeholder; Amplify rewrite cubre IDs reales
  return Array.from({ length: 100 }, (_, i) => ({ id: String(i + 1) }));
}

export default function SolicitudLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
