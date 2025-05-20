"use client";

import { useState, Suspense, useEffect, useRef } from "react";
import { Conversation } from "@/types";
import ConversationInfoList from "../components/ConversationInfoList";
import ChatArea from "../components/chat-area/ChatArea";
import SupportPanel from "../components/SupportPanel";
import { LoadingScreen } from "@/components/loading-screen";
import { guestService } from "@/services/api/guest.service";
import { useParams } from "next/navigation";
import { useApp } from "@/context/app-context"; // Import useApp

export default function ConversationDetail() {
  // Sử dụng useParams() để lấy params từ URL
  const params = useParams();
  const conversationId = params.id as string;
  const { setActiveNavTab } = useApp(); // Get setActiveNavTab from context

  const [selectedConversation, setSelectedConversation] =
    useState<Conversation | null>(null);
  const [unreadConversations, setUnreadConversations] = useState<Set<string>>(
    new Set()
  );
  const [isLoading, setIsLoading] = useState(true);
  const [showSupportPanel, setShowSupportPanel] = useState(true); // Added state for SupportPanel visibility

  // Ref để kiểm soát việc gọi API một lần
  const hasInitialFetchRef = useRef<boolean>(false);

  // Set active nav tab and fetch conversation
  useEffect(() => {
    setActiveNavTab("messages"); // Set "messages" tab as active
    if (conversationId && !hasInitialFetchRef.current) {
      hasInitialFetchRef.current = true;
      fetchSelectedConversation(conversationId);
    }
  }, [conversationId, setActiveNavTab]);

  // Hàm fetch conversation cụ thể để tránh code trùng lặp
  const fetchSelectedConversation = (id: string) => {
    setIsLoading(true);
    guestService
      .getGuestInfo(id)
      .then((conversation) => {
        if (conversation) {
          setSelectedConversation(conversation);
          // Mark as read when loading from URL
          setUnreadConversations((prev) => {
            const newSet = new Set(prev);
            newSet.delete(id);
            return newSet;
          });
        } else {
        }
      })
      .catch(() => {})
      .finally(() => {
        setIsLoading(false);
      });
  };

  // Handle conversation selection
  const handleSelectConversation = (conversation: Conversation) => {
    // Update selected conversation in state immediately
    setSelectedConversation(conversation);

    // Update URL without full page reload
    window.history.pushState({}, "", `/conversations/${conversation.id}`);

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

  const toggleSupportPanel = () => {
    setShowSupportPanel((prev) => !prev);
  };

  if (isLoading) {
    return <LoadingScreen />;
  }

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
        />{" "}
        {/* Middle - Chat Area */}
        <ChatArea
          selectedConversationId={selectedConversation?.id || null}
          onConversationRead={handleConversationRead}
          onConversationUpdated={handleConversationUpdated}
          toggleSupportPanel={toggleSupportPanel} // Pass toggle function
        />{" "}
        {/* Right Sidebar - Support Panel */}
        <div
          className={`transition-all duration-300 ease-in-out ${
            showSupportPanel ? "w-80" : "w-0"
          } overflow-hidden`}
        >
          {showSupportPanel && (
            <SupportPanel
              conversationId={selectedConversation?.id || null}
              onGuestInfoUpdated={handleConversationUpdated} // Added this line
            />
          )}
        </div>
      </div>
    </Suspense>
  );
}
