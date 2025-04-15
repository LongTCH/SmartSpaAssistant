import { Conversation } from "@/types";
import ConversationInfo from "./ConversationInfo";
import { useState, useEffect, useRef } from "react";
import { conversationService } from "@/services/api/conversation.service";
import { useApp } from "@/context/app-context";
import { WS_MESSAGES } from "@/lib/constants";

interface ConversationInfoListProps {
  selectedConversation: Conversation | null;
  setSelectedConversation: React.Dispatch<
    React.SetStateAction<Conversation | null>
  >;
  handleSelectConversation: (conversation: Conversation) => void;
  onNewMessage?: (conversation: Conversation) => void; // Callback when there's a new message
  unreadConversations?: Set<string>; // Set of conversation IDs with unread messages
}

export default function ConversationInfoList(props: ConversationInfoListProps) {
  const conversationLimit = 20;
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [hasNext, setHasNext] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Use the WebSocket context instead of creating a new connection
  const { registerMessageHandler } = useApp();

  const fetchConversations = async (isInitialLoad = false) => {
    try {
      // Nếu đang tải, không fetch thêm
      if (isLoading) return;

      setIsLoading(true);

      // Sử dụng độ dài của mảng hiện tại làm giá trị skip
      const skip = isInitialLoad ? 0 : conversations.length;

      const response = await conversationService.getPagingConversation(
        skip,
        conversationLimit
      );

      if (response.data.length !== 0) {
        if (isInitialLoad) {
          // First page, replace data
          setConversations(response.data);

          // Auto-select first conversation on page initialization
          if (!props.selectedConversation) {
            props.setSelectedConversation(response.data[0]);
          }
        } else {
          // Next page, append data
          setConversations((prevConversations) => [
            ...prevConversations,
            ...response.data,
          ]);
        }
        setHasNext(response.has_next || false);
      }
    } catch (error) {
      console.error("Error fetching conversations:", error);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle new conversation from WebSocket
  const handleNewConversation = (conversation: Conversation) => {
    setConversations((prevConversations) => {
      // Check if conversation already exists
      const existingIndex = prevConversations.findIndex(
        (conv) => conv.id === conversation.id
      );

      // Create a new list to update state
      let newConversations = [...prevConversations];

      if (existingIndex !== -1) {
        // If exists, remove from old position
        newConversations.splice(existingIndex, 1);
      }

      // Add new conversation to the top of the list
      newConversations = [conversation, ...newConversations];

      return newConversations;
    });

    // If it's not the currently selected conversation, notify parent about new message
    if (
      props.selectedConversation?.id !== conversation.id &&
      props.onNewMessage
    ) {
      props.onNewMessage(conversation);
    }
  };

  // Register WebSocket handler
  useEffect(() => {
    // Register handler for "INBOX" messages
    const unregisterInbox = registerMessageHandler(
      WS_MESSAGES.INBOX,
      (data) => {
        handleNewConversation(data as Conversation);
      }
    );
    const unregisterSentiment = registerMessageHandler(
      WS_MESSAGES.UPDATE_SENTIMENT,
      (data) => {
        const conversation = data as Conversation;
        setConversations((prevConversations) =>
          prevConversations.map((conv) =>
            conv.id === conversation.id
              ? { ...conv, sentiment: conversation.sentiment }
              : conv
          )
        );
      }
    );

    // Cleanup when component unmounts
    return () => {
      unregisterInbox();
      unregisterSentiment();
    };
  }, [props.selectedConversation, registerMessageHandler]);

  useEffect(() => {
    fetchConversations(true);
  }, []);

  return (
    <div
      className="flex-1 overflow-auto"
      onScroll={(e) => {
        const target = e.target as HTMLDivElement;
        // Check when user scrolls near the bottom
        if (target.scrollHeight - target.scrollTop - target.clientHeight < 50) {
          // Only load more if there's more data and not currently loading
          if (hasNext && !isLoading) {
            fetchConversations();
          }
        }
      }}
    >
      {Array.isArray(conversations) && conversations.length > 0 ? (
        <>
          {conversations.map((item, index) => (
            <ConversationInfo
              key={item.id || index}
              item={item}
              onClick={() => props.handleSelectConversation(item)}
              isSelected={props.selectedConversation?.id === item.id}
              isUnread={props.unreadConversations?.has(item.id) || false}
            />
          ))}
          {isLoading && (
            <div className="p-4 text-center text-gray-500">
              <span className="inline-block animate-spin mr-2">⟳</span>
              Loading...
            </div>
          )}
        </>
      ) : (
        <div className="flex-1 overflow-auto flex items-center justify-center text-gray-500">
          No conversations yet
        </div>
      )}
    </div>
  );
}
