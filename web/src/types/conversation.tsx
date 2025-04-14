export type ProviderType = "messenger" | "web";
export type ConversationalistType = "client" | "staff";
export type ChatAttachmentType = "image" | "video" | "audio" | "file";

export interface Conversation {
  id: string;
  account_name: string;
  last_message_at: string;
  avatar: string;
  last_message: ChatContent;
  provider: ProviderType;
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
