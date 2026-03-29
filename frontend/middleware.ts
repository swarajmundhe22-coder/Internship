import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

const REMOVED_SCREEN_PREFIXES = [
  "/dashboard",
  "/projects",
  "/about",
  "/credibility",
  "/expertise",
  "/simulations",
  "/reports",
  "/materials",
  "/environments",
  "/visualization",
  "/admin",
];

function isRemovedScreen(pathname: string): boolean {
  return REMOVED_SCREEN_PREFIXES.some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`));
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (!isRemovedScreen(pathname)) {
    return NextResponse.next();
  }

  const destination = request.nextUrl.clone();
  destination.pathname = "/";
  destination.search = "";
  return NextResponse.redirect(destination);
}

export const config = {
  matcher: [
    "/dashboard/:path*",
    "/projects/:path*",
    "/about/:path*",
    "/credibility/:path*",
    "/expertise/:path*",
    "/simulations/:path*",
    "/reports/:path*",
    "/materials/:path*",
    "/environments/:path*",
    "/visualization/:path*",
    "/admin/:path*",
  ],
};
