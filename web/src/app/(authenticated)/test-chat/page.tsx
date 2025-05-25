"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useApp } from "@/context/app-context";
import { useMediaQuery } from "@/hooks/use-media-query";
import { WS_MESSAGES } from "@/lib/constants";
// Import our components
import {
  ChatMessage,
  TypingIndicator,
  EmptyChatState,
} from "./components/ChatMessage";
import {
  ConversationSidebar,
  saveConversation,
  loadConversations,
  deleteAllConversations,
  deleteConversation,
  updateConversationTitle as updateConversationTitleInStorage,
} from "./components/ConversationSidebar";
import { ChatHeader } from "./components/ChatHeader";
import { ChatInput } from "./components/ChatInput";
// Use a type alias to distinguish local Conversation from global Conversation
import {
  Chat,
  ChatAttachment,
} from "@/types/conversation"; // Added ChatAttachment
import { Conversation as LocalConversation } from "./components/ConversationSidebar";

export default function TestChatPage() {
  // State
  const [messages, setMessages] = useState<Chat[]>([]); // Use global Chat type
  const [processingConversationId, setProcessingConversationId] = useState<
    string | null
  >(null);
  const [conversations, setConversations] = useState<LocalConversation[]>([]); // Use LocalConversation for sidebar
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
        resolve: (data: Chat) => void; // Changed from ChatResponse to Chat
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
    setPageLoading,
  } = useApp();

  // Set active tab when component mounts and handle loading state
  useEffect(() => {
    setActiveNavTab("test-chat");
    // Turn off loading after a short delay to ensure UI is ready
    const timer = setTimeout(() => {
      setPageLoading(false);
    }, 500);

    return () => clearTimeout(timer);
  }, [setActiveNavTab, setPageLoading]);

  // Create a new conversation
  const handleNewConversation = useCallback(
    (title: string = "New Conversation") => {
      const newId = crypto.randomUUID();
      setCurrentConversationId(newId);
      localStorage.setItem("test-chat-last-opened-id", newId);
      setMessages([]); // messages are global Chat objects

      const newConversationEntry: LocalConversation = {
        // For sidebar storage
        id: newId,
        title: title,
        date: new Date().toISOString(),
        messages: [], // Will store global Chat objects
      };
      saveConversation(newConversationEntry);
      setConversations(loadConversations()); // Reload to get the new list
    },
    // saveConversation & loadConversations are stable imports, setConversations, setCurrentConversationId, setMessages are stable state setters
     
    []
  );

  // Initialize conversations and set active conversation
  useEffect(() => {
    const loadedConvos: LocalConversation[] = loadConversations();

    if (loadedConvos.length === 0) {
      // No conversations exist, create a new one.
      const newInitialConversationId = crypto.randomUUID();
      const newInitialConversation: LocalConversation = {
        // For sidebar storage
        id: newInitialConversationId,
        title: "New Conversation", // Default title
        date: new Date().toISOString(),
        messages: [], // Will store global Chat objects
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
      let activeMessagesToSet: Chat[] = []; // Use global Chat type

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
      senderSide: "client" | "staff",
      text: string,
      attachments?: ChatAttachment[] // Added optional attachments parameter
    ) => {
      const newMessage: Chat = {
        id: crypto.randomUUID(),
        guest_id: conversationId,
        content: {
          side: senderSide,
          message: {
            text: text,
            attachments: attachments || [], // Use provided attachments or default to empty array
          },
        },
        created_at: new Date().toISOString(),
      };

      // Load the latest conversations from storage to avoid stale state
      const currentStoredConversations: LocalConversation[] =
        loadConversations();
      const existingConversation = currentStoredConversations.find(
        (c) => c.id === conversationId
      );

      const prevMessages: Chat[] = existingConversation?.messages || [];
      const updatedMessages = [...prevMessages, newMessage];

      let conversationTitle = existingConversation?.title || "New Conversation";
      if (
        senderSide === "client" && // Use senderSide
        prevMessages.filter((m) => m.content.side === "client").length === 0 && // Check content.side
        (!existingConversation ||
          !existingConversation.title ||
          existingConversation.title === "New Conversation")
      ) {
        conversationTitle = text.substring(0, 30) || "New Conversation";
      }

      const conversationToSave: LocalConversation = {
        // For sidebar storage
        id: conversationId,
        title: conversationTitle,
        date: existingConversation?.date || new Date().toISOString(),
        messages: updatedMessages, // Store global Chat objects
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
    ): Promise<Chat> => {
      // Changed from ChatResponse to Chat
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
              "staff", // 'staff' for Assistant messages
              "Xin lỗi, đã xảy ra lỗi timeout khi xử lý yêu cầu của bạn. Vui lòng thử lại sau."
              // "ai" // type removed
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
        let chatData = data as Chat;
        try {
          // Phương pháp mới: xử lý tất cả các định dạng dữ liệu có thể có
          console.log("Raw data type:", typeof data);

          if (
            data &&
            typeof data === "object" &&
            data.id &&
            data.guest_id &&
            data.content &&
            data.content.message // Ensure message object exists
          ) {
            chatData = data;
          } else {
            console.error("Received data is not a valid Chat object:", data);
            return;
          }

          // Dừng hiệu ứng đang xử lý với ID tương ứng (guest_id is the conversationId)
          if (processingConversationId === chatData.guest_id) {
            setProcessingConversationId(null);
          }
          const entry = responseMapRef.current[chatData.guest_id];
          if (entry) {
            console.log(
              "Found pending request, clearing timeout for conversation:",
              chatData.guest_id
            );
            clearTimeout(entry.timeoutId);
            entry.resolve(chatData);
            delete responseMapRef.current[chatData.guest_id];
          } else if (chatData.guest_id === currentConversationId) {
            addMessage(
              chatData.guest_id,
              "staff",
              chatData.content.message.text,
              chatData.content.message.attachments // Pass attachments
            );
          }
        } catch {
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
          "staff", // 'staff' for Assistant messages
          "Xin lỗi, kết nối đến máy chủ đã bị mất. Vui lòng làm mới trang và thử lại."
          // "ai" // type removed
        );
        return;
      }

      const convoIdToSendMessageTo = currentConversationId;

      // User sends a message (typically text only from input)
      addMessage(convoIdToSendMessageTo, "client", messageText);

      try {
        setProcessingConversationId(convoIdToSendMessageTo);
        const chatRes: Chat = await getChatResponse(
          convoIdToSendMessageTo,
          messageText
        );
        // Add assistant's response, which might include text and attachments
        addMessage(
          chatRes.guest_id,
          "staff",
          chatRes.content.message.text,
          chatRes.content.message.attachments // Pass attachments
        );
      } catch {
        addMessage(
          convoIdToSendMessageTo,
          "staff", // 'staff' for Assistant messages
          "Xin lỗi, tôi không thể xử lý yêu cầu của bạn lúc này. Vui lòng thử lại sau."
          // "ai" // type removed
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

      const allConvos: LocalConversation[] = loadConversations(); // Load fresh conversations
      const selectedConversation = allConvos.find((conv) => conv.id === id);
      setMessages(selectedConversation?.messages || []); // messages are global Chat objects
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
      />
      {/* Main chat area */}
      <div
        className={`flex-1 flex flex-col transition-all duration-300 ${
          !isMobile && sidebarOpen ? "ml-72" : "ml-0"
        }`}
      >
        {/* Chat header - made sticky */}
        <div className="sticky top-0 z-10 bg-white border-b">
          <ChatHeader
            title={chatHeaderTitle} // Use dynamic title
            toggleMobileSidebar={toggleSidebar}
            isMobile={isMobile}
          />
        </div>
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
