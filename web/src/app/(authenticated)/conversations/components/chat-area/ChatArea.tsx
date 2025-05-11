"use client";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { ChevronDown } from "lucide-react";

import { useState, useEffect, useRef, useCallback } from "react";
import { conversationService } from "@/services/api/conversation.service";
import { guestService } from "@/services/api/guest.service";
import { Conversation, Chat } from "@/types";
import { useApp } from "@/context/app-context";
import { MarkdownContent } from "@/components/markdown-content";
import { AttachmentViewer } from "@/components/attachment-viewer";
import { WS_MESSAGES } from "@/lib/constants";
import { GuestInfoModal } from "../../../../../components/guest-info/GuestInfoModal";
import { TagRow } from "./TagRow";
import ChatHeader from "./ChatHeader";

interface ChatAreaProps {
  selectedConversationId: string | null; // Changed from selectedConversation object to just ID
  onNewMessageAdded?: (chat: Chat) => void;
  onConversationRead?: (conversationId: string) => void;
  onConversationUpdated?: (conversation: Conversation) => void; // Prop remains
}

const messageLimit = 20; // Limit the number of messages loaded each time
export default function ChatArea(props: ChatAreaProps) {
  const {
    selectedConversationId,
    onConversationRead,
    onNewMessageAdded,
    onConversationUpdated,
  } = props; // Destructure props

  const [isLoadingMessages, setIsLoadingMessages] = useState<boolean>(false);
  const [chatList, setChatList] = useState<Chat[]>([]);
  const [_sentiment, _setSentiment] = useState<string | null>(null);
  const [conversationData, setConversationData] = useState<Conversation | null>(
    null
  ); // Add state for full conversation data
  const [_isLoadingConversation, _setIsLoadingConversation] =
    useState<boolean>(false); // Add loading state for conversation
  const [showUserInfo, setShowUserInfo] = useState(false);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const prevScrollHeight = useRef<number>(0);
  const prevScrollTop = useRef<number>(0);

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
          messageLimit
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
        _setSentiment(response.sentiment as string);
        return response;
      } catch {
        setConversationData(null);
        return null;
      } finally {
        _setIsLoadingConversation(false);
      }
    },
    []
  ); // _setIsLoadingConversation, setConversationData, _setSentiment are stable setters

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
        // Update sentiment if it changed (already exists)
        // if (sentiment !== conversation.sentiment) {
        //   setSentiment(conversation.sentiment as string);
        // }
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

  useEffect(() => {
    const unregister = registerMessageHandler(
      WS_MESSAGES.UPDATE_SENTIMENT,
      (data) => {
        const conversation = data as Conversation;
        if (selectedConversationId === conversation.id) {
          _setSentiment(conversation.sentiment as string);
        }
      }
    );

    return () => {
      unregister();
    };
  }, [selectedConversationId, registerMessageHandler]);

  // Handle conversation change
  useEffect(() => {
    if (selectedConversationId) {
      // Reset state before fetching new data
      setIsConversationSwitching(true);
      setChatList([]); // Clear old messages immediately to avoid displaying incorrect data
      setHasMoreMessages(false);
      setHasNewMessage(false);
      setIsAtBottom(true);
      _setSentiment("neutral");
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
    <div className="flex-1 flex flex-col bg-gray-50">
      {/* Chat Header */}
      <ChatHeader
        conversationData={conversationData}
        setShowUserInfo={setShowUserInfo}
        selectedConversationId={selectedConversationId || ""}
        onConversationUpdated={handleLocalConversationUpdate} // Pass handler
      />
      {/* Chat Messages Area */}
      <div className="h-[10vh] flex-1 flex flex-col relative">
        {/* Scrollable Messages - Thay đổi từ flex-col-reverse thành flex-col thông thường */}
        <div
          ref={chatContainerRef}
          className="flex-1 overflow-y-auto p-4 space-y-4 flex flex-col"
          onScroll={(e) => {
            const target = e.target as HTMLDivElement;
            // Check if user is near the bottom (within 20px)
            checkScrollPosition();

            // Load more messages when user scrolls to the top (infinite scroll up)
            if (
              !isConversationSwitching &&
              target.scrollTop < 50 &&
              hasMoreMessages &&
              !isLoadingMessages &&
              selectedConversationId
            ) {
              // Save current scroll height and position before loading more messages
              prevScrollHeight.current = target.scrollHeight;
              prevScrollTop.current = target.scrollTop;

              // Load more messages by calling the function directly
              fetchConversationMessages(selectedConversationId, true);
            }
          }}
        >
          {/* Loading indicator for more messages */}
          {isLoadingMessages && chatList.length > 0 && (
            <div className="text-center text-gray-500 py-2">
              <span className="inline-block animate-spin mr-2">⟳</span>
              Loading more messages...
            </div>
          )}

          {/* Message list - Bây giờ hiển thị theo thứ tự thông thường */}
          {isLoadingMessages && chatList.length === 0 ? (
            <div className="flex justify-center items-center h-full">
              <div className="text-center text-gray-500">
                <span className="inline-block animate-spin mr-2">⟳</span>
                Loading messages...
              </div>
            </div>
          ) : chatList && chatList.length > 0 ? (
            <>
              {chatList.map((chat, index) =>
                chat.content.side === "client" ? (
                  // Client/User Message - Now using dark theme (previously light)
                  <div
                    key={chat.id || `chat-${index}`}
                    className="flex items-start space-x-2 max-w-[80%]"
                  >
                    <Avatar>
                      <AvatarImage src="/placeholder.svg?height=40&width=40" />
                      <AvatarFallback>?</AvatarFallback>
                    </Avatar>
                    <div>
                      <div className="bg-indigo-500 p-3 rounded-lg shadow-sm">
                        {chat.content.message.text ? (
                          <MarkdownContent
                            content={chat.content.message.text}
                            className="text-sm"
                            isDarkTheme={true}
                          />
                        ) : null}

                        {/* Hiển thị attachment nếu có */}
                        {chat.content.message.attachments &&
                          chat.content.message.attachments.length > 0 && (
                            <AttachmentViewer
                              attachments={chat.content.message.attachments}
                              className={
                                chat.content.message.text ? "mt-2" : ""
                              }
                              isDarkTheme={true}
                            />
                          )}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {new Date(chat.created_at).toLocaleString("vi-VN", {
                          day: "2-digit",
                          month: "2-digit",
                          year: "numeric",
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </div>
                    </div>
                  </div>
                ) : (
                  // Staff/Bot Message - Now using light theme (previously dark)
                  <div
                    key={chat.id || `chat-${index}`}
                    className="flex items-start justify-end space-x-2 max-w-[80%] ml-auto"
                  >
                    <div>
                      <div className="bg-gray-200 p-3 rounded-lg shadow-sm">
                        {chat.content.message.text ? (
                          <MarkdownContent
                            content={chat.content.message.text}
                            className="text-sm"
                            isDarkTheme={false}
                          />
                        ) : null}

                        {/* Hiển thị attachment nếu có */}
                        {chat.content.message.attachments &&
                          chat.content.message.attachments.length > 0 && (
                            <AttachmentViewer
                              attachments={chat.content.message.attachments}
                              className={
                                chat.content.message.text ? "mt-2" : ""
                              }
                              isDarkTheme={false}
                            />
                          )}
                      </div>
                      <div className="text-xs text-gray-500 mt-1 text-right">
                        {new Date(chat.created_at).toLocaleString("vi-VN", {
                          day: "2-digit",
                          month: "2-digit",
                          year: "numeric",
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </div>
                    </div>
                    <Avatar className="w-8 h-8">
                      <AvatarImage src="/placeholder.svg?height=32&width=32" />
                      <AvatarFallback>SA</AvatarFallback>
                    </Avatar>
                  </div>
                )
              )}
            </>
          ) : (
            <div className="flex justify-center items-center h-full">
              <div className="text-gray-500">
                {selectedConversationId
                  ? "No messages available"
                  : "Please select a conversation"}
              </div>
            </div>
          )}
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
      {/* User Info Modal */}
      <GuestInfoModal
        open={showUserInfo}
        onOpenChange={(open) => {
          setShowUserInfo(open);
          // Nếu đóng modal và có conversation đã chọn, cập nhật lại thông tin từ API
          if (!open && selectedConversationId) {
            // Fetch lại thông tin khách hàng mà không cần fetch lại tin nhắn chat
            fetchConversationData(selectedConversationId)
              .then((updatedConversation) => {
                // Báo lên component cha rằng conversation đã được cập nhật nếu có callback
                if (onConversationUpdated && updatedConversation) {
                  onConversationUpdated(updatedConversation);
                }
              })
              .catch(() => {});
          }
        }}
        guestId={selectedConversationId || ""}
      />
    </div>
  );
}
