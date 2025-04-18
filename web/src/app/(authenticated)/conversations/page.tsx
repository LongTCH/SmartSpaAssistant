"use client";

import { useApp } from "@/context/app-context";
import { useState, useEffect } from "react";
import { Chat, Conversation } from "@/types";
import ConversationInfoList from "./components/ConversationInfoList";
import ChatArea from "./components/ChatArea";
import SentimentConversations from "./components/SentimentConversations";

export default function ChatInterface() {
  const { contentHeight, setActiveNavTab } = useApp();

  // Set active tab to messages when this page is loaded
  useEffect(() => {
    setActiveNavTab("messages");
  }, [setActiveNavTab]);

  const [selectedConversation, setSelectedConversation] =
    useState<Conversation | null>(null);

  // State to track conversations with unread messages
  const [unreadConversations, setUnreadConversations] = useState<Set<string>>(
    new Set()
  );

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

  return (
    <div className="flex flex-1 overflow-hidden">
      {/* Left Sidebar - Conversation List */}
      {/* Conversation Items */}
      <ConversationInfoList
        selectedConversation={selectedConversation}
        setSelectedConversation={setSelectedConversation}
        handleSelectConversation={handleSelectConversation}
        onNewMessage={handleNewMessage}
        unreadConversations={unreadConversations}
      />

      {/* Middle - Chat Area */}
      <ChatArea
        selectedConversation={selectedConversation}
        onConversationRead={handleConversationRead}
      />

      {/* Right Sidebar - Support Panel */}
      <SentimentConversations
        selectedConversation={selectedConversation}
        setSelectedConversation={setSelectedConversation}
      />
    </div>
  );
}
