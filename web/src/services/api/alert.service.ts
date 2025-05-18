import apiClient from "@/lib/axios";
import { API_ROUTES } from "@/lib/constants";
import { Alert } from "@/types";

export interface AlertsPagingResponse {
  data: Alert[];
  total: number;
  skip: number;
  limit: number;
  has_next: boolean;
  has_prev: boolean;
}

export const alertService = {
  async getPagingAlert(
    skip: number,
    limit: number,
    notification_id: string
  ): Promise<AlertsPagingResponse> {
    const response = await apiClient.instance.get(API_ROUTES.ALERT.GET, {
      params: { skip, limit, notification: notification_id },
    });
    return response.data as AlertsPagingResponse;
  },
};
