import apiClient from "@/lib/axios";
import { API_ROUTES } from "@/lib/constants";
import { GuestInfo, GuestInfoUpdate } from "@/types";

export interface GuestsPaginationResponse {
  data: GuestInfo[];
  total: number;
  page: number;
  limit: number;
  has_next: boolean;
  has_prev: boolean;
  next_page: number | null;
  prev_page: number | null;
  total_pages: number;
}

export const guestService = {
  async getGuestInfo(guestId: string): Promise<GuestInfo> {
    const response = await apiClient.instance.get(
      API_ROUTES.GUEST.DETAIL(guestId)
    );
    return response.data as GuestInfo;
  },

  async updateGuestInfo(
    guestId: string,
    data: GuestInfoUpdate
  ): Promise<GuestInfo> {
    const response = await apiClient.instance.put(
      API_ROUTES.GUEST.DETAIL(guestId),
      data
    );
    return response.data as GuestInfo;
  },

  async getGuestsWithInterests(
    page: number,
    limit: number
  ): Promise<GuestsPaginationResponse> {
    const response = await apiClient.instance.get(API_ROUTES.GUEST.GET, {
      params: { page, limit },
    });
    return response.data as GuestsPaginationResponse;
  },
};
