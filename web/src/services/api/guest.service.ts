import apiClient from "@/lib/axios";
import { API_ROUTES } from "@/lib/constants";
import { GuestInfo, GuestInfoUpdate } from "@/types";

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
};
