import api from '../lib/api';
import { LoginFormInputs, RegisterFormInputs } from '../schemas/authSchema';

export interface AuthResponse {
  message: string;
  user: {
    id: number;
    full_name: string;
    email: string;
    role: string;
  };
  token?: string;
}

export const authService = {
  register: async (data: RegisterFormInputs): Promise<AuthResponse> => {
    // We send only the necessary fields to the backend (exclude confirmPassword)
    const { confirmPassword, ...registerData } = data;
    const response = await api.post<AuthResponse>('/auth/register', registerData);
    return response.data;
  },

  login: async (data: LoginFormInputs): Promise<AuthResponse> => {
    const response = await api.post<AuthResponse>('/auth/login', data);
    return response.data;
  },

  logout: async (): Promise<void> => {
    await api.post('/auth/logout');
  },

  getMe: async (): Promise<AuthResponse['user']> => {
     try {
       const response = await api.get<{ user: AuthResponse['user'] }>('/auth/me');
       return response.data.user;
     } catch (error) {
       throw error;
     }
  },

  updateUser: async (userId: number, data: Partial<AuthResponse['user']> & { password?: string }): Promise<AuthResponse['user']> => {
    const response = await api.put<AuthResponse['user']>(`/users/${userId}`, data);
    return response.data;
  }
};
