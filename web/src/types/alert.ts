import { Notification } from "./notification";

export type AlertStatus = "unread" | "read";
export type AlertType = "system" | "custom";

export interface Alert {
  id: string;
  notification_id?: string;
  content: string;
  notification?: Notification;
  guest_id?: string;
  created_at: string;
  status: AlertStatus;
  type: AlertType;
}
