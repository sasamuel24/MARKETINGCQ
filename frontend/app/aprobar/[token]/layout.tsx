export function generateStaticParams() {
  // El token es dinámico (UUID), Amplify rewrite cubre todos los casos
  return [];
}

export default function AprobarLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
