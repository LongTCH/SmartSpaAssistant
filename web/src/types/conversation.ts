import { Interest } from "./interest";

export type ProviderType = "messenger" | "web";
export type ConversationalistType = "client" | "staff";
export type ChatAttachmentType = "image" | "video" | "audio" | "file";
export type SentimentType = "positive" | "negative" | "neutral";
export type ChatAssignmentType = "ai" | "me" | "all";

export interface Conversation {
  id: string;
  account_name: string;
  last_message_at: string;
  avatar: string;
  last_message: ChatContent;
  provider: ProviderType;
  sentiment: SentimentType;
  assigned_to: ChatAssignmentType;
  fullname: string;
  email: string;
  phone: string;
  address: string;
  gender: string;
  birthday: string;
  interests: Interest[];
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
