"use client";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { useApp } from "@/context/app-context";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useState, useEffect, useRef } from "react";
import { Chat, Conversation } from "@/types";
import ConversationInfoList from "./components/ConversationInfoList";
import ChatArea from "./components/ChatArea";

export default function ChatInterface() {
  const { contentHeight } = useApp();

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
    <div className="flex flex-col" style={{ height: contentHeight }}>
      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar - Conversation List */}
        <div className="w-80 border-r flex flex-col bg-white">
          <div className="p-4 border-b">
            <div className="flex items-center justify-between">
              <h3 className="text-sm text-gray-500 mr-2">Phụ trách bởi</h3>
              <Select defaultValue="all">
                <SelectTrigger className="h-9">
                  <SelectValue placeholder="Tất cả" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tất cả</SelectItem>
                  <SelectItem value="ai">AI</SelectItem>
                  <SelectItem value="me">Tôi</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Conversation Items */}
          <ConversationInfoList
            selectedConversation={selectedConversation}
            setSelectedConversation={setSelectedConversation}
            handleSelectConversation={handleSelectConversation}
            onNewMessage={handleNewMessage}
            unreadConversations={unreadConversations}
          />
        </div>

        {/* Middle - Chat Area */}
        <ChatArea
          selectedConversation={selectedConversation}
          onConversationRead={handleConversationRead}
        />

        {/* Right Sidebar - Support Panel */}
        <div className="w-72 border-l flex flex-col bg-white">
          <div className="flex flex-col h-full">
            {/* Negative Section */}
            <div className="h-1/2 flex flex-col">
              <div className="p-1 bg-red-500 text-white text-center font-medium">
                Tiêu cực
              </div>
              <div className="p-2 space-y-2 overflow-auto h-[calc(100%-40px)]">
                {[1, 2, 3, 4, 5, 6, 7].map((item) => (
                  <div
                    key={`neg-${item}`}
                    className="border rounded-md p-2 hover:bg-indigo-50 flex items-center space-x-2 cursor-pointer"
                  >
                    <Avatar className="h-8 w-8">
                      <AvatarImage src="/placeholder.svg?height=32&width=32" />
                      <AvatarFallback>SA</AvatarFallback>
                    </Avatar>
                    <span className="text-sm font-medium">Suporte ADMIN</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Positive Section */}
            <div className="h-1/2 flex flex-col">
              <div className="p-1 bg-green-500 text-white text-center font-medium">
                Tích cực
              </div>
              <div className="p-2 space-y-2 overflow-auto h-[calc(100%-40px)]">
                {[1, 2, 3, 4, 5, 6, 7].map((item) => (
                  <div
                    key={`pos-${item}`}
                    className="border rounded-md p-2 flex hover:bg-indigo-50 items-center space-x-2 cursor-pointer"
                  >
                    <Avatar className="h-8 w-8">
                      <AvatarImage src="/placeholder.svg?height=32&width=32" />
                      <AvatarFallback>SA</AvatarFallback>
                    </Avatar>
                    <span className="text-sm font-medium">Suporte ADMIN</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
