import apiClient from "@/lib/axios";
import { API_ROUTES } from "@/lib/constants";
import { Conversation, GuestInfoUpdate } from "@/types";

export interface GuestsPaginationResponse {
  data: Conversation[];
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
  async getGuestInfo(guestId: string): Promise<Conversation> {
    const response = await apiClient.instance.get(
      API_ROUTES.GUEST.DETAIL(guestId)
    );
    return response.data as Conversation;
  },

  async updateGuestInfo(
    guestId: string,
    data: GuestInfoUpdate
  ): Promise<Conversation> {
    const response = await apiClient.instance.put(
      API_ROUTES.GUEST.DETAIL(guestId),
      data
    );
    return response.data as Conversation;
  },

  async getGuestsWithInterests(
    page: number,
    limit: number,
    keyword: string,
    interest_ids: string[]
  ): Promise<GuestsPaginationResponse> {
    const response = await apiClient.instance.post(API_ROUTES.GUEST.FILTER, {
      page,
      limit,
      keyword,
      interest_ids,
    });
    return response.data as GuestsPaginationResponse;
  },

  async deleteGuest(guestId: string): Promise<void> {
    await apiClient.instance.delete(API_ROUTES.GUEST.DELETE(guestId));
  },

  async deleteGuests(guestIds: string[]): Promise<void> {
    await apiClient.instance.post(API_ROUTES.GUEST.DELETE_MULTIPLE, {
      guest_ids: guestIds,
    });
  },
};
