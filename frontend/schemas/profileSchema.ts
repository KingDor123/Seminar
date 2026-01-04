import { z } from 'zod';
import { he } from '../constants/he';

export const profileSchema = z.object({
  full_name: z.string().min(2, he.validation.fullNameMin),
  email: z.string().email(he.validation.invalidEmail),
  password: z.string().optional().or(z.literal('')), // Optional, allow empty string to ignore
  confirmPassword: z.string().optional().or(z.literal(''))
}).refine((data) => {
  if (data.password && data.password.length > 0) {
      return data.password.length >= 6;
  }
  return true;
}, {
  message: he.validation.passwordMinOptional,
  path: ["password"]
}).refine((data) => data.password === data.confirmPassword, {
  message: he.validation.passwordsDontMatch,
  path: ["confirmPassword"],
});

export type ProfileFormInputs = z.infer<typeof profileSchema>;
