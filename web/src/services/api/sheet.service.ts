import apiClient from "@/lib/axios";
import { API_ROUTES } from "@/lib/constants";
import { Sheet, SheetRow } from "@/types";

export interface SheetsPaginationResponse {
  data: Sheet[];
  total: number;
  page: number;
  limit: number;
  has_next: boolean;
  has_prev: boolean;
  next_page: number | null;
  prev_page: number | null;
  total_pages: number;
}

export interface SheetRowsPagingResponse {
  data: SheetRow[];
  total: number;
  skip: number;
  limit: number;
  has_next: boolean;
  has_prev: boolean;
}

export const sheetService = {
  async uploadSheet(
    name: string,
    description: string,
    status: string,
    file: File
  ): Promise<Sheet> {
    const formData = new FormData();
    formData.append("name", name);
    formData.append("description", description);
    formData.append("status", status);
    formData.append("file", file);

    const response = await apiClient.instance.post(
      API_ROUTES.SHEET.CREATE,
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
          Accept: "application/json",
        },
      }
    );
    return response.data as Sheet;
  },

  async getPaginationSheet(
    page: number,
    limit: number,
    status: string
  ): Promise<SheetsPaginationResponse> {
    const response = await apiClient.instance.get(API_ROUTES.SHEET.GET, {
      params: { page, limit, status },
    });
    return response.data as SheetsPaginationResponse;
  },

  async getSheetById(sheetId: string): Promise<Sheet> {
    const response = await apiClient.instance.get(
      API_ROUTES.SHEET.DETAIL(sheetId)
    );
    return response.data as Sheet;
  },

  async getPagingSheetRows(
    sheetId: string,
    skip: number,
    limit: number
  ): Promise<SheetRowsPagingResponse> {
    const response = await apiClient.instance.get(
      API_ROUTES.SHEET.GET_ROWS(sheetId),
      {
        params: { skip, limit },
      }
    );
    return response.data as SheetRowsPagingResponse;
  },

  async updateSheet(
    sheetId: string,
    name: string,
    description: string,
    status: string
  ): Promise<Sheet> {
    const response = await apiClient.instance.put(
      API_ROUTES.SHEET.UPDATE(sheetId),
      {
        name,
        description,
        status,
      }
    );
    return response.data as Sheet;
  },

  async deleteSheet(sheetId: string): Promise<void> {
    await apiClient.instance.delete(API_ROUTES.SHEET.DELETE(sheetId));
  },

  async deleteSheets(sheetIds: string[]): Promise<void> {
    await apiClient.instance.post(API_ROUTES.SHEET.DELETE_MULTIPLE, {
      sheet_ids: sheetIds,
    });
  },

  async downloadSheet(sheetId: string): Promise<Blob> {
    const response = await apiClient.instance.get(
      API_ROUTES.SHEET.DOWNLOAD(sheetId),
      {
        responseType: "blob",
      }
    );
    return response.data;
  },
};
