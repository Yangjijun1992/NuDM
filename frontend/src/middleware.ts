import { NextResponse } from "next/server"
import type { NextRequest } from "next/server"

const AUTH_ROUTES = ["/favorites", "/subscriptions", "/notifications", "/profile"]
const ADMIN_ROUTES = ["/admin"]

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  const token = request.cookies.get("token")?.value || ""

  const requiresAuth = AUTH_ROUTES.some((r) => pathname.startsWith(r))
  const requiresAdmin = ADMIN_ROUTES.some((r) => pathname.startsWith(r))

  if (requiresAuth && !token) {
    return NextResponse.redirect(new URL("/auth", request.url))
  }

  if (requiresAdmin) {
    if (!token) {
      return NextResponse.redirect(new URL("/auth", request.url))
    }
  }

  return NextResponse.next()
}

export const config = {
  matcher: ["/favorites/:path*", "/subscriptions/:path*", "/notifications/:path*", "/profile/:path*", "/admin/:path*"],
}
