"use client";

import { useState, Suspense, useEffect } from "react";
import { Conversation } from "@/types";
import ConversationInfoList from "./components/ConversationInfoList";
import ChatArea from "./components/chat-area/ChatArea";
import SentimentConversations from "./components/SentimentConversations";
import { LoadingScreen } from "@/components/loading-screen";
import { guestService } from "@/services/api/guest.service";

export default function ChatInterface() {
  const [selectedConversation, setSelectedConversation] =
    useState<Conversation | null>(null);

  // State to track conversations with unread messages
  const [unreadConversations, setUnreadConversations] = useState<Set<string>>(
    new Set()
  );

  // Check sessionStorage for selected conversation ID when component mounts
  useEffect(() => {
    const selectedId = sessionStorage.getItem("selectedConversationId");

    if (selectedId) {
      // Fetch the conversation data by ID
      guestService
        .getGuestInfo(selectedId)
        .then((conversation) => {
          if (conversation) {
            setSelectedConversation(conversation);
          }
          // Clear the sessionStorage after using it
          sessionStorage.removeItem("selectedConversationId");
        })
        .catch((error) => {
          console.error("Error fetching conversation:", error);
          sessionStorage.removeItem("selectedConversationId");
        });
    }
  }, []);

  // Handle conversation selection
  const handleSelectConversation = (conversation: Conversation) => {
    setSelectedConversation(conversation);

    // Mark the conversation as read when selected
    setUnreadConversations((prev) => {
      const newSet = new Set(prev);
      newSet.delete(conversation.id);
      return newSet;
    });
  };

  // Handle new messages from WebSocket
  const handleNewMessage = (conversation: Conversation) => {
    // If it's not the currently selected conversation, mark it as unread
    if (selectedConversation?.id !== conversation.id) {
      setUnreadConversations((prev) => {
        const newSet = new Set(prev);
        newSet.add(conversation.id);
        return newSet;
      });
    }
  };

  // Handle when a conversation is read (viewed in ChatArea)
  const handleConversationRead = (conversationId: string) => {
    // Mark the conversation as read
    setUnreadConversations((prev) => {
      const newSet = new Set(prev);
      newSet.delete(conversationId);
      return newSet;
    });
  };

  // Handle when guest information is updated
  const handleConversationUpdated = (updatedConversation: Conversation) => {
    // Update the selected conversation with the updated data
    setSelectedConversation(updatedConversation);
  };

  return (
    <Suspense fallback={<LoadingScreen />}>
      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar - Conversation List */}
        <ConversationInfoList
          selectedConversation={selectedConversation}
          setSelectedConversation={setSelectedConversation}
          handleSelectConversation={handleSelectConversation}
          onNewMessage={handleNewMessage}
          unreadConversations={unreadConversations}
        />

        {/* Middle - Chat Area */}
        <ChatArea
          selectedConversationId={selectedConversation?.id || null}
          onConversationRead={handleConversationRead}
          onConversationUpdated={handleConversationUpdated}
        />

        {/* Right Sidebar - Support Panel */}
        <SentimentConversations
          selectedConversation={selectedConversation}
          setSelectedConversation={setSelectedConversation}
        />
      </div>
    </Suspense>
  );
}
