import axios, { AxiosRequestConfig, AxiosResponse } from 'axios';
import Cookies from 'js-cookie';
import { getAccessToken, setAccessToken } from './auth';
import { ApiResponse } from '@/schemas/api';
import { APP_ROUTES } from './constants';

const apiBaseUrl = (
  typeof window == "undefined" && process.env.NEXT_PUBLIC_SSR_API_URL) 
  || process.env.NEXT_PUBLIC_API_URL 
  || 'http://localhost:8080';
const baseURL = `${apiBaseUrl}`;

const api = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, 
});

api.interceptors.request.use(
  (config) => {
    const token = getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      const refreshToken = Cookies.get('refreshToken');
      if (refreshToken) {
        try {
          const refreshResponse = await axios.post(`${baseURL}/auth/refresh`, {
            refreshToken,
          });
          
          if (refreshResponse.data?.data?.token) {
            const newToken = refreshResponse.data.data.token;
            setAccessToken(newToken);
            
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
            return axios(originalRequest);
          }
        } catch (refreshError) {
        }
      }
      
      if (typeof window !== 'undefined') {
        Cookies.remove('refreshToken');
        window.location.href = APP_ROUTES.LOGIN;
      }
    }
    
    return Promise.reject(error);
  }
);

export const apiClient = {
  get: <T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<ApiResponse<T>>> => {
    return api.get<ApiResponse<T>>(url, config);
  },
  
  post: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<ApiResponse<T>>> => {
    return api.post<ApiResponse<T>>(url, data, config);
  },
  
  put: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<ApiResponse<T>>> => {
    return api.put<ApiResponse<T>>(url, data, config);
  },
  
  patch: <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<ApiResponse<T>>> => {
    return api.patch<ApiResponse<T>>(url, data, config);
  },
  
  delete: <T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<ApiResponse<T>>> => {
    return api.delete<ApiResponse<T>>(url, config);
  },
  
  instance: api
};

export default apiClient;
