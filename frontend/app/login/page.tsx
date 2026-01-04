'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { loginSchema, LoginFormInputs } from '../../schemas/authSchema';
import { useAuth } from '../../context/AuthContext';
import { useState } from 'react';
import Link from 'next/link';
import { AuthShell } from '../../components/auth/AuthShell';
import { Input } from '../../components/ui/input';
import { Button } from '../../components/ui/button';
import { cn } from '../../lib/utils';
import { ensureHebrew, he } from '../../constants/he';

export default function LoginPage() {
  const { login } = useAuth();
  const [error, setError] = useState<string | null>(null);
  
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormInputs>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFormInputs) => {
    try {
      setError(null);
      await login(data);
      // Redirect is handled by AuthContext
    } catch (err: unknown) {
      console.error(err);
      let errorMessage = he.auth.errors.loginFailed;
      if (err && typeof err === 'object' && 'response' in err) {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          errorMessage = (err as any).response?.data?.message || errorMessage;
      } else if (err instanceof Error) {
          errorMessage = err.message;
      }
      setError(ensureHebrew(errorMessage, he.auth.errors.loginFailed));
    }
  };

  return (
    <AuthShell
      title={he.auth.signIn.title}
      subtitle={
        <>
          {he.auth.signIn.subtitlePrefix}{' '}
          <Link href="/register" className="font-medium text-primary hover:text-primary/80">
            {he.auth.signIn.subtitleLink}
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
          <label htmlFor="email-address" className="text-sm font-medium text-muted-foreground">
            {he.auth.fields.email}
          </label>
          <Input
            id="email-address"
            type="email"
            autoComplete="email"
            placeholder={he.auth.placeholders.email}
            className={cn("mt-2 rounded-xl", errors.email && "border-destructive")}
            {...register("email")}
          />
          {errors.email && (
            <p className="mt-1 text-xs text-destructive">{errors.email.message}</p>
          )}
        </div>

        <div>
          <label htmlFor="password" className="text-sm font-medium text-muted-foreground">
            {he.auth.fields.password}
          </label>
          <Input
            id="password"
            type="password"
            autoComplete="current-password"
            placeholder={he.auth.placeholders.password}
            className={cn("mt-2 rounded-xl", errors.password && "border-destructive")}
            {...register("password")}
          />
          {errors.password && (
            <p className="mt-1 text-xs text-destructive">{errors.password.message}</p>
          )}
        </div>

        <Button
          type="submit"
          disabled={isSubmitting}
          className="mt-4 w-full rounded-xl"
        >
          {isSubmitting ? (
            <span className="flex items-center gap-2">
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-primary-foreground/30 border-t-primary-foreground" />
              {he.auth.signIn.loading}
            </span>
          ) : (
            he.auth.signIn.button
          )}
        </Button>
      </form>
    </AuthShell>
  );
}
