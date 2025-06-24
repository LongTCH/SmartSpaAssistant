export interface NotificationParams {
  index: number;
  param_name: string;
  param_type: string;
  description: string;
  validation?: string;
}
export interface Notification {
  id: string;
  label: string;
  description: string;
  status: "published" | "draft";
  color: string;
  params: NotificationParams[] | null;
  content: string | null;
  created_at: string;
}
export interface NotificationData {
  label: string;
  description: string;
  status: "published" | "draft";
  color: string;
  params: NotificationParams[] | null;
  content: string | null;
}
