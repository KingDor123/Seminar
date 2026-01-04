'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { registerSchema, RegisterFormInputs } from '../../schemas/authSchema';
import { useAuth } from '../../context/AuthContext';
import { useState } from 'react';
import Link from 'next/link';
import { AuthShell } from '../../components/auth/AuthShell';
import { Input } from '../../components/ui/input';
import { Button } from '../../components/ui/button';
import { cn } from '../../lib/utils';

export default function RegisterPage() {
  const { register: registerUser } = useAuth();
  const [error, setError] = useState<string | null>(null);
  
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormInputs>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = async (data: RegisterFormInputs) => {
    try {
      setError(null);
      await registerUser(data);
      // Redirect handled by AuthContext
    } catch (err: unknown) {
      console.error(err);
      let errorMessage = 'Registration failed';
      if (err && typeof err === 'object' && 'response' in err) {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          errorMessage = (err as any).response?.data?.message || errorMessage;
      } else if (err instanceof Error) {
          errorMessage = err.message;
      }
      setError(errorMessage);
    }
  };

  return (
    <AuthShell
      title="Create an account"
      subtitle={
        <>
          Or{' '}
          <Link href="/login" className="font-medium text-primary hover:text-primary/80">
            sign in to your existing account
          </Link>
        </>
      }
    >
      {error && (
        <div className="rounded-xl border border-destructive/20 bg-destructive/10 p-3 text-sm text-destructive">
          {error}
        </div>
      )}

      <form className="mt-6 space-y-4" onSubmit={handleSubmit(onSubmit)}>
        <div>
          <label htmlFor="full_name" className="text-sm font-medium text-muted-foreground">
            Full Name
          </label>
          <Input
            id="full_name"
            type="text"
            placeholder="Your name"
            className={cn("mt-2 rounded-xl", errors.full_name && "border-destructive")}
            {...register("full_name")}
          />
          {errors.full_name && (
            <p className="mt-1 text-xs text-destructive">{errors.full_name.message}</p>
          )}
        </div>

        <div>
          <label htmlFor="email-address" className="text-sm font-medium text-muted-foreground">
            Email address
          </label>
          <Input
            id="email-address"
            type="email"
            autoComplete="email"
            placeholder="you@example.com"
            className={cn("mt-2 rounded-xl", errors.email && "border-destructive")}
            {...register("email")}
          />
          {errors.email && (
            <p className="mt-1 text-xs text-destructive">{errors.email.message}</p>
          )}
        </div>

        <div>
          <label htmlFor="password" className="text-sm font-medium text-muted-foreground">
            Password
          </label>
          <Input
            id="password"
            type="password"
            autoComplete="new-password"
            placeholder="Create a password"
            className={cn("mt-2 rounded-xl", errors.password && "border-destructive")}
            {...register("password")}
          />
          {errors.password && (
            <p className="mt-1 text-xs text-destructive">{errors.password.message}</p>
          )}
        </div>

        <div>
          <label htmlFor="confirmPassword" className="text-sm font-medium text-muted-foreground">
            Confirm Password
          </label>
          <Input
            id="confirmPassword"
            type="password"
            autoComplete="new-password"
            placeholder="Repeat your password"
            className={cn("mt-2 rounded-xl", errors.confirmPassword && "border-destructive")}
            {...register("confirmPassword")}
          />
          {errors.confirmPassword && (
            <p className="mt-1 text-xs text-destructive">{errors.confirmPassword.message}</p>
          )}
        </div>

        <Button type="submit" disabled={isSubmitting} className="mt-4 w-full rounded-xl">
          {isSubmitting ? (
            <span className="flex items-center gap-2">
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-primary-foreground/30 border-t-primary-foreground" />
              Creating account...
            </span>
          ) : (
            "Sign up"
          )}
        </Button>
      </form>
    </AuthShell>
  );
}
