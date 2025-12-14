import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const token = request.cookies.get('token')?.value;
  const { pathname } = request.nextUrl;

  // Define paths
  const isAuthPage = pathname === '/login' || pathname === '/register';
  const isRootPage = pathname === '/';
  
  // 1. If user is at root '/', redirect based on auth status
  if (isRootPage) {
    if (token) {
      return NextResponse.redirect(new URL('/home', request.url));
    } else {
      return NextResponse.redirect(new URL('/login', request.url));
    }
  }

  // 2. If user is logged in and tries to access login/register, redirect to home
  if (isAuthPage && token) {
    return NextResponse.redirect(new URL('/home', request.url));
  }

  // 3. If user is NOT logged in and tries to access protected pages
  // We assume everything EXCEPT login/register/public assets is protected
  // We exclude /_next, /static, /favicon.ico, etc. via config matcher below
  if (!token && !isAuthPage) {
     return NextResponse.redirect(new URL('/login', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder files (svgs, images etc if strictly needed, but usually handled by _next exclusion or specific patterns)
     */
    '/((?!api|_next/static|_next/image|favicon.ico|.*\.svg|.*\.png|.*\.glb|.*\.js).*)',
  ],
};
