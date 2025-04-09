import apiClient from "@/lib/axios";
import { handleResponse } from "./helper";
import { API_ROUTES } from "../../lib/constants";

export const spaceService = {
    createSpace: async (data: { name: string; description: string; privacy_status: boolean }) => {
      const response = await apiClient.post(API_ROUTES.SPACE.ALL, data);
      return handleResponse(response.data);
    },
    getSpacePublic: async () => {
      const response = await apiClient.get(API_ROUTES.SPACE.PUBLIC);
      return handleResponse(response.data);
    },
    getYourSpaces: async () => {
      const response = await apiClient.get(API_ROUTES.SPACE.MINE);
      return handleResponse(response.data);
    },
    getSpaceById: async (spaceId: string) => {
      const response = await apiClient.get(`${API_ROUTES.SPACE.ALL}/${spaceId}`);
      return handleResponse(response.data);
    },
    getDocumentBySpace: async (spaceId: string) => {
      const response = await apiClient.get(`${API_ROUTES.SPACE.DETAIL}/${spaceId}/documents`);
      return handleResponse(response.data);
    },
};