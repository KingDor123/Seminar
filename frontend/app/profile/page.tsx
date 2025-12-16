'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { profileSchema, ProfileFormInputs } from '../../schemas/profileSchema';
import { useAuth } from '../../context/AuthContext';
import { authService } from '../../services/authService';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

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
      
      setSuccess('Profile updated successfully!');
      await checkAuth(); // Refresh global auth state
      
      // Clear password fields
      setValue('password', '');
      setValue('confirmPassword', '');

    } catch (err: unknown) {
      console.error(err);
      let errorMessage = 'Failed to update profile';
      if (err && typeof err === 'object' && 'response' in err) {
         // eslint-disable-next-line @typescript-eslint/no-explicit-any
         errorMessage = (err as any).response?.data?.message || errorMessage;
      } else if (err instanceof Error) {
         errorMessage = err.message;
      }
      setError(errorMessage);
    }
  };

  if (isLoading) {
      return <div className="flex justify-center items-center min-h-screen">Loading user profile...</div>;
  }

  if (!user) {
      return null; // AuthContext redirect handles this
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8 dark:bg-gray-900">
      <div className="max-w-3xl mx-auto space-y-8">
        
        {/* Header */}
        <div className="text-center">
            <h2 className="text-3xl font-extrabold text-gray-900 dark:text-white">Your Profile</h2>
            <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                Manage your personal information and security settings.
            </p>
        </div>

        {/* Profile Card */}
        <div className="bg-white shadow overflow-hidden sm:rounded-lg dark:bg-gray-800">
            <div className="px-4 py-5 sm:px-6 flex items-center border-b border-gray-200 dark:border-gray-700">
                 <div className="h-16 w-16 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 text-2xl font-bold mr-4">
                    {user.full_name?.charAt(0).toUpperCase()}
                 </div>
                 <div>
                     <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white">
                        {user.full_name}
                     </h3>
                     <p className="mt-1 max-w-2xl text-sm text-gray-500 dark:text-gray-400">
                        {user.role === 'admin' ? 'Administrator' : 'Standard User'}
                     </p>
                 </div>
            </div>

            <div className="px-4 py-5 sm:p-6">
                {success && (
                    <div className="mb-4 rounded-md bg-green-50 p-4 text-sm text-green-700 border border-green-200 dark:bg-green-900/30 dark:text-green-200 dark:border-green-800">
                        {success}
                    </div>
                )}
                {error && (
                    <div className="mb-4 rounded-md bg-red-50 p-4 text-sm text-red-700 border border-red-200 dark:bg-red-900/30 dark:text-red-200 dark:border-red-800">
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                    <div className="grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-6">
                        
                        <div className="sm:col-span-4">
                            <label htmlFor="full_name" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                                Full Name
                            </label>
                            <div className="mt-1">
                                <input
                                    type="text"
                                    id="full_name"
                                    className={`shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white p-2 border ${errors.full_name ? 'border-red-500' : ''}`}
                                    {...register("full_name")}
                                />
                                {errors.full_name && <p className="mt-1 text-xs text-red-500">{errors.full_name.message}</p>}
                            </div>
                        </div>

                        <div className="sm:col-span-4">
                            <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                                Email Address
                            </label>
                            <div className="mt-1">
                                <input
                                    type="email"
                                    id="email"
                                    className={`shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white p-2 border ${errors.email ? 'border-red-500' : ''}`}
                                    {...register("email")}
                                />
                                {errors.email && <p className="mt-1 text-xs text-red-500">{errors.email.message}</p>}
                            </div>
                        </div>

                        <div className="sm:col-span-6 border-t border-gray-200 pt-6 dark:border-gray-700">
                             <h4 className="text-base font-medium text-gray-900 dark:text-white mb-4">Change Password</h4>
                        </div>

                        <div className="sm:col-span-3">
                            <label htmlFor="password" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                                New Password <span className="text-gray-400 font-normal">(Optional)</span>
                            </label>
                            <div className="mt-1">
                                <input
                                    type="password"
                                    id="password"
                                    className={`shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white p-2 border ${errors.password ? 'border-red-500' : ''}`}
                                    {...register("password")}
                                />
                                {errors.password && <p className="mt-1 text-xs text-red-500">{errors.password.message}</p>}
                            </div>
                        </div>

                        <div className="sm:col-span-3">
                            <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                                Confirm New Password
                            </label>
                            <div className="mt-1">
                                <input
                                    type="password"
                                    id="confirmPassword"
                                    className={`shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-white p-2 border ${errors.confirmPassword ? 'border-red-500' : ''}`}
                                    {...register("confirmPassword")}
                                />
                                {errors.confirmPassword && <p className="mt-1 text-xs text-red-500">{errors.confirmPassword.message}</p>}
                            </div>
                        </div>

                    </div>
                    
                    <div className="flex justify-end pt-5">
                         <button
                            type="button"
                            onClick={() => router.back()}
                            className="bg-white py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-gray-200 dark:border-gray-600 dark:hover:bg-gray-600 mr-3"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={isSubmitting}
                            className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                        >
                            {isSubmitting ? 'Saving...' : 'Save Changes'}
                        </button>
                    </div>
                </form>
            </div>
        </div>

      </div>
    </div>
  );
}
