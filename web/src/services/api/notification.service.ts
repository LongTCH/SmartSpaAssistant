import apiClient from "@/lib/axios";
import { API_ROUTES } from "@/lib/constants";
import { Notification, NotificationData } from "@/types";

export interface NotificationsPaginationResponse {
  data: Notification[];
  total: number;
  page: number;
  limit: number;
  has_next: boolean;
  has_prev: boolean;
  next_page: number | null;
  prev_page: number | null;
  total_pages: number;
}

export const notificationService = {
  async getPaginationNotification(
    page: number,
    limit: number,
    status: string
  ): Promise<NotificationsPaginationResponse> {
    const response = await apiClient.instance.get(API_ROUTES.NOTIFICATION.GET, {
      params: { page, limit, status },
    });
    return response.data as NotificationsPaginationResponse;
  },

  async getNotificationById(notificationId: string): Promise<Notification> {
    const response = await apiClient.instance.get(
      API_ROUTES.NOTIFICATION.DETAIL(notificationId)
    );
    return response.data as Notification;
  },

  async createNotification(
    notification: NotificationData
  ): Promise<Notification> {
    const response = await apiClient.instance.post(
      API_ROUTES.NOTIFICATION.CREATE,
      notification
    );
    return response.data as Notification;
  },

  async updateNotification(
    notificationId: string,
    notification: Notification
  ): Promise<Notification> {
    const response = await apiClient.instance.put(
      API_ROUTES.NOTIFICATION.UPDATE(notificationId),
      notification
    );
    return response.data as Notification;
  },

  async deleteNotification(notificationId: string): Promise<void> {
    await apiClient.instance.delete(
      API_ROUTES.NOTIFICATION.DELETE(notificationId)
    );
  },

  async deleteNotifications(notification_ids: string[]): Promise<void> {
    await apiClient.instance.post(API_ROUTES.NOTIFICATION.DELETE_MULTIPLE, {
      notification_ids: notification_ids,
    });
  },
  async downloadNotifications(): Promise<Blob> {
    const response = await apiClient.instance.get(
      API_ROUTES.NOTIFICATION.DOWNLOAD,
      {
        responseType: "blob",
      }
    );
    return response.data;
  },

  async downloadNotificationTemplate(): Promise<Blob> {
    const response = await apiClient.instance.get(
      API_ROUTES.NOTIFICATION.DOWNLOAD_TEMPLATE,
      {
        responseType: "blob",
      }
    );
    return response.data;
  },

  async uploadNotifications(file: File): Promise<void> {
    const formData = new FormData();
    formData.append("file", file);

    await apiClient.instance.post(API_ROUTES.NOTIFICATION.UPLOAD, formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
  },
};
