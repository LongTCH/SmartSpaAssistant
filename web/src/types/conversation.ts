import { GuestInfo } from "./guest";
import { Interest } from "./interest";

export type ProviderType = "messenger" | "web";
export type ConversationalistType = "client" | "staff";
export type ChatAttachmentType = "image" | "video" | "audio" | "file";
export type ChatAssignmentType = "ai" | "me" | "all";

export interface Conversation {
  id: string;
  account_name: string;
  avatar: string;
  last_chat_message: Chat;
  provider: ProviderType;
  assigned_to: ChatAssignmentType;
  info?: GuestInfo;
  interests?: Interest[];
}

export interface ChatAttachmentPayload {
  url: string;
}

export interface ChatAttachment {
  type: ChatAttachmentType;
  payload?: ChatAttachmentPayload;
}

export interface ChatMessage {
  text: string;
  attachments: ChatAttachment[];
}

export interface ChatContent {
  side: ConversationalistType;
  message: ChatMessage;
}

export interface Chat {
  id: string;
  guest_id: string;
  content: ChatContent;
  created_at: string;
}
