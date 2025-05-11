import { z } from "zod";

export const loginSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
  password: z.string().nonempty("Password is required"),
});

export const registerSchema = z.object({
  username: z.string().min(2, "Last name must be at least 2 characters"),
  email: z.string().email("Please enter a valid email address"),
  password: z.string().min(8, "Password must be at least 8 characters"),
  confirmPassword: z.string(),
}) .refine((data) => data.password === data.confirmPassword, {
  message: 'Passwords do not match',
  path: ['confirmPassword'],
});

export type LoginCredentials = z.infer<typeof loginSchema>;

export const stateParamSchema = z.string().min(1);

export const userSchema = z.object({
  id: z.string().or(z.number()),
  email: z.string().email(),
  username: z.string(),
})

export type User = z.infer<typeof userSchema>;

export const authResponseSchema = z.object({
  token: z.string(),
  refresh: z.string().optional(),
  user: userSchema.optional(),
  is_new_user: z.boolean().optional(),
});

export type AuthResponse = z.infer<typeof authResponseSchema>;
