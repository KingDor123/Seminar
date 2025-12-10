import { z } from 'zod';

export const profileSchema = z.object({
  full_name: z.string().min(2, "Full name must be at least 2 characters"),
  email: z.string().email("Invalid email format"),
  password: z.string().optional().or(z.literal('')), // Optional, allow empty string to ignore
  confirmPassword: z.string().optional().or(z.literal(''))
}).refine((data) => {
  if (data.password && data.password.length > 0) {
      return data.password.length >= 6;
  }
  return true;
}, {
  message: "Password must be at least 6 characters if provided",
  path: ["password"]
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
});

export type ProfileFormInputs = z.infer<typeof profileSchema>;
