'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { profileSchema, ProfileFormInputs } from '../../schemas/profileSchema';
import { useAuth } from '../../context/AuthContext';
import { authService } from '../../services/authService';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { PageShell } from '../../components/layout/PageShell';
import { Input } from '../../components/ui/input';
import { Button } from '../../components/ui/button';
import { cn } from '../../lib/utils';
import { ensureHebrew, he } from '../../constants/he';

export default function ProfilePage() {
  const { user, checkAuth, isLoading } = useAuth();
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<ProfileFormInputs>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      full_name: '',
      email: '',
      password: '',
      confirmPassword: ''
    }
  });

  // Pre-fill form with user data
  useEffect(() => {
    if (user) {
      setValue('full_name', user.full_name);
      setValue('email', user.email);
    }
  }, [user, setValue]);

  const onSubmit = async (data: ProfileFormInputs) => {
    if (!user) return;
    setSuccess(null);
    setError(null);

    try {
      // Filter out empty password fields to avoid sending them
      const updatePayload: Partial<ProfileFormInputs> = {
          full_name: data.full_name,
          email: data.email
      };
      if (data.password) {
          updatePayload.password = data.password;
      }

      await authService.updateUser(user.id, updatePayload);

      setSuccess(he.profile.updatedSuccess);
      await checkAuth(); // Refresh global auth state

      // Clear password fields
      setValue('password', '');
      setValue('confirmPassword', '');

    } catch (err: unknown) {
      console.error(err);
      let errorMessage: string = he.profile.updateFailed;
      if (err && typeof err === 'object' && 'response' in err) {
         // eslint-disable-next-line @typescript-eslint/no-explicit-any
         errorMessage = (err as any).response?.data?.message || errorMessage;
      } else if (err instanceof Error) {
         errorMessage = err.message;
      }
      setError(ensureHebrew(errorMessage, he.profile.updateFailed)||null);
    }
  };

  if (isLoading) {
      return (
        <PageShell className="flex items-center justify-center">
          <div className="text-sm text-muted-foreground">{he.profile.loading}</div>
        </PageShell>
      );
  }

  if (!user) {
      return null; // AuthContext redirect handles this
  }

  return (
    <PageShell>
      <div className="container mx-auto max-w-3xl px-4 space-y-8">
        <div className="text-center">
          <h2 className="text-3xl font-heading font-bold text-foreground">{he.profile.title}</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            {he.profile.subtitle}
          </p>
        </div>

        <div className="rounded-2xl border border-border bg-card shadow-sm overflow-hidden">
          <div className="flex items-center gap-4 border-b border-border px-6 py-5">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/10 text-primary text-2xl font-semibold">
              {user.full_name?.charAt(0).toUpperCase()}
            </div>
            <div>
              <h3 className="text-lg font-heading font-semibold text-foreground">{user.full_name}</h3>
              <p className="text-sm text-muted-foreground">
                {user.role === 'admin' ? he.profile.roleAdmin : he.profile.roleStandard}
              </p>
            </div>
          </div>

          <div className="px-6 py-6">
            {success && (
              <div className="mb-4 rounded-xl border border-primary/20 bg-primary/10 p-3 text-sm text-primary">
                {success}
              </div>
            )}
            {error && (
              <div className="mb-4 rounded-xl border border-destructive/20 bg-destructive/10 p-3 text-sm text-destructive">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-6">
                <div className="sm:col-span-4">
                  <label htmlFor="full_name" className="text-sm font-medium text-muted-foreground">
                    {he.auth.fields.fullName}
                  </label>
                  <Input
                    id="full_name"
                    type="text"
                    className={cn("mt-2 rounded-xl", errors.full_name && "border-destructive")}
                    {...register("full_name")}
                  />
                  {errors.full_name && (
                    <p className="mt-1 text-xs text-destructive">{errors.full_name.message}</p>
                  )}
                </div>

                <div className="sm:col-span-4">
                  <label htmlFor="email" className="text-sm font-medium text-muted-foreground">
                    {he.auth.fields.email}
                  </label>
                  <Input
                    id="email"
                    type="email"
                    className={cn("mt-2 rounded-xl", errors.email && "border-destructive")}
                    {...register("email")}
                  />
                  {errors.email && (
                    <p className="mt-1 text-xs text-destructive">{errors.email.message}</p>
                  )}
                </div>

                <div className="sm:col-span-6 border-t border-border pt-6">
                  <h4 className="text-base font-heading font-semibold text-foreground">{he.profile.changePasswordTitle}</h4>
                  <p className="text-sm text-muted-foreground">{he.profile.changePasswordSubtitle}</p>
                </div>

                <div className="sm:col-span-3">
                  <label htmlFor="password" className="text-sm font-medium text-muted-foreground">
                    {he.profile.newPasswordLabel}
                  </label>
                  <Input
                    id="password"
                    type="password"
                    className={cn("mt-2 rounded-xl", errors.password && "border-destructive")}
                    {...register("password")}
                  />
                  {errors.password && (
                    <p className="mt-1 text-xs text-destructive">{errors.password.message}</p>
                  )}
                </div>

                <div className="sm:col-span-3">
                  <label htmlFor="confirmPassword" className="text-sm font-medium text-muted-foreground">
                    {he.profile.confirmNewPasswordLabel}
                  </label>
                  <Input
                    id="confirmPassword"
                    type="password"
                    className={cn("mt-2 rounded-xl", errors.confirmPassword && "border-destructive")}
                    {...register("confirmPassword")}
                  />
                  {errors.confirmPassword && (
                    <p className="mt-1 text-xs text-destructive">{errors.confirmPassword.message}</p>
                  )}
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <Button
                  type="button"
                  variant="secondary"
                  className="rounded-xl"
                  onClick={() => router.back()}
                >
                  {he.profile.cancel}
                </Button>
                <Button type="submit" disabled={isSubmitting} className="rounded-xl">
                  {isSubmitting ? he.profile.saving : he.profile.saveChanges}
                </Button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </PageShell>
  );
}
