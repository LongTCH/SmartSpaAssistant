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
import { conversationService } from "@/services/api/conversation.service";
import { Conversation, Chat } from "@/types";
import ConversationInfoList from "./components/ConversationInfoList";

export default function ChatInterface() {
  const { contentHeight } = useApp();
  const [skip, setSkip] = useState<number>(0);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [hasNext, setHasNext] = useState<boolean>(false);
  const [selectedConversation, setSelectedConversation] =
    useState<Conversation | null>(null);
  const [isLoadingMessages, setIsLoadingMessages] = useState<boolean>(false);
  const [chatSkip, setChatSkip] = useState<number>(0);
  const [chatList, setChatList] = useState<Chat[]>([]);
  const conversationLimit = 10; // Giới hạn số lượng cuộc trò chuyện mỗi lần tải
  const messageLimit = 5; // Giới hạn số lượng tin nhắn mỗi lần tải

  // Thêm state để theo dõi trạng thái tải
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const fetchConversations = async () => {
    try {
      setIsLoading(true);
      const response = await conversationService.getPagingConversation(
        skip,
        conversationLimit
      );

      if (response.data.length !== 0) {
        if (skip === 0) {
          // Trang đầu tiên, thay thế dữ liệu
          setConversations(response.data);

          // Tự động chọn conversation đầu tiên khi khởi tạo trang
          if (!selectedConversation) {
            setSelectedConversation(response.data[0]);
          }
        } else {
          // Trang tiếp theo, nối thêm dữ liệu
          setConversations((prevConversations) => [
            ...prevConversations,
            ...response.data,
          ]);
        }
        setHasNext(response.has_next);
      }
    } catch (error) {
      console.error("Error fetching conversations:", error);
    } finally {
      setIsLoading(false);
    }
  };

  // Sửa lại phần tải thêm tin nhắn trong fetchConversationMessages
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

      // Nếu đang tải thêm, thêm tin nhắn mới vào đầu danh sách
      if (loadMore && response.data.length > 0) {
        // Bảo toàn chiều cao cuộn bằng cách lưu chiều cao trước khi cập nhật state
        setChatList((prevMessages) => [...response.data, ...prevMessages]);

        // Bạn cần thêm logic để giữ vị trí cuộn sau khi thêm tin nhắn mới
        // Điều này cần được xử lý với useRef và useEffect
      } else {
        // Nếu tải mới, thay thế danh sách cũ
        setChatList(response.data);
      }

      // Cập nhật hasMoreMessages nếu API trả về thông tin này
      setHasMoreMessages(response.has_next || false);
    } catch (error) {
      console.error("Error fetching conversation messages:", error);
      if (!loadMore) setChatList([]); // Chỉ reset nếu không phải đang tải thêm
    } finally {
      setIsLoadingMessages(false);
    }
  };

  // Thêm state để quản lý việc tải thêm tin nhắn
  const [hasMoreMessages, setHasMoreMessages] = useState<boolean>(false);

  // Xử lý khi chọn một conversation
  const handleSelectConversation = (conversation: Conversation) => {
    setSelectedConversation(conversation);
    // Reset chat pagination khi chọn conversation mới
    setChatSkip(0);
    if (conversation.id) {
      fetchConversationMessages(conversation.id);
    }
  };

  // Theo dõi việc thay đổi conversation
  useEffect(() => {
    if (selectedConversation?.id) {
      setChatSkip(0); // Reset skip khi đổi conversation
      fetchConversationMessages(selectedConversation.id);
    }
  }, [selectedConversation?.id]);

  // Cập nhật useEffect để không gọi API khi đang tải
  useEffect(() => {
    // Chỉ gọi khi skip > 0 (không phải lần đầu tiên) và có conversation được chọn
    if (chatSkip > 0 && selectedConversation?.id && !isLoadingMessages) {
      setIsLoadingMessages(true);
      fetchConversationMessages(selectedConversation.id, true).finally(() => {
        setIsLoadingMessages(false);
      });
    }
  }, [chatSkip, selectedConversation?.id]);

  useEffect(() => {
    fetchConversations();
  }, [skip]);

  // Thêm ở đầu component
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const prevScrollHeight = useRef<number>(0);
  const prevScrollTop = useRef<number>(0);

  // Thêm useEffect để xử lý việc giữ vị trí cuộn
  useEffect(() => {
    if (chatContainerRef.current && prevScrollHeight.current > 0) {
      const newScrollHeight = chatContainerRef.current.scrollHeight;
      const heightDifference = newScrollHeight - prevScrollHeight.current;

      chatContainerRef.current.scrollTop =
        prevScrollTop.current + heightDifference;

      // Reset sau khi đã xử lý
      prevScrollHeight.current = 0;
      prevScrollTop.current = 0;
    }
  }, [chatList]);

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
            conversationLimit={conversationLimit}
            conversations={conversations}
            isLoading={isLoading}
            hasNext={hasNext}
            setSkip={setSkip}
            selectedConversation={selectedConversation}
            handleSelectConversation={handleSelectConversation}
          />
        </div>

        {/* Middle - Chat Area */}
        

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
