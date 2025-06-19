"use client";

import {
  useState,
  useEffect,
  useRef,
  useCallback,
  useLayoutEffect,
} from "react";
import { useApp } from "@/context/app-context";
import { useMediaQuery } from "@/hooks/use-media-query";
import { WS_MESSAGES } from "@/lib/constants";
import { conversationService } from "@/services/api/conversation.service";
import { guestService } from "@/services/api/guest.service";
import { Conversation } from "@/types";
import {
  TooltipProvider,
} from "@/components/ui/tooltip";
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
import { Chat } from "@/types/conversation"; // Added ChatAttachment
import { Conversation as LocalConversation } from "./components/ConversationSidebar";

interface ConversationWithTitle extends LocalConversation {
  title: string;
}

const MESSAGE_LIMIT = 20;

export default function TestChatPage() {
  // State
  const [messages, setMessages] = useState<Chat[]>([]); // Use global Chat type
  const [isLoadingMessages, setIsLoadingMessages] = useState<boolean>(false);
  const [hasMoreMessages, setHasMoreMessages] = useState<boolean>(false);
  const [isConversationSwitching, setIsConversationSwitching] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [conversations, setConversations] = useState<ConversationWithTitle[]>(
    []
  ); // Use LocalConversation for sidebar
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [currentConversationId, setCurrentConversationId] =
    useState<string>(""); // ID of the currently active conversation
  const [wasDisconnected, setWasDisconnected] = useState(false); // Track if was previously disconnected
  const [connectionCheckAttempts, setConnectionCheckAttempts] = useState(0); // Track connection attempts
  const [initialLoadDone, setInitialLoadDone] = useState(false); // Track if initial load is done

  // Check if mobile view
  const isMobile = !useMediaQuery("(min-width: 640px)");

  // Refs
  const chatBoxRef = useRef<HTMLDivElement>(null);
  const chatListRef = useRef(messages);
  useEffect(() => {
    chatListRef.current = messages;
  }, [messages]);
  const isLoadingMore = useRef<boolean>(false);
  const prevScrollHeight = useRef<number>(0);
  const prevScrollTop = useRef<number>(0);
  const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // WebSocket from AppContext
  const {
    sendWebSocketMessage,
    registerMessageHandler,
    isWebSocketConnected,
    setActiveNavTab,
    setPageLoading,
  } = useApp(); // Set active tab when component mounts and handle loading state
  useEffect(() => {
    setActiveNavTab("test-chat");
    // Turn off loading after a short delay to ensure UI is ready
    const timer = setTimeout(() => {
      setPageLoading(false);
    }, 500);

    // Check initial WebSocket connection status
    if (!isWebSocketConnected) {
      setWasDisconnected(true);
    }

    return () => clearTimeout(timer);
  }, [setActiveNavTab, setPageLoading, isWebSocketConnected]);

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

  const fetchConversationMessages = useCallback(
    async (conversationId: string, loadMore: boolean = false) => {
      if (!conversationId) return;
      setIsLoadingMessages(true);
      try {
        const currentMessages = chatListRef.current;
        const skip = loadMore ? currentMessages.length : 0;

        const response = await conversationService.getChatById(
          conversationId,
          skip,
          MESSAGE_LIMIT
        );

        if (response && response.data) {
          const newMessages = response.data;
          // The API returns messages sorted from newest to oldest.
          // We need to reverse them to display in chronological order.
          const reversedNewMessages = newMessages.reverse();
          setMessages((prev) =>
            loadMore ? [...reversedNewMessages, ...prev] : reversedNewMessages
          );
          setHasMoreMessages(response.has_next);
        } else {
          if (!loadMore) setMessages([]);
          setHasMoreMessages(false);
        }
      } catch (error) {
        console.error("Failed to fetch messages:", error);
        if (!loadMore) setMessages([]);
        setHasMoreMessages(false);
        // Re-throw to be handled by the caller for specific actions like 404
        throw error;
      } finally {
        setIsLoadingMessages(false);
      }
    },
    [] // Dependencies are stable setters
  );

  // Create a new conversation
  const handleNewConversation = useCallback(
    (title: string = "New Conversation") => {
      const newId = crypto.randomUUID();
      setCurrentConversationId(newId);
      localStorage.setItem("test-chat-last-opened-id", newId);
      setMessages([]); // messages are global Chat objects
      setHasMoreMessages(false);

      const newConversationEntry: LocalConversation = {
        // For sidebar storage
        id: newId,
        date: new Date().toISOString(),
      };
      saveConversation(newConversationEntry);
      setConversations((prev) => [...prev, { ...newConversationEntry, title }]); // Reload to get the new list
    },
    // saveConversation & loadConversations are stable imports, setConversations, setCurrentConversationId, setMessages are stable state setters

    []
  );

  // Initialize conversations and set active conversation
  useEffect(() => {
    const loadedConvos: LocalConversation[] = loadConversations();

    const initialize = async () => {
      setIsConversationSwitching(true);
      setInitialLoadDone(false);
      if (loadedConvos.length === 0) {
        handleNewConversation();
        setIsConversationSwitching(false);
        setInitialLoadDone(true);
        return;
      }

      const convosWithTitles: ConversationWithTitle[] = loadedConvos.map(
        (c) => ({ ...c, title: "Loading..." })
      );
      setConversations(convosWithTitles);

      let idToLoad =
        localStorage.getItem("test-chat-last-opened-id") || loadedConvos[0].id;

      // Verify the idToLoad is actually in our list
      if (!loadedConvos.find((c) => c.id === idToLoad)) {
        idToLoad = loadedConvos[0].id;
      }

      try {
        setCurrentConversationId(idToLoad);
        localStorage.setItem("test-chat-last-opened-id", idToLoad);
        await fetchConversationMessages(idToLoad);
        setInitialLoadDone(true);
        const details = await guestService.getGuestInfo(idToLoad);
        if (details && details.account_name) {
          handleUpdateConversationTitle(idToLoad, details.account_name);
        }
      } catch (error: any) {
        if (error.response && error.response.status === 404) {
          const allConvos = loadConversations();
          if (allConvos.length <= 1) {
            // This is the only conversation, and it's not on the server.
            // Treat it as a new conversation. The UI is already clear.
            setMessages([]);
            setHasMoreMessages(false);
            // Update title to "New Conversation" since it's treated as new
            handleUpdateConversationTitle(idToLoad, "New Conversation");
          } else {
            // Multiple conversations exist, this one is invalid.
            deleteConversation(idToLoad);
            const remaining = allConvos.filter((c) => c.id !== idToLoad);
            setConversations(convosWithTitles.filter((c) => c.id !== idToLoad));
            if (remaining.length > 0) {
              handleConversationSelect(remaining[0].id);
            } else {
              handleNewConversation();
            }
          }
        } else {
          console.error("Failed to load initial conversation:", error);
        }
      } finally {
        setIsConversationSwitching(false);
      }
    };

    initialize(); // Fetch titles for all other conversations in the background
    loadedConvos.forEach((convo) => {
      guestService
        .getGuestInfo(convo.id)
        .then((details) => {
          if (details && details.account_name) {
            handleUpdateConversationTitle(convo.id, details.account_name);
          }
        })
        .catch((err: any) => {
          if (err.response && err.response.status === 404) {
            const allConvos = loadConversations();
            if (allConvos.length > 1) {
              // Only delete if there are multiple conversations
              deleteConversation(convo.id);
              setConversations((prev) => prev.filter((c) => c.id !== convo.id));
            } else {
              // Don't delete if it's the only conversation, just log and update title
              handleUpdateConversationTitle(convo.id, "New Conversation");
            }
          }
        });
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // This effect should only run once on mount.

  // Refactor addMessage to accept conversationId explicitly and use fresh conversations list
  const addMessage = useCallback(
    (conversationId: string, message: Chat, addToEnd: boolean) => {
      // 1. Update UI state
      if (conversationId === currentConversationId) {
        setMessages((prev) => {
          // Check if message already exists
          const existingMessage = prev.find((m) => m.id === message.id);
          if (existingMessage) {
            return prev;
          }

          return addToEnd ? [...prev, message] : [message, ...prev];
        });
      } else {
        // Message is for different conversation, skip
      }

      // 2. Update localStorage conversation metadata
      const allConvos = loadConversations();
      const convoIndex = allConvos.findIndex((c) => c.id === conversationId);
      if (convoIndex > -1) {
        const existingConvo = allConvos[convoIndex];

        const updatedConvo = {
          ...existingConvo,
          date: new Date().toISOString(),
        };
        // This assumes saveConversation can update an existing one.
        saveConversation(updatedConvo);
        // Refresh sidebar state by updating the date of the relevant conversation
        setConversations((prev) =>
          prev.map((c) =>
            c.id === conversationId ? { ...c, date: updatedConvo.date } : c
          )
        );
      }
    },
    [currentConversationId]
  );

  // Monitor WebSocket connection status changes
  useEffect(() => {
    if (!isWebSocketConnected && !wasDisconnected) {
      // Connection lost
      setWasDisconnected(true);
      setConnectionCheckAttempts(0);
    } else if (isWebSocketConnected && wasDisconnected) {
      // Connection restored
      setWasDisconnected(false);
      setConnectionCheckAttempts(0);
      // No automatic staff message - UI will show connection status
    }
  }, [isWebSocketConnected, wasDisconnected]);
  // Auto-retry connection check after extended disconnection
  useEffect(() => {
    if (!isWebSocketConnected && wasDisconnected) {
      const timer = setTimeout(() => {
        setConnectionCheckAttempts((prev) => prev + 1);
        // Connection status is shown in UI - no automatic staff message needed
      }, 10000); // Check every 10 seconds

      return () => clearTimeout(timer);
    }
  }, [isWebSocketConnected, wasDisconnected, connectionCheckAttempts]);

  // Register WebSocket message handler (must be after addMessage is defined)
  useEffect(() => {
    const unregister = registerMessageHandler(
      WS_MESSAGES.TEST_CHAT,
      (data: any) => {
        try {
          // The server sends the full Conversation object.
          const conversation = data as Conversation;
          if (
            !conversation ||
            !conversation.id ||
            !conversation.last_chat_message
          ) {
            console.warn("Invalid conversation data received from WS:", data);
            return;
          }

          const chatData = conversation.last_chat_message;

          // Stop typing indicator when a real message arrives
          if (typingTimeoutRef.current) {
            clearTimeout(typingTimeoutRef.current);
            typingTimeoutRef.current = null;
          }
          setIsTyping(false);

          // If the conversation has a name, update the title in the sidebar
          if (conversation.account_name) {
            handleUpdateConversationTitle(
              conversation.id,
              conversation.account_name
            );
          }

          // Add the incoming message to the conversation
          addMessage(chatData.guest_id, chatData, true);
        } catch (e) {
          console.error("Error processing WebSocket message:", e);
        }
      }
    );
    return unregister;
  }, [registerMessageHandler, addMessage, handleUpdateConversationTitle]);

  // Handler for typing actions based on server's keep-alive signal
  useEffect(() => {
    const unregister = registerMessageHandler(
      "SEND_ACTION",
      (data: { guest_id: string; action: "typing_on" | "typing_off" }) => {
        if (data.guest_id !== currentConversationId) {
          return;
        }

        // Always clear the previous timeout when a new action is received
        if (typingTimeoutRef.current) {
          clearTimeout(typingTimeoutRef.current);
          typingTimeoutRef.current = null;
        }
        if (data.action === "typing_on") {
          setIsTyping(true);
          // The server sends this action every 8s. We'll set a 9s timeout.
          // If another typing_on arrives, the timeout will be reset.
          typingTimeoutRef.current = setTimeout(() => {
            setIsTyping(false);
            typingTimeoutRef.current = null;
          }, 9000); // Timeout after 9 seconds
        } else if (data.action === "typing_off") {
          // Immediately stop typing if requested
          setIsTyping(false);
        }
      }
    );
    return unregister;
  }, [registerMessageHandler, currentConversationId]);

  // Khôi phục scroll sau khi load thêm tin nhắn (pagination)
  useEffect(() => {
    if (
      chatBoxRef.current &&
      prevScrollHeight.current > 0 &&
      isLoadingMore.current === false
    ) {
      const newScrollHeight = chatBoxRef.current.scrollHeight;
      const heightDifference = newScrollHeight - prevScrollHeight.current;
      chatBoxRef.current.scrollTop = prevScrollTop.current + heightDifference;
      prevScrollHeight.current = 0;
      prevScrollTop.current = 0;
    }
  }, [messages]); // Depends on messages changing

  // Scroll to bottom sau khi load lần đầu hoặc chuyển conversation
  useLayoutEffect(() => {
    if (
      initialLoadDone &&
      !isLoadingMessages &&
      !isConversationSwitching &&
      messages.length > 0 &&
      prevScrollHeight.current === 0 // Chỉ scroll xuống cuối khi KHÔNG phải load thêm
    ) {
      if (chatBoxRef.current) {
        chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight;
      }
    }
  }, [
    initialLoadDone,
    messages,
    currentConversationId,
    isLoadingMessages,
    isConversationSwitching,
  ]);

  // Handle sending a message
  const handleSendMessage = useCallback(
    async (messageText: string) => {
      if (!messageText.trim() || !currentConversationId) {
        return;
      } // Kiểm tra kết nối WebSocket trước khi gửi tin nhắn
      if (!isWebSocketConnected) {
        // Connection status is shown in UI - user will see the reconnecting status
        return;
      }

      const convoIdToSendMessageTo = currentConversationId;

      // User sends a message (typically text only from input)
      const userMessage: Chat = {
        id: crypto.randomUUID(),
        guest_id: convoIdToSendMessageTo,
        content: {
          side: "client",
          message: { text: messageText, attachments: [] },
        },
        created_at: new Date().toISOString(),
      };
      addMessage(convoIdToSendMessageTo, userMessage, true);

      sendWebSocketMessage({
        message: WS_MESSAGES.TEST_CHAT,
        data: { id: convoIdToSendMessageTo, message: messageText },
      });
    },
    [
      addMessage,
      currentConversationId,
      isWebSocketConnected,
      sendWebSocketMessage,
    ]
  );
  // Handle selecting a conversation
  const handleConversationSelect = useCallback(
    async (id: string) => {
      if (id === currentConversationId) return;

      setIsConversationSwitching(true);
      setCurrentConversationId(id);
      localStorage.setItem("test-chat-last-opened-id", id);
      setMessages([]); // Clear messages immediately
      setHasMoreMessages(false); // Reset pagination state

      try {
        await fetchConversationMessages(id);
        const conversationDetails = await guestService.getGuestInfo(id);
        if (conversationDetails && conversationDetails.account_name) {
          handleUpdateConversationTitle(id, conversationDetails.account_name);
        }
      } catch (error: any) {
        if (error.response && error.response.status === 404) {
          deleteConversation(id);
          const remainingConversations = conversations.filter(
            (c) => c.id !== id
          );
          setConversations(remainingConversations);

          if (remainingConversations.length > 0) {
            handleConversationSelect(remainingConversations[0].id);
          } else {
            handleNewConversation();
          }
        } else {
          console.error("Failed to select conversation:", error);
        }
      } finally {
        setIsConversationSwitching(false);
      }
    },
    [
      currentConversationId,
      conversations,
      fetchConversationMessages,
      handleUpdateConversationTitle,
      handleNewConversation,
    ]
  );

  // Delete specific conversation
  const handleDeleteConversation = useCallback(
    async (id: string) => {
      try {
        // Call API to delete guest
        await guestService.deleteGuest(id);

        // Delete conversation from localStorage
        deleteConversation(id);

        // Update conversation list state
        const remainingConversations = conversations.filter((c) => c.id !== id);
        setConversations(remainingConversations);

        // If the deleted conversation was the current one
        if (id === currentConversationId) {
          // If there are other conversations, switch to the first one
          if (remainingConversations.length > 0) {
            handleConversationSelect(remainingConversations[0].id);
          } else {
            // If no conversations are left, create a new one
            handleNewConversation();
          }
        }
      } catch (error) {
        console.error("Failed to delete conversation:", error);
        // Optionally, show an error message to the user
      }
    },
    [
      currentConversationId,
      handleNewConversation,
      handleConversationSelect,
      conversations,
    ]
  );

  // Delete all conversations
  const handleDeleteAllConversations = useCallback(async () => {
    try {
      const allConversations = loadConversations();
      if (allConversations.length > 0) {
        const guestIds = allConversations.map((c) => c.id);
        await guestService.deleteGuests(guestIds);
      }

      deleteAllConversations();
      localStorage.removeItem("test-chat-last-opened-id");

      // Create a new conversation and reset the state
      const newId = crypto.randomUUID();
      const title = "New Conversation";
      const newConversationEntry: LocalConversation = {
        id: newId,
        date: new Date().toISOString(),
      };

      saveConversation(newConversationEntry);
      setConversations([{ ...newConversationEntry, title }]);
      setCurrentConversationId(newId);
      localStorage.setItem("test-chat-last-opened-id", newId);
      setMessages([]);
      setHasMoreMessages(false);
    } catch (error) {
      console.error("Failed to delete all conversations:", error);
      // Optionally, show an error message to the user
    }
  }, []);

  // Toggle sidebar
  const toggleSidebar = useCallback(() => {
    setSidebarOpen((prev) => !prev);
  }, []);
  const handleScroll = async () => {
    if (
      chatBoxRef.current &&
      chatBoxRef.current.scrollTop === 0 &&
      !isLoadingMessages &&
      hasMoreMessages &&
      currentConversationId &&
      !isLoadingMore.current
    ) {
      isLoadingMore.current = true;
      // Lưu lại scrollHeight trước khi load thêm
      prevScrollHeight.current = chatBoxRef.current.scrollHeight;
      prevScrollTop.current = chatBoxRef.current.scrollTop;
      await fetchConversationMessages(currentConversationId, true);
      // Việc khôi phục scroll sẽ được thực hiện trong useEffect([messages]) phía dưới
      isLoadingMore.current = false;
    }
  };

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
        sidebarOpen={sidebarOpen}
        toggleSidebar={toggleSidebar}
        isMobile={isMobile}
      />{" "}
      {/* Main chat area */}
      <div
        className={`flex-1 flex flex-col h-full transition-all duration-300 ${
          !isMobile && sidebarOpen ? "ml-72" : "ml-0"
        }`}
      >
        {/* Chat header - fixed */}
        <div className="flex-shrink-0 bg-white border-b">
          <ChatHeader
            title={chatHeaderTitle} // Use dynamic title
            toggleMobileSidebar={toggleSidebar}
            isMobile={isMobile}
            isWebSocketConnected={isWebSocketConnected}
          />
        </div>
        {/* Messages container - only this scrolls */}
        <div
          ref={chatBoxRef}
          onScroll={handleScroll}
          className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50"
        >
          {isLoadingMessages && messages.length === 0 ? (
            <div className="flex justify-center items-center h-full">
              <p>Loading messages...</p>
            </div>
          ) : messages.length === 0 ? (
            <EmptyChatState onSampleQuestionClick={handleSampleQuestionClick} />
          ) : (
            <TooltipProvider>
              {messages.map((message, index) => (
                <ChatMessage key={message.id} message={message} index={index} />
              ))}
              {isTyping && <TypingIndicator />}
            </TooltipProvider>
          )}
        </div>
        {/* Chat input - fixed */}
        <div className="flex-shrink-0 bg-white border-t">
          <ChatInput
            disabled={isTyping || !isWebSocketConnected}
            sendMessage={handleSendMessage}
            placeholder="Type your message here..."
          />
        </div>
      </div>
    </div>
  );
}
