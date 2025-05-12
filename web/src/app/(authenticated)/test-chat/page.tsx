"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useApp } from "@/context/app-context";
import { useMediaQuery } from "@/hooks/use-media-query";

// Import our components
import {
  ChatMessage,
  TypingIndicator,
  EmptyChatState,
} from "./components/ChatMessage";
import {
  ConversationSidebar,
  Conversation,
  saveConversation,
  loadConversations,
  deleteAllConversations,
  deleteConversation,
  updateConversationTitle as updateConversationTitleInStorage,
} from "./components/ConversationSidebar";
import { ChatHeader } from "./components/ChatHeader";
import { ChatInput } from "./components/ChatInput";

// Define WebSocket message types
const WS_MESSAGES = {
  TEST_CHAT: "TEST_CHAT",
  CONNECTED: "CONNECTED",
  PING: "PING",
  PONG: "PONG",
};

interface Message {
  id: string;
  sender: "You" | "Assistant";
  text: string;
  type: "human" | "ai";
}

interface ChatResponse {
  id: string; // This is conversationId
  message: string;
}

export default function TestChatPage() {
  // State
  // const [userId, setUserId] = useState<string | null>(null); // REMOVED
  const [messages, setMessages] = useState<Message[]>([]);
  const [processingConversationId, setProcessingConversationId] = useState<
    string | null
  >(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [currentConversationId, setCurrentConversationId] =
    useState<string>(""); // ID of the currently active conversation

  // Check if mobile view
  const isMobile = !useMediaQuery("(min-width: 640px)");

  // Refs
  const chatBoxRef = useRef<HTMLDivElement>(null);
  // Map to track pending responses per conversation
  const responseMapRef = useRef<
    Record<
      string,
      {
        resolve: (data: ChatResponse) => void;
        reject: (error: Error) => void;
        timeoutId: NodeJS.Timeout;
      }
    >
  >({});

  // WebSocket from AppContext
  const {
    sendWebSocketMessage,
    registerMessageHandler,
    isWebSocketConnected,
    setActiveNavTab,
  } = useApp();

  // Set active tab when component mounts
  useEffect(() => {
    setActiveNavTab("test-chat");
  }, [setActiveNavTab]);

  // Create a new conversation
  const handleNewConversation = useCallback(
    (title: string = "New Conversation") => {
      const newId = crypto.randomUUID();
      setCurrentConversationId(newId);
      localStorage.setItem("test-chat-last-opened-id", newId);
      setMessages([]);

      const newConversationEntry: Conversation = {
        id: newId,
        title: title,
        date: new Date().toISOString(),
        messages: [],
      };
      saveConversation(newConversationEntry);
      setConversations(loadConversations()); // Reload to get the new list
    },
    // saveConversation & loadConversations are stable imports, setConversations, setCurrentConversationId, setMessages are stable state setters
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  );

  // Initialize conversations and set active conversation
  useEffect(() => {
    const loadedConvos = loadConversations();

    if (loadedConvos.length === 0) {
      // No conversations exist, create a new one.
      const newInitialConversationId = crypto.randomUUID();
      const newInitialConversation: Conversation = {
        id: newInitialConversationId,
        title: "New Conversation", // Default title
        date: new Date().toISOString(),
        messages: [],
      };
      saveConversation(newInitialConversation);
      localStorage.setItem(
        "test-chat-last-opened-id",
        newInitialConversationId
      );

      setConversations([newInitialConversation]);
      setCurrentConversationId(newInitialConversationId);
      setMessages([]); // Start with empty messages for the new conversation
    } else {
      // Conversations exist, load the last opened or most recent.
      setConversations(loadedConvos);

      let activeConversationIdToSet = "";
      let activeMessagesToSet: Message[] = [];

      const lastOpenedConvoId = localStorage.getItem(
        "test-chat-last-opened-id"
      );
      const lastOpenedConvo = loadedConvos.find(
        (c) => c.id === lastOpenedConvoId
      );

      if (lastOpenedConvo) {
        activeConversationIdToSet = lastOpenedConvo.id;
        activeMessagesToSet = lastOpenedConvo.messages || [];
      } else if (loadedConvos.length > 0) {
        // Default to the most recent conversation (e.g., first in a sorted list, or just the first one)
        activeConversationIdToSet = loadedConvos[0].id;
        activeMessagesToSet = loadedConvos[0].messages || [];
        localStorage.setItem(
          "test-chat-last-opened-id",
          activeConversationIdToSet
        ); // Update last opened
      }

      setCurrentConversationId(activeConversationIdToSet);
      setMessages(activeMessagesToSet);
    }
  }, []); // Runs once on mount

  // Refactor addMessage to accept conversationId explicitly and use fresh conversations list
  const addMessage = useCallback(
    (
      conversationId: string,
      sender: "You" | "Assistant",
      text: string,
      type: "human" | "ai"
    ) => {
      const newMessage: Message = {
        id: crypto.randomUUID(),
        sender,
        text,
        type,
      };

      // Load the latest conversations from storage to avoid stale state
      const currentStoredConversations = loadConversations();
      const existingConversation = currentStoredConversations.find(
        (c) => c.id === conversationId
      );

      const prevMessages = existingConversation?.messages || [];
      const updatedMessages = [...prevMessages, newMessage];

      let conversationTitle = existingConversation?.title || "New Conversation";
      if (
        type === "human" &&
        prevMessages.filter((m) => m.type === "human").length === 0 &&
        (!existingConversation ||
          !existingConversation.title ||
          existingConversation.title === "New Conversation")
      ) {
        conversationTitle = text.substring(0, 30) || "New Conversation";
      }

      const conversationToSave: Conversation = {
        id: conversationId,
        title: conversationTitle,
        date: existingConversation?.date || new Date().toISOString(),
        messages: updatedMessages,
      };

      saveConversation(conversationToSave);
      setConversations(loadConversations());

      if (conversationId === currentConversationId) {
        setMessages(updatedMessages);
      }
    },
    [currentConversationId]
  );

  // Get chat response via WebSocket, passing conversationId to differentiate
  const getChatResponse = useCallback(
    async (
      conversationId: string, // This is the conversationId
      messageText: string
    ): Promise<ChatResponse> => {
      if (!conversationId || !messageText || !isWebSocketConnected) {
        throw new Error("Cannot send message at this time");
      }
      return new Promise((resolve, reject) => {
        const timeoutId = setTimeout(() => {
          const entry = responseMapRef.current[conversationId];
          if (entry) {
            console.log("Request timed out for conversation:", conversationId);
            entry.reject(new Error("Response timeout"));
            delete responseMapRef.current[conversationId];
            // Tự động xóa trạng thái xử lý khi timeout
            setProcessingConversationId(null);
            // Hiển thị thông báo lỗi trong UI
            addMessage(
              conversationId,
              "Assistant",
              "Xin lỗi, đã xảy ra lỗi timeout khi xử lý yêu cầu của bạn. Vui lòng thử lại sau.",
              "ai"
            );
          }
        }, 150000);
        console.log("Sending message for conversation:", conversationId);
        responseMapRef.current[conversationId] = { resolve, reject, timeoutId };
        sendWebSocketMessage({
          message: WS_MESSAGES.TEST_CHAT,
          data: { id: conversationId, message: messageText },
        });
      });
    },
    [
      isWebSocketConnected,
      sendWebSocketMessage,
      addMessage,
      setProcessingConversationId,
    ]
  );

  // Register WebSocket message handler (must be after addMessage is defined)
  useEffect(() => {
    const unregister = registerMessageHandler(
      WS_MESSAGES.TEST_CHAT,
      (data: any) => {
        console.log("Received message:", data);
        let chatData = data as ChatResponse;
        try {
          // Phương pháp mới: xử lý tất cả các định dạng dữ liệu có thể có
          console.log("Raw data type:", typeof data);

          // TRƯỜNG HỢP 1: Nhận thẳng object
          if (data && typeof data === "object") {
            chatData = { id: data.id, message: data.message };
          }

          // Dừng hiệu ứng đang xử lý với ID tương ứng
          if (processingConversationId === chatData.id) {
            setProcessingConversationId(null);
          } // Tìm entry trong responseMapRef và giải quyết Promise
          const entry = responseMapRef.current[chatData.id];
          if (entry) {
            console.log("Found pending request, clearing timeout");
            clearTimeout(entry.timeoutId);
            entry.resolve(chatData);
            delete responseMapRef.current[chatData.id];
          }
          // Nếu không tìm thấy entry (không có Promise đang đợi), thì cập nhật UI trực tiếp
          else if (chatData.id === currentConversationId) {
            addMessage(chatData.id, "Assistant", chatData.message, "ai");
          }
        } catch (error) {
          console.error("Error processing WebSocket response:", error);
        }
      }
    );
    return unregister;
  }, [
    registerMessageHandler,
    currentConversationId,
    addMessage,
    processingConversationId,
  ]);

  // Scroll to bottom when messages change
  useEffect(() => {
    if (chatBoxRef.current) {
      chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight;
    }
  }, [messages]);

  // Handle sending a message
  const handleSendMessage = useCallback(
    async (messageText: string) => {
      if (
        !messageText.trim() ||
        !currentConversationId || // Ensure there's an active conversation
        processingConversationId === currentConversationId
      ) {
        return;
      }

      // Kiểm tra kết nối WebSocket trước khi gửi tin nhắn
      if (!isWebSocketConnected) {
        addMessage(
          currentConversationId,
          "Assistant",
          "Xin lỗi, kết nối đến máy chủ đã bị mất. Vui lòng làm mới trang và thử lại.",
          "ai"
        );
        return;
      }

      const convoIdToSendMessageTo = currentConversationId;

      addMessage(convoIdToSendMessageTo, "You", messageText, "human");

      try {
        setProcessingConversationId(convoIdToSendMessageTo);
        const chatRes = await getChatResponse(
          convoIdToSendMessageTo,
          messageText
        );
        // The response 'chatRes.id' should match 'convoIdToSendMessageTo'
        // if the backend correctly uses the ID it received.
        addMessage(chatRes.id, "Assistant", chatRes.message, "ai");
      } catch (error) {
        console.error("Error getting chat response:", error);
        addMessage(
          convoIdToSendMessageTo,
          "Assistant",
          "Xin lỗi, tôi không thể xử lý yêu cầu của bạn lúc này. Vui lòng thử lại sau.",
          "ai"
        );
      } finally {
        setProcessingConversationId(null);
      }
    },
    [
      addMessage,
      getChatResponse,
      currentConversationId,
      processingConversationId,
      isWebSocketConnected,
    ]
  );
  // Handle selecting a conversation
  const handleConversationSelect = useCallback(
    (id: string) => {
      setCurrentConversationId(id);
      localStorage.setItem("test-chat-last-opened-id", id);
      setProcessingConversationId(null);

      const allConvos = loadConversations(); // Load fresh conversations
      const selectedConversation = allConvos.find((conv) => conv.id === id);
      setMessages(selectedConversation?.messages || []);
    },
    [] // loadConversations is stable, state setters are stable
  );

  // Delete specific conversation
  const handleDeleteConversation = useCallback(
    (id: string) => {
      // Xóa conversation từ localStorage
      deleteConversation(id);

      // Reload danh sách conversation
      const remainingConversations = loadConversations();
      setConversations(remainingConversations);

      // Nếu conversation đã xóa là conversation hiện tại
      if (id === currentConversationId) {
        // Nếu vẫn còn conversation khác, chuyển sang conversation đầu tiên
        if (remainingConversations.length > 0) {
          handleConversationSelect(remainingConversations[0].id);
        } else {
          // Nếu không còn conversation nào, tạo conversation mới
          handleNewConversation();
        }
      }
    },
    [currentConversationId, handleNewConversation, handleConversationSelect]
  );

  // Delete all conversations
  const handleDeleteAllConversations = useCallback(() => {
    deleteAllConversations();
    localStorage.removeItem("test-chat-last-opened-id");
    // After deleting all, create a new default conversation state.
    // This will also set it as the current one.
    handleNewConversation();
  }, [handleNewConversation]);

  // Toggle sidebar
  const toggleSidebar = useCallback(() => {
    setSidebarOpen((prev) => !prev);
  }, []);

  // Handle updating conversation title
  const handleUpdateConversationTitle = useCallback(
    (id: string, newTitle: string) => {
      updateConversationTitleInStorage(id, newTitle);
      setConversations((prevConversations) =>
        prevConversations.map((conv) =>
          conv.id === id ? { ...conv, title: newTitle } : conv
        )
      );
    },
    []
  );

  // Handle sample question click
  const handleSampleQuestionClick = useCallback(
    (question: string) => {
      handleSendMessage(question);
    },
    [handleSendMessage]
  );

  // Determine current conversation title for the header
  const currentConvoDetails = conversations.find(
    (c) => c.id === currentConversationId
  );
  const chatHeaderTitle = currentConvoDetails?.title || "Bot Test";

  return (
    <div className="h-[calc(100vh-4rem)] relative flex flex-col">
      {" "}
      {/* Sidebar for conversations */}
      <ConversationSidebar
        conversations={conversations}
        currentConversationId={currentConversationId}
        onConversationSelect={handleConversationSelect}
        onNewConversation={handleNewConversation}
        onDeleteAllConversations={handleDeleteAllConversations}
        onDeleteConversation={handleDeleteConversation}
        onUpdateTitle={handleUpdateConversationTitle}
        sidebarOpen={sidebarOpen}
        toggleSidebar={toggleSidebar}
        isMobile={isMobile}
      />{" "}
      {/* Main chat area */}
      <div
        className={`flex-1 flex flex-col transition-all duration-300 ${
          !isMobile && sidebarOpen ? "ml-72" : "ml-0"
        }`}
      >
        {" "}
        {/* Chat header - made sticky */}
        <div className="sticky top-0 z-10 bg-white border-b">
          <ChatHeader
            title={chatHeaderTitle} // Use dynamic title
            toggleMobileSidebar={toggleSidebar}
            isMobile={isMobile}
          />
        </div>{" "}
        {/* Messages container - only this scrolls */}
        <div
          ref={chatBoxRef}
          className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50"
        >
          <div className="flex-1 flex flex-col">
            {messages.length === 0 ? (
              <EmptyChatState
                onSampleQuestionClick={handleSampleQuestionClick}
              />
            ) : (
              <>
                {messages.map((message, index) => (
                  <ChatMessage
                    key={message.id}
                    message={message}
                    index={index}
                  />
                ))}
                {processingConversationId === currentConversationId && (
                  <TypingIndicator />
                )}
              </>
            )}
          </div>
        </div>
        {/* Chat input - made sticky */}
        <div className="sticky bottom-0 z-10 bg-white border-t">
          <ChatInput
            disabled={
              processingConversationId === currentConversationId &&
              currentConversationId !== null
            }
            sendMessage={handleSendMessage}
            placeholder="Type your message here..."
          />
        </div>
      </div>
    </div>
  );
}
