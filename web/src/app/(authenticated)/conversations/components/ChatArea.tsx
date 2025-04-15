"use client";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Frown, Info, ChevronDown, Smile } from "lucide-react";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { useState, useEffect, useRef } from "react";
import { conversationService } from "@/services/api/conversation.service";
import { Conversation, Chat, SentimentType } from "@/types";
import { getBadge } from "./ConversationInfo";
import { useApp } from "@/context/app-context";
import { MarkdownContent } from "@/components/markdown-content";
import { AttachmentViewer } from "@/components/attachment-viewer";
import { WS_MESSAGES } from "@/lib/constants";

interface ChatAreaProps {
  selectedConversation: Conversation | null;
  onNewMessageAdded?: (chat: Chat) => void;
  onConversationRead?: (conversationId: string) => void; // New prop for marking as read
}

export default function ChatArea(props: ChatAreaProps) {
  const [isLoadingMessages, setIsLoadingMessages] = useState<boolean>(false);
  const [chatSkip, setChatSkip] = useState<number>(0);
  const [chatList, setChatList] = useState<Chat[]>([]);
  const [sentiment, setSentiment] = useState<string>("neutral");
  const messageLimit = 20; // Limit the number of messages loaded each time

  const chatContainerRef = useRef<HTMLDivElement>(null);
  const prevScrollHeight = useRef<number>(0);
  const prevScrollTop = useRef<number>(0);

  // State to manage new messages and scroll state
  const [hasNewMessage, setHasNewMessage] = useState<boolean>(false);
  const [isAtBottom, setIsAtBottom] = useState<boolean>(true);
  const [hasMoreMessages, setHasMoreMessages] = useState<boolean>(false);
  const [isConversationSwitching, setIsConversationSwitching] = useState(false);

  // Use the WebSocket context from app-context
  const { registerMessageHandler } = useApp();

  const getSentimentPopover = (sentiment: string) => {
    if (sentiment === "neutral") {
      return <></>;
    }

    return (
      <Popover>
        {sentiment === "negative" ? (
          <PopoverTrigger asChild>
            <Button variant="link" size="icon" className="w-5 h-5 rounded-full">
              <Frown className="h-6 w-6 text-red-500" />
            </Button>
          </PopoverTrigger>
        ) : (
          <PopoverTrigger asChild>
            <Button variant="link" size="icon" className="w-5 h-5 rounded-full">
              <Smile className="h-6 w-6 text-green-500" />
            </Button>
          </PopoverTrigger>
        )}
        {/* Popover content */}
        <PopoverContent className="w-80 p-4">
          <div className="space-y-2">
            <h4 className="font-medium">Dự đoán cảm xúc</h4>
            <p className="text-sm text-gray-500">
              AI dự đoán cảm xúc của người dùng trong đoạn hội thoại là{" "}
              <strong>
                {sentiment === "negative" ? "tiêu cực" : "tích cực"}
              </strong>
              .
            </p>
          </div>
        </PopoverContent>
      </Popover>
    );
  };

  const fetchConversationMessages = async (
    conversationId: string,
    loadMore: boolean = false
  ) => {
    try {
      setIsLoadingMessages(true);
      const response = await conversationService.getChatById(
        conversationId,
        chatSkip,
        messageLimit
      );

      if (response && response.data) {
        // Sắp xếp tin nhắn theo thời gian để đảm bảo thứ tự đúng
        const sortedMessages = [...response.data].sort(
          (a, b) =>
            new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
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
    } catch (error) {
      console.error("Error fetching conversation messages:", error);
      if (!loadMore) setChatList([]);
      setHasMoreMessages(false);
      throw error;
    } finally {
      setIsLoadingMessages(false);
    }
  };

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
  const handleIncomingMessage = (conversation: Conversation) => {
    // Only process if the message belongs to the current conversation
    if (props.selectedConversation?.id === conversation.id) {
      if (conversation.last_message) {
        // Create a new Chat object from the conversation data
        const newChat: Chat = {
          id: `temp-${Date.now()}`, // Temporary ID
          guest_id: conversation.id,
          content: conversation.last_message,
          created_at: conversation.last_message_at,
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
        if (props.onNewMessageAdded) {
          props.onNewMessageAdded(newChat);
        }
      }
      if (sentiment !== conversation.sentiment) {
        setSentiment(conversation.sentiment as string);
      }
    }
  };

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
  }, [props.selectedConversation?.id, isAtBottom]);

  useEffect(() => {
    const unregister = registerMessageHandler(
      WS_MESSAGES.UPDATE_SENTIMENT,
      (data) => {
        const conversation = data as Conversation;
        if (props.selectedConversation?.id === conversation.id) {
          setSentiment(conversation.sentiment as string);
        }
      }
    );

    return () => {
      unregister();
    };
  }, [props.selectedConversation?.id]);

  // Handle conversation change
  useEffect(() => {
    if (props.selectedConversation?.id) {
      // Reset state before fetching new data
      setChatSkip(0);
      setIsConversationSwitching(true);
      setChatList([]); // Clear old messages immediately to avoid displaying incorrect data
      setHasMoreMessages(false);
      setHasNewMessage(false);
      setIsAtBottom(true);
      setSentiment(props.selectedConversation.sentiment as string);

      // Add a small timeout to ensure state has been updated
      setTimeout(() => {
        if (props.selectedConversation?.id) {
          fetchConversationMessages(props.selectedConversation.id)
            .then((response) => {
              if (response.data && response.data.length > 0) {
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
            .catch((error) => {
              console.error("Error fetching messages:", error);
              setIsConversationSwitching(false);
            });
        }
      }, 50);
    }
  }, [props.selectedConversation?.id]);

  // Separate useEffect to handle scroll when conversation changes
  useEffect(() => {
    // Chỉ cuộn xuống khi thay đổi hội thoại và dữ liệu đã được tải
    if (
      props.selectedConversation?.id &&
      !isLoadingMessages &&
      chatList.length > 0 &&
      chatSkip === 0 &&
      isConversationSwitching
    ) {
      scrollToBottom();
    }
  }, [
    isLoadingMessages,
    props.selectedConversation?.id,
    chatSkip === 0,
    isConversationSwitching,
  ]);

  // Update useEffect to not call API when loading
  useEffect(() => {
    // Only call when skip > 0 (not the first time) and a conversation is selected
    if (chatSkip > 0 && props.selectedConversation?.id && !isLoadingMessages) {
      setIsLoadingMessages(true);
      fetchConversationMessages(props.selectedConversation.id, true).finally(
        () => {
          setIsLoadingMessages(false);
        }
      );
    }
  }, [chatSkip, props.selectedConversation?.id]);

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
      props.selectedConversation?.id &&
      !isLoadingMessages &&
      chatList.length > 0 &&
      props.onConversationRead
    ) {
      props.onConversationRead(props.selectedConversation.id);
    }
  }, [props.selectedConversation?.id, isLoadingMessages, chatList]);

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
  }, [chatList, isLoadingMessages]);

  return (
    <div className="flex-1 flex flex-col bg-gray-50">
      {/* Chat Header */}
      <div className="p-3 border-b bg-white flex items-center gap-2">
        <div className="flex items-center justify-between flex-1">
          <div className="flex items-center space-x-2">
            <Avatar className="w-10 h-10">
              <AvatarImage src={props.selectedConversation?.avatar} />
              <AvatarFallback>?</AvatarFallback>
            </Avatar>
            <span className="text-sm font-medium text-gray-800">
              {props.selectedConversation?.account_name}
            </span>
            {getBadge(props.selectedConversation?.provider)}
            {sentiment && getSentimentPopover(sentiment as string)}
          </div>

          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">Assign to</span>
            <Select defaultValue="ai">
              <SelectTrigger className="w-[120px] h-8">
                <SelectValue placeholder="AI" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ai">AI</SelectItem>
                <SelectItem value="me">Me</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <Popover>
          <PopoverTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 rounded-full bg-blue-100 text-blue-600 hover:bg-blue-200 hover:text-blue-700"
            >
              <Info className="h-4 w-4" />
              <span className="sr-only">Information</span>
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-80 p-4">
            <div className="space-y-2">
              <h4 className="font-medium">Chat Information</h4>
              <p className="text-sm text-gray-500">
                This conversation is being handled by AI support. Response time
                may vary based on query complexity.
              </p>
            </div>
          </PopoverContent>
        </Popover>
      </div>

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
              !isLoadingMessages
            ) {
              // Save current scroll height and position before loading more messages
              prevScrollHeight.current = target.scrollHeight;
              prevScrollTop.current = target.scrollTop;

              // Increase skip to load older messages
              const newSkip = chatSkip + messageLimit;
              setChatSkip(newSkip);
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
                      <AvatarImage src={props.selectedConversation?.avatar} />
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
                {props.selectedConversation
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
              New message
            </Button>
          </div>
        )}

        {/* Fixed System Message at Bottom */}
        <div className="p-2 border-t bg-white sticky bottom-0 z-10">
          <div className="text-xs text-gray-500 text-center bg-gray-50 py-2 rounded border border-gray-200">
            Sorry, direct messaging is not supported.
          </div>
        </div>
      </div>
    </div>
  );
}
