export function generateStaticParams() {
  return Array.from({ length: 100 }, (_, i) => ({ id: String(i + 1) }));
}

export default function IniciativaLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
