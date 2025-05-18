import { Notification } from "./notification";

export interface Alert {
  id: string;
  notification_id: string;
  content: string;
  notification: Notification;
  guest_id: string;
  created_at: string;
}
