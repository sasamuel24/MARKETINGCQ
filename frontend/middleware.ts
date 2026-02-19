import { type NextRequest, NextResponse } from "next/server";

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // No interferir con change-password, login ni assets estáticos
  if (
    pathname.startsWith("/change-password") ||
    pathname.startsWith("/login") ||
    pathname.startsWith("/_next")
  ) {
    return NextResponse.next();
  }

  // Redirigir si el usuario debe cambiar su contraseña
  const mustChange = request.cookies.get("must_change_password")?.value;
  if (mustChange === "true") {
    return NextResponse.redirect(new URL("/change-password", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
