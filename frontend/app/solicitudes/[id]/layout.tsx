export function generateStaticParams() {
  return [{ id: "placeholder" }];
}

export default function SolicitudLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
