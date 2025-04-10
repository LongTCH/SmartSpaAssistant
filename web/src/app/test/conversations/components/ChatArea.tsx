"use client";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { useApp } from "@/context/app-context";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Frown, Info } from "lucide-react";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Badge } from "@/components/ui/badge";
import { useState, useEffect, useRef } from "react";
import { conversationService } from "@/services/api/conversation.service";
import { Conversation, Chat } from "@/types";
import ConversationInfo from "./ConversationInfo";
import ConversationInfoList from "./ConversationInfoList";
import { getBadge } from "./ConversationInfo";
interface ChatAreaProps {
  selectedConversation: Conversation | null;
  setSelectedConversation: (conversation: Conversation) => void;
  chatList: Chat[];
  setChatList: (chatList: Chat[]) => void;
  isLoadingMessages: boolean;
  setIsLoadingMessages: (isLoading: boolean) => void;
  chatSkip: number;
  setChatSkip: (skip: number) => void;
  hasMoreMessages: boolean;
  messageLimit: number;
}
export default function ChatArea(props: ChatAreaProps) {
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
            <Popover>
              <PopoverTrigger asChild>
                <Button
                  variant="link"
                  size="icon"
                  className="w-5 h-5 rounded-full bg-red-500 flex items-center justify-center mr-4"
                >
                  <Frown className="h-6 w-6 text-white" />
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-80 p-4">
                <div className="space-y-2">
                  <h4 className="font-medium">Dự đoán cảm xúc</h4>
                  <p className="text-sm text-gray-500">
                    AI dự đoán cảm xúc của người dùng trong cuộc trò chuyện này
                    là <strong>tiêu cực</strong>.
                  </p>
                </div>
              </PopoverContent>
            </Popover>
          </div>

          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">Giao cho</span>
            <Select defaultValue="ai">
              <SelectTrigger className="w-[120px] h-8">
                <SelectValue placeholder="AI" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ai">AI</SelectItem>
                <SelectItem value="me">Tôi</SelectItem>
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

      {/* Chat Messages Area - Restructured for scrollable messages with fixed bottom note */}
      <div className="h-[10vh] flex-1 flex flex-col">
        {/* Chat Messages Area - Scrollable Messages */}
        <div
          ref={chatContainerRef}
          className="flex-1 overflow-y-auto p-4 space-y-4 flex flex-col-reverse"
          onScroll={(e) => {
            const target = e.target as HTMLDivElement;
            // Khi cuộn gần đến đầu (top) của danh sách
            if (
              target.scrollTop < 50 &&
              hasMoreMessages &&
              !isLoadingMessages
            ) {
              // Lưu lại chiều cao và vị trí cuộn hiện tại
              prevScrollHeight.current = target.scrollHeight;
              prevScrollTop.current = target.scrollTop;

              // Tăng skip để tải tin nhắn cũ hơn
              const newSkip = chatSkip + messageLimit;
              setChatSkip(newSkip);

              // API sẽ tự động được gọi thông qua useEffect theo dõi chatSkip
            }
          }}
        >
          {/* Hiển thị indicator đang tải thêm tin nhắn ở phía trên */}
          {isLoadingMessages && chatList.length > 0 && (
            <div className="text-center text-gray-500 py-2">
              <span className="inline-block animate-spin mr-2">⟳</span>
              Đang tải thêm tin nhắn...
            </div>
          )}

          {/* Hiển thị danh sách tin nhắn - sử dụng flex-col-reverse để tin nhắn mới nhất ở dưới */}
          {isLoadingMessages && chatList.length === 0 ? (
            <div className="flex justify-center items-center h-full">
              <div className="text-center text-gray-500">
                <span className="inline-block animate-spin mr-2">⟳</span>
                Đang tải tin nhắn...
              </div>
            </div>
          ) : chatList.length > 0 ? (
            <>
              {chatList.map((chat, index) =>
                chat.content.side === "client" ? (
                  // Sender Message
                  <div
                    key={index}
                    className="flex items-start space-x-2 max-w-[80%]"
                  >
                    <Avatar>
                      <AvatarImage src={selectedConversation?.avatar} />
                      <AvatarFallback>?</AvatarFallback>
                    </Avatar>
                    <div>
                      <div className="bg-white p-3 rounded-lg shadow-sm">
                        <p className="text-sm">{chat.content.message.text}</p>
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {new Date(chat.created_at).toLocaleTimeString()}
                      </div>
                    </div>
                  </div>
                ) : (
                  // Receiver Message
                  <div
                    key={index}
                    className="flex items-start justify-end space-x-2 max-w-[80%] ml-auto"
                  >
                    <div>
                      <div className="bg-indigo-500 p-3 rounded-lg shadow-sm">
                        <p className="text-sm text-white">
                          {chat.content.message.text}
                        </p>
                      </div>
                      <div className="text-xs text-gray-500 mt-1 text-right">
                        {new Date(chat.created_at).toLocaleTimeString()}
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
                {selectedConversation
                  ? "Không có tin nhắn nào"
                  : "Vui lòng chọn một cuộc trò chuyện"}
              </div>
            </div>
          )}
        </div>

        {/* Fixed System Message at Bottom */}
        {/* Fixed System Message at Bottom - Will stick to bottom even when chat scrolls */}
        <div className="p-2 border-t bg-white sticky bottom-0 z-10">
          <div className="text-xs text-gray-500 text-center bg-gray-50 py-2 rounded border border-gray-200">
            Xin lỗi, việc nhận tin trực tiếp không được hỗ trợ. Vui lòng dùng
            Messenger.
          </div>
        </div>
      </div>
    </div>
  );
}
