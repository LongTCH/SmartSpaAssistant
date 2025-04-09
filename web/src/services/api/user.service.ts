import apiClient from "@/lib/axios";
import { handleResponse } from "./helper";

export const userService = {
    getProfile: async () => {
      const response = await apiClient.get('/users/me');
      return handleResponse(response.data);
    },
    
    updateProfile: async (data: any) => {
      const response = await apiClient.put('/users/me', data);
      return handleResponse(response.data);
    },
  };