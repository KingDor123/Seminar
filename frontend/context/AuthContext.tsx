'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { authService, AuthResponse } from '../services/authService';
import { LoginFormInputs, RegisterFormInputs } from '../schemas/authSchema';

// Define the User type based on what the backend returns
type User = AuthResponse['user'];

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (data: LoginFormInputs) => Promise<void>;
  register: (data: RegisterFormInputs) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  const checkAuth = async () => {
    try {
      const userData = await authService.getMe();
      setUser(userData);
    } catch {
      // If authenticaton fails (e.g. 401), we must ensure the local cookie is cleared
      // to prevent Middleware from redirecting back to home in an infinite loop.
      try {
          await authService.logout(); 
      } catch (e) {
          console.error("Failed to perform cleanup logout", e);
      }
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    checkAuth();
  }, []);

  // Protect routes
  useEffect(() => {
    // Public routes that don't require authentication
    const publicRoutes = ['/login', '/register', '/'];
    if (!isLoading && !user && !publicRoutes.includes(pathname)) {
        // If not logged in and trying to access a protected route
        // We could redirect here, or let the page handle it.
        // For a strict "Pro" feel, centralizing redirect is often good,
        // but Middleware is better for server-side.
        // Client-side redirect:
        router.push('/login');
    }
    // If logged in and on login/register page, redirect to home
    if (!isLoading && user && (pathname === '/login' || pathname === '/register')) {
        router.push('/home');
    }
  }, [user, isLoading, pathname, router]);


  const login = async (data: LoginFormInputs) => {
    setIsLoading(true);
    try {
      const response = await authService.login(data);
      setUser(response.user);
      router.push('/home');
    } catch (error) {
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const registerUser = async (data: RegisterFormInputs) => {
    setIsLoading(true);
    try {
      const response = await authService.register(data);
      setUser(response.user);
      router.push('/home');
    } catch (error) {
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setIsLoading(true);
    try {
      await authService.logout();
      setUser(null);
      router.push('/login');
    } catch (error) {
      console.error('Logout failed', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register: registerUser, logout, checkAuth }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
