import { z } from 'zod';
import { he } from '../constants/he';

export const registerSchema = z.object({
  full_name: z.string().min(2, he.validation.fullNameMin),
  email: z.string().email(he.validation.invalidEmail),
  password: z.string().min(6, he.validation.passwordMin),
  confirmPassword: z.string()
}).refine((data) => data.password === data.confirmPassword, {
  message: he.validation.passwordsDontMatch,
  path: ["confirmPassword"],
});

export const loginSchema = z.object({
  email: z.string().email(he.validation.invalidEmail),
  password: z.string().min(1, he.validation.passwordRequired),
});

export type RegisterFormInputs = z.infer<typeof registerSchema>;
export type LoginFormInputs = z.infer<typeof loginSchema>;
