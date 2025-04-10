import apiClient from "@/lib/axios";
import { API_ROUTES } from "@/lib/constants";
import { Conversation, Chat } from "@/types";

export interface ConversationsPagingResponse {
  data: Conversation[];
  total: number;
  skip: number;
  limit: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface ChatPagingResponse {
  data: Chat[];
  total: number;
  skip: number;
  limit: number;
  has_next: boolean;
  has_prev: boolean;
}

export const conversationService = {
  async getPagingConversation(
    skip: number,
    limit: number
  ): Promise<ConversationsPagingResponse> {
    const response = await apiClient.instance.get(API_ROUTES.CONVERSATION.GET, {
      params: { skip, limit },
    });
    return response.data as ConversationsPagingResponse;
  },

  async getChatById(
    guestId: string,
    skip: number,
    limit: number
  ): Promise<ChatPagingResponse> {
    const response = await apiClient.instance.get(
      API_ROUTES.CONVERSATION.DETAIL(guestId),
      {
        params: { skip, limit },
      }
    );
    return response.data as ChatPagingResponse;
  },
};
