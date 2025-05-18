import apiClient from "@/lib/axios";
import { API_ROUTES } from "@/lib/constants";
import { Script, ScriptData } from "@/types";

export interface ScriptsPaginationResponse {
  data: Script[];
  total: number;
  page: number;
  limit: number;
  has_next: boolean;
  has_prev: boolean;
  next_page: number | null;
  prev_page: number | null;
  total_pages: number;
}

export const scriptService = {
  async getPaginationScript(
    page: number,
    limit: number,
    status: string
  ): Promise<ScriptsPaginationResponse> {
    const response = await apiClient.instance.get(API_ROUTES.SCRIPT.GET, {
      params: { page, limit, status },
    });
    return response.data as ScriptsPaginationResponse;
  },

  async getScriptById(scriptId: string): Promise<Script> {
    const response = await apiClient.instance.get(
      API_ROUTES.SCRIPT.DETAIL(scriptId)
    );
    return response.data as Script;
  },

  async createScript(script: ScriptData): Promise<Script> {
    const response = await apiClient.instance.post(
      API_ROUTES.SCRIPT.CREATE,
      script
    );
    return response.data as Script;
  },

  async updateScript(scriptId: string, script: ScriptData): Promise<Script> {
    const response = await apiClient.instance.put(
      API_ROUTES.SCRIPT.UPDATE(scriptId),
      script
    );
    return response.data as Script;
  },

  async deleteScript(scriptId: string): Promise<void> {
    await apiClient.instance.delete(API_ROUTES.SCRIPT.DELETE(scriptId));
  },

  async deleteScripts(scriptIds: string[]): Promise<void> {
    await apiClient.instance.post(API_ROUTES.SCRIPT.DELETE_MULTIPLE, {
      script_ids: scriptIds,
    });
  },

  async downloadScripts(): Promise<Blob> {
    const response = await apiClient.instance.get(API_ROUTES.SCRIPT.DOWNLOAD, {
      responseType: "blob",
    });
    return response.data;
  },

  async downloadScriptTemplate(): Promise<Blob> {
    const response = await apiClient.instance.get(
      API_ROUTES.SCRIPT.DOWNLOAD_TEMPLATE,
      {
        responseType: "blob",
      }
    );
    return response.data;
  },

  async uploadScriptFile(file: File): Promise<void> {
    const formData = new FormData();
    formData.append("file", file);

    await apiClient.instance.post(API_ROUTES.SCRIPT.UPLOAD, formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
  },
};
