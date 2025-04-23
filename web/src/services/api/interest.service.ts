import apiClient from "@/lib/axios";
import { API_ROUTES } from "@/lib/constants";
import { Interest, InterestData } from "@/types";

export interface InterestsPaginationResponse {
  data: Interest[];
  total: number;
  page: number;
  limit: number;
  has_next: boolean;
  has_prev: boolean;
  next_page: number | null;
  prev_page: number | null;
  total_pages: number;
}

export const interestService = {
  async getPaginationInterest(
    page: number,
    limit: number,
    status: string
  ): Promise<InterestsPaginationResponse> {
    const response = await apiClient.instance.get(API_ROUTES.INTEREST.GET, {
      params: { page, limit, status },
    });
    return response.data as InterestsPaginationResponse;
  },

  async getInterestById(interestId: string): Promise<Interest> {
    const response = await apiClient.instance.get(
      API_ROUTES.INTEREST.DETAIL(interestId)
    );
    return response.data as Interest;
  },

  async createInterest(interest: InterestData): Promise<Interest> {
    const response = await apiClient.instance.post(
      API_ROUTES.INTEREST.CREATE,
      interest
    );
    return response.data as Interest;
  },

  async updateInterest(
    interestId: string,
    interest: Interest
  ): Promise<Interest> {
    const response = await apiClient.instance.put(
      API_ROUTES.INTEREST.UPDATE(interestId),
      interest
    );
    return response.data as Interest;
  },

  async deleteInterest(interestId: string): Promise<void> {
    await apiClient.instance.delete(API_ROUTES.INTEREST.DELETE(interestId));
  },

  async deleteInterests(interestIds: string[]): Promise<void> {
    await apiClient.instance.post(API_ROUTES.INTEREST.DELETE_MULTIPLE, {
      interest_ids: interestIds,
    });
  },

  async downloadInterests(): Promise<Blob> {
    const response = await apiClient.instance.get(
      API_ROUTES.INTEREST.DOWNLOAD,
      {
        responseType: "blob",
      }
    );
    return response.data;
  },

  async uploadInterestFile(file: File): Promise<void> {
    const formData = new FormData();
    formData.append("file", file);

    await apiClient.instance.post(API_ROUTES.INTEREST.UPLOAD, formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
  },
};
