"use client";

import { Button } from "@/components/ui/button";
import { ChevronDown } from "lucide-react";

import { useState, useEffect, useRef, useCallback } from "react";
import { conversationService } from "@/services/api/conversation.service";
import { guestService } from "@/services/api/guest.service";
import { Conversation, Chat } from "@/types";
import { useApp } from "@/context/app-context";
import { WS_MESSAGES } from "@/lib/constants";
import { TagRow } from "./TagRow";
import ChatHeader from "./ChatHeader";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface ChatAreaProps {
  selectedConversationId: string | null; // Changed from selectedConversation object to just ID
  onNewMessageAdded?: (chat: Chat) => void;
  onConversationRead?: (conversationId: string) => void;
  onConversationUpdated?: (conversation: Conversation) => void; // Prop remains
  toggleSupportPanel?: () => void; // Added this line
}

const MESSAGE_LIMIT = 20; // Limit the number of messages loaded each time
const TIMESTAMP_GROUPING_INTERVAL_MINUTES = 5; // Display timestamp if previous message is older than this

export default function ChatArea(props: ChatAreaProps) {
  const {
    selectedConversationId,
    onConversationRead,
    onNewMessageAdded,
    onConversationUpdated,
    toggleSupportPanel, // Added this line
  } = props; // Destructure props

  const [isLoadingMessages, setIsLoadingMessages] = useState<boolean>(false);
  const [chatList, setChatList] = useState<Chat[]>([]);
  const [conversationData, setConversationData] = useState<Conversation | null>(
    null
  ); // Add state for full conversation data
  const [_isLoadingConversation, _setIsLoadingConversation] =
    useState<boolean>(false); // Add loading state for conversation
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const prevScrollHeight = useRef<number>(0);
  const prevScrollTop = useRef<number>(0);
  const isLoadingMore = useRef<boolean>(false); // Ref to track if loading more is in progress

  // Ref to hold the latest onConversationRead prop to avoid issues with unstable function references
  const onConversationReadRef = useRef(onConversationRead);
  useEffect(() => {
    onConversationReadRef.current = onConversationRead;
  }, [onConversationRead]);

  // Ref to hold the current chatList for use in useCallback without adding chatList as a dependency
  const chatListRef = useRef(chatList);
  useEffect(() => {
    chatListRef.current = chatList;
  }, [chatList]);

  // State to manage new messages and scroll state
  const [hasNewMessage, setHasNewMessage] = useState<boolean>(false);
  const [isAtBottom, setIsAtBottom] = useState<boolean>(true);
  const [hasMoreMessages, setHasMoreMessages] = useState<boolean>(false);
  const [isConversationSwitching, setIsConversationSwitching] = useState(false);

  // Use the WebSocket context from app-context
  const { registerMessageHandler } = useApp();

  const fetchConversationMessages = useCallback(
    async (conversationIdParam: string, loadMore: boolean = false) => {
      try {
        setIsLoadingMessages(true);

        // Use chatListRef to get current length without adding chatList.length to dependencies
        const currentChatList = chatListRef.current;
        const skip = loadMore ? currentChatList.length : 0;

        const response = await conversationService.getChatById(
          conversationIdParam,
          skip,
          MESSAGE_LIMIT
        );

        if (response && response.data) {
          // Sắp xếp tin nhắn theo thời gian để đảm bảo thứ tự đúng
          const sortedMessages = [...response.data].sort(
            (a, b) =>
              new Date(a.created_at).getTime() -
              new Date(b.created_at).getTime()
          );

          if (loadMore && sortedMessages.length > 0) {
            // Khi tải thêm tin nhắn cũ, thêm vào đầu danh sách
            setChatList((prevMessages) => [...sortedMessages, ...prevMessages]);
          } else {
            setChatList(sortedMessages);
          }
          setHasMoreMessages(response.has_next || false);
        } else {
          if (!loadMore) {
            setChatList([]);
          }
          setHasMoreMessages(false);
        }

        return response;
      } catch {
        if (!loadMore) setChatList([]);
        setHasMoreMessages(false);
      } finally {
        setIsLoadingMessages(false);
      }
    },
    // Dependencies now only include stable setters or truly external stable dependencies
    [setIsLoadingMessages, setChatList, setHasMoreMessages] // conversationService is assumed stable
  );

  // Add a new function to fetch conversation data by ID
  const fetchConversationData = useCallback(
    async (conversationIdParam: string) => {
      try {
        _setIsLoadingConversation(true);
        const response = await guestService.getGuestInfo(conversationIdParam);
        setConversationData(response);
        return response;
      } catch {
        setConversationData(null);
        return null;
      } finally {
        _setIsLoadingConversation(false);
      }
    },
    []
  ); // _setIsLoadingConversation, setConversationData are stable setters

  // useEffect to automatically load more messages if the content is not scrollable initially
  useEffect(() => {
    const checkAndLoadMoreIfNeeded = async () => {
      if (
        chatContainerRef.current &&
        chatContainerRef.current.scrollHeight <=
          chatContainerRef.current.clientHeight && // Not scrollable
        hasMoreMessages && // Still more messages to load
        !isLoadingMessages && // Not currently loading (main loading)
        selectedConversationId && // Conversation is selected
        !isLoadingMore.current && // Not currently loading more (scroll or auto)
        !isConversationSwitching // Not in the middle of switching conversations
      ) {
        // Prevent multiple rapid calls
        if (isLoadingMore.current) return;
        isLoadingMore.current = true;

        // Store current scroll height and top position before loading new messages
        prevScrollHeight.current = chatContainerRef.current.scrollHeight;
        prevScrollTop.current = chatContainerRef.current.scrollTop; // Should be 0 if not scrollable

        await fetchConversationMessages(selectedConversationId, true);

        isLoadingMore.current = false;
      }
    };

    // Call after a short delay to allow DOM to update after chatList changes
    // and after conversation switching is complete.
    if (!isConversationSwitching) {
      const timeoutId = setTimeout(checkAndLoadMoreIfNeeded, 250); // Adjusted delay
      return () => clearTimeout(timeoutId);
    }
  }, [
    chatList,
    hasMoreMessages,
    isLoadingMessages,
    selectedConversationId,
    fetchConversationMessages,
    isConversationSwitching, // Ensure this runs after switching is done
  ]);

  // Scroll to latest messages with enhanced reliability
  const scrollToBottom = () => {
    if (chatContainerRef.current) {
      const scrollElement = chatContainerRef.current;
      // Use a slight timeout to ensure DOM is fully updated
      setTimeout(() => {
        scrollElement.scrollTop = scrollElement.scrollHeight;
        setHasNewMessage(false);
        setIsAtBottom(true);
      }, 100);
    }
  };

  // Handle new messages from WebSocket
  const handleIncomingMessage = useCallback(
    (conversation: Conversation) => {
      // Only process if the message belongs to the current conversation
      if (selectedConversationId === conversation.id) {
        // Update conversation data state to reflect potential changes (like interests)
        setConversationData(conversation); // <--- Add this line

        if (conversation.last_chat_message) {
          // Create a new Chat object from the conversation data
          const newChat: Chat = {
            id: `temp-${Date.now()}`, // Temporary ID
            guest_id: conversation.id,
            content: conversation.last_chat_message.content,
            created_at: conversation.last_chat_message.created_at,
          };

          // Add new message to chat list
          setChatList((prevChats) => [...prevChats, newChat]);

          // Show new message notification only when user has scrolled up
          if (!isAtBottom) {
            setHasNewMessage(true);
            // Don't scroll automatically - user will click notification to scroll
          } else {
            // Only auto-scroll when user is already at the bottom
            setTimeout(() => {
              scrollToBottom();
            }, 100);
          }

          // Call the callback if provided
          if (onNewMessageAdded) {
            onNewMessageAdded(newChat);
          }
        }
      }
    },

    [selectedConversationId, isAtBottom, onNewMessageAdded]
  );

  // Check scroll position to determine if user is at the bottom
  const checkScrollPosition = () => {
    if (chatContainerRef.current) {
      const scrollPosition = chatContainerRef.current.scrollTop;
      const scrollHeight = chatContainerRef.current.scrollHeight;
      const clientHeight = chatContainerRef.current.clientHeight;

      // Consider user at bottom if within 20px of the bottom
      const isBottom = scrollHeight - scrollPosition - clientHeight < 20;
      setIsAtBottom(isBottom);

      // Clear new message notification if scrolled to bottom
      if (isBottom && hasNewMessage) {
        setHasNewMessage(false);
      }
    }
  };

  // Scroll handler to load more messages when scrolling to the top
  const handleScroll = async () => {
    if (
      chatContainerRef.current &&
      chatContainerRef.current.scrollTop === 0 &&
      !isLoadingMessages &&
      hasMoreMessages &&
      selectedConversationId &&
      !isLoadingMore.current // Check ref to prevent multiple calls
    ) {
      isLoadingMore.current = true; // Set loading more flag
      // Store current scroll height and top position before loading new messages
      prevScrollHeight.current = chatContainerRef.current.scrollHeight;
      prevScrollTop.current = chatContainerRef.current.scrollTop; // Should be 0

      await fetchConversationMessages(selectedConversationId, true);
      isLoadingMore.current = false; // Reset loading more flag
    }
    checkScrollPosition(); // Also check if user is at bottom after any scroll
  };

  // Register WebSocket message handler for INBOX messages
  useEffect(() => {
    const unregister = registerMessageHandler(WS_MESSAGES.INBOX, (data) => {
      const conversation = data as Conversation;
      handleIncomingMessage(conversation);
    });

    return () => {
      unregister();
    };
  }, [selectedConversationId, registerMessageHandler, handleIncomingMessage]);

  // Handle conversation change
  useEffect(() => {
    if (selectedConversationId) {
      // Reset state before fetching new data
      setIsConversationSwitching(true);
      setChatList([]); // Clear old messages immediately to avoid displaying incorrect data
      setHasMoreMessages(false);
      setHasNewMessage(false);
      setIsAtBottom(true);
    }
  }, [selectedConversationId]);

  useEffect(() => {
    if (isConversationSwitching && selectedConversationId) {
      fetchConversationMessages(selectedConversationId)
        .then((response) => {
          if (response && response.data && response.data.length > 0) {
            // Make sure to scroll to bottom after messages are loaded
            requestAnimationFrame(() => {
              scrollToBottom();
              setTimeout(() => {
                setIsConversationSwitching(false);
              }, 200);
            });
          } else {
            setIsConversationSwitching(false);
          }
        })
        .catch(() => {
          setIsConversationSwitching(false);
        });
    }
  }, [
    isConversationSwitching,
    fetchConversationMessages,
    selectedConversationId,
  ]);

  // Separate useEffect to handle scroll when conversation changes
  useEffect(() => {
    // Chỉ cuộn xuống khi thay đổi hội thoại và dữ liệu đã được tải
    if (
      selectedConversationId &&
      !isLoadingMessages &&
      chatList.length > 0 &&
      isConversationSwitching
    ) {
      scrollToBottom();
    }
  }, [
    isLoadingMessages,
    selectedConversationId,
    isConversationSwitching,
    chatList.length,
  ]);

  // Add useEffect to handle maintaining scroll position
  useEffect(() => {
    if (chatContainerRef.current && prevScrollHeight.current > 0) {
      const newScrollHeight = chatContainerRef.current.scrollHeight;
      const heightDifference = newScrollHeight - prevScrollHeight.current;

      chatContainerRef.current.scrollTop =
        prevScrollTop.current + heightDifference;

      // Reset after handling
      prevScrollHeight.current = 0;
      prevScrollTop.current = 0;
    }
  }, [chatList]);

  // Add a function to mark conversation as read when user views messages
  useEffect(() => {
    // When a conversation is selected and messages are loaded, mark it as read
    if (
      selectedConversationId &&
      !isLoadingMessages &&
      chatList.length > 0 &&
      onConversationReadRef.current // Use the ref's current value
    ) {
      onConversationReadRef.current(selectedConversationId);
    }
  }, [
    selectedConversationId,
    // onConversationRead removed from dependencies
    isLoadingMessages,
    chatList.length,
  ]);

  // Force scroll to bottom when chat list changes and we're at initial load
  useEffect(() => {
    if (chatList.length > 0 && !isLoadingMessages) {
      // Chỉ tự động cuộn xuống khi lần đầu tải tin nhắn
      // hoặc khi chuyển đổi hội thoại
      if (isConversationSwitching) {
        setTimeout(() => {
          scrollToBottom();
        }, 200);
      }
    }
  }, [chatList, isLoadingMessages, chatList.length, isConversationSwitching]);

  // Effect to load conversation data when conversation ID changes
  useEffect(() => {
    if (selectedConversationId) {
      fetchConversationData(selectedConversationId);
    } else {
      setConversationData(null);
    }
  }, [selectedConversationId, fetchConversationData, setConversationData]); // Added fetchConversationData and setConversationData (stable)

  // Handler for when conversation data is updated (e.g., assignment change in header)
  const handleLocalConversationUpdate = (updatedConversation: Conversation) => {
    setConversationData(updatedConversation);
    // Also notify the parent component if needed
    if (onConversationUpdated) {
      onConversationUpdated(updatedConversation);
    }
  };

  return (
    <div className="flex-1 flex flex-col bg-gray-50 min-w-0">
      {" "}
      {/* Added min-w-0 here */}
      <ChatHeader
        conversationData={conversationData}
        toggleSupportPanel={toggleSupportPanel} // Changed from setShowUserInfo
        selectedConversationId={selectedConversationId || ""}
        onConversationUpdated={handleLocalConversationUpdate}
      />
      {/* Chat messages area */}
      <div
        ref={chatContainerRef}
        onScroll={handleScroll} // Add your scroll handler if it exists for other features like loading more
        className="flex-1 overflow-y-auto p-4 space-y-1" // Reduced space-y for tighter packing if timestamps are hidden
      >
        {isLoadingMessages && chatList.length === 0 ? (
          <div className="flex justify-center items-center h-full">
            <div className="text-center">
              {/* You can use a spinner component here */}
              <p className="text-gray-500">Loading messages...</p>
            </div>
          </div>
        ) : (
          <TooltipProvider>
            {chatList.map((chat, index) => {
              const currentMessageDate = new Date(chat.created_at); // Ensure chat.created_at is valid
              let showTimestamp = true;

              if (index > 0) {
                const previousMessageDate = new Date(
                  chatList[index - 1].created_at
                );
                const diffInMilliseconds =
                  currentMessageDate.getTime() - previousMessageDate.getTime();
                const intervalMilliseconds =
                  TIMESTAMP_GROUPING_INTERVAL_MINUTES * 60 * 1000;

                if (diffInMilliseconds < intervalMilliseconds) {
                  // Optional: if you also want to group by sender blocks, you could add:
                  // && chat.content.side === chatList[index - 1].content.side
                  showTimestamp = false;
                }
              }

              // Determine message alignment and style based on sender
              const isUserMessage = chat.content.side === "client";
              const isAgentOrBotMessage = chat.content.side === "staff";

              return (
                <div
                  key={chat.id}
                  className={`flex flex-col ${
                    isUserMessage ? "items-end" : "items-start"
                  } mb-1`}
                >
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <div
                        className={`max-w-xs md:max-w-md lg:max-w-lg xl:max-w-2xl p-2 px-3 rounded-lg shadow-sm ${
                          isUserMessage
                            ? "bg-blue-500 text-white"
                            : isAgentOrBotMessage // staff messages are gray as per image
                            ? "bg-gray-200 text-gray-800"
                            : "bg-gray-200 text-gray-800" // Default for other received messages (e.g. bot if different from staff)
                        }`}
                      >
                        <p className="text-sm whitespace-pre-wrap">
                          {chat.content.message.text || ""}
                        </p>
                      </div>
                    </TooltipTrigger>
                    <TooltipContent side="left">
                      <p>
                        {currentMessageDate.toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                          second: "2-digit",
                        })}{" "}
                        {currentMessageDate.toLocaleDateString([], {
                          day: "2-digit",
                          month: "2-digit",
                          year: "numeric",
                        })}
                      </p>
                    </TooltipContent>
                  </Tooltip>
                  {showTimestamp && (
                    <div
                      className={`text-xs text-gray-400 mt-1 px-1 ${
                        isUserMessage ? "text-right w-full" : "text-left w-full"
                      }`}
                    >
                      {currentMessageDate.toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}{" "}
                      {currentMessageDate.toLocaleDateString([], {
                        day: "2-digit",
                        month: "2-digit",
                        year: "numeric",
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </TooltipProvider>
        )}
        {/* Placeholder for new message indicator or other elements */}
        {/* {hasNewMessage && !isAtBottom && <NewMessageIndicator onClick={scrollToBottom} />} */}
      </div>
      {/* New message notification button */}
      {hasNewMessage && (
        <div className="absolute bottom-16 right-4">
          <Button
            onClick={scrollToBottom}
            size="sm"
            className="flex items-center gap-1.5 shadow-lg bg-indigo-600 text-white hover:bg-indigo-700 transition-all duration-200 font-medium px-4 py-2 rounded-full animate-pulse"
          >
            <ChevronDown className="w-4 h-4" />
            Tin nhắn mới
          </Button>
        </div>
      )}
      {/* Fixed System Message at Bottom */}
      <div className="p-2 border-t bg-white sticky bottom-0 z-10">
        {/* Hiển thị các nhãn của cuộc hội thoại */}
        {conversationData && conversationData.interests && (
          <TagRow interests={conversationData.interests} />
        )}
        <div className="text-xs text-gray-500 text-center bg-gray-50 py-2 rounded border border-gray-200">
          Xin lỗi, nhắn tin trực tiếp không được hỗ trợ.
        </div>
      </div>
    </div>
  );
}
