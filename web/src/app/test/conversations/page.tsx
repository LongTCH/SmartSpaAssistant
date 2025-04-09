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

export default function ChatInterface() {
  const { contentHeight } = useApp();

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

          <div className="flex-1 overflow-auto">
            {/* Conversation Items */}
            {[1, 2, 3, 4, 5, 6, 7, 8].map((item, index) => (
              <div
                key={item}
                className={`p-3 border-b hover:bg-indigo-50 cursor-pointer ${
                  index === 0
                    ? "border-l-4 border-l-red-500"
                    : index === 2
                    ? "border-l-4 border-l-green-500"
                    : ""
                } ${index === 0 ? "bg-indigo-100 font-semibold" : ""}`}
              >
                <div className="flex items-start space-x-3">
                  <Avatar>
                    <AvatarImage src="/placeholder.svg?height=40&width=40" />
                    <AvatarFallback>SA</AvatarFallback>
                  </Avatar>
                  <div className="flex-1 min-w-0">
                    <div className="flex justify-between">
                      <div className="flex items-center space-x-2">
                        <p className="font-medium truncate">Suporte ADMIN</p>
                        <Badge
                          variant="outline"
                          className="bg-[#0084FF]/10 text-[#0084FF] border-[#0084FF]/20 text-[10px] px-1.5 py-0 h-4 rounded-sm flex items-center"
                        >
                          Messenger
                        </Badge>
                      </div>
                      <span className="text-xs text-gray-500">10 min</span>
                    </div>
                    <p className="text-sm text-gray-500 truncate">
                      Supporting line text lorem ipsum dolor sit amet...
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Middle - Chat Area */}
        <div className="flex-1 flex flex-col bg-gray-50">
          {/* Chat Header */}
          <div className="p-3 border-b bg-white flex items-center gap-2">
            <div className="flex items-center justify-between flex-1">
              <div className="flex items-center space-x-2">
                <Popover>
                  <PopoverTrigger asChild>
                    <Button
                      variant="link"
                      size="icon"
                      className="w-10 h-10 rounded-full bg-red-500 flex items-center justify-center mr-4"
                    >
                      <Frown className="h-6 w-6 text-white" />
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-80 p-4">
                    <div className="space-y-2">
                      <h4 className="font-medium">Dự đoán cảm xúc</h4>
                      <p className="text-sm text-gray-500">
                        AI dự đoán cảm xúc của người dùng trong cuộc trò chuyện
                        này là <strong>tiêu cực</strong>.
                      </p>
                    </div>
                  </PopoverContent>
                </Popover>
                <span className="text-sm font-medium text-gray-800">
                  Suporte ADMIN
                </span>
                <Badge
                  variant="outline"
                  className="bg-[#0084FF]/10 text-[#0084FF] border-[#0084FF]/20 text-[10px] px-1.5 py-0 h-4 rounded-sm flex items-center"
                >
                  Messenger
                </Badge>
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
                    This conversation is being handled by AI support. Response
                    time may vary based on query complexity.
                  </p>
                </div>
              </PopoverContent>
            </Popover>
          </div>

          {/* Chat Messages Area - Restructured for scrollable messages with fixed bottom note */}
          <div className="h-[10vh] flex-1 flex flex-col">
            {/* Scrollable Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {/* Sender Message */}
              <div className="flex items-start space-x-2 max-w-[80%]">
                <div className="w-8 h-8 rounded-full bg-gray-300 flex items-center justify-center text-xs">
                  OP
                </div>
                <div>
                  <div className="bg-white p-3 rounded-lg shadow-sm">
                    <p className="text-sm">
                      Lorem Ipsum has been the industry's standard dummy text
                      ever since the 1500s.
                    </p>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">8:00 PM</div>
                </div>
              </div>
              {/* Receiver Message */}
              <div className="flex items-start justify-end space-x-2 max-w-[80%] ml-auto">
                <div>
                  <div className="bg-indigo-500 p-3 rounded-lg shadow-sm">
                    <p className="text-sm text-white">
                      Lorem Ipsum has been the industry's standard dummy text
                      ever since the 1500s.
                    </p>
                  </div>
                  <div className="text-xs text-gray-500 mt-1 text-right">
                    8:00 PM
                  </div>
                </div>
                <Avatar className="w-8 h-8">
                  <AvatarImage src="/placeholder.svg?height=32&width=32" />
                  <AvatarFallback>SA</AvatarFallback>
                </Avatar>
              </div>
              {/* Sender Message */}
              <div className="flex items-start space-x-2 max-w-[80%]">
                <div className="w-8 h-8 rounded-full bg-gray-300 flex items-center justify-center text-xs">
                  OP
                </div>
                <div>
                  <div className="bg-white p-3 rounded-lg shadow-sm">
                    <p className="text-sm">
                      Lorem Ipsum has been the industry's standard dummy text
                      ever since the 1500s.
                    </p>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">8:00 PM</div>
                </div>
              </div>
              {/* Receiver Message */}
              <div className="flex items-start justify-end space-x-2 max-w-[80%] ml-auto">
                <div>
                  <div className="bg-indigo-500 p-3 rounded-lg shadow-sm">
                    <p className="text-sm text-white">
                      Lorem Ipsum has been the industry's standard dummy text
                      ever since the 1500s.
                    </p>
                  </div>
                  <div className="text-xs text-gray-500 mt-1 text-right">
                    8:00 PM
                  </div>
                </div>
                <Avatar className="w-8 h-8">
                  <AvatarImage src="/placeholder.svg?height=32&width=32" />
                  <AvatarFallback>SA</AvatarFallback>
                </Avatar>
              </div>{" "}
              {/* Sender Message */}
              <div className="flex items-start space-x-2 max-w-[80%]">
                <div className="w-8 h-8 rounded-full bg-gray-300 flex items-center justify-center text-xs">
                  OP
                </div>
                <div>
                  <div className="bg-white p-3 rounded-lg shadow-sm">
                    <p className="text-sm">
                      Lorem Ipsum has been the industry's standard dummy text
                      ever since the 1500s.
                    </p>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">8:00 PM</div>
                </div>
              </div>
              {/* Sender Message */}
              <div className="flex items-start space-x-2 max-w-[80%]">
                <div className="w-8 h-8 rounded-full bg-gray-300 flex items-center justify-center text-xs">
                  OP
                </div>
                <div>
                  <div className="bg-white p-3 rounded-lg shadow-sm">
                    <p className="text-sm">
                      Lorem Ipsum has been the industry's standard dummy text
                      ever since the 1500s.
                    </p>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">8:00 PM</div>
                </div>
              </div>
              {/* Sender Message */}
              <div className="flex items-start space-x-2 max-w-[80%]">
                <div className="w-8 h-8 rounded-full bg-gray-300 flex items-center justify-center text-xs">
                  OP
                </div>
                <div>
                  <div className="bg-white p-3 rounded-lg shadow-sm">
                    <p className="text-sm">
                      Lorem Ipsum has been the industry's standard dummy text
                      ever since the 1500s.
                    </p>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">8:00 PM</div>
                </div>
              </div>
              {/* Sender Message */}
              <div className="flex items-start space-x-2 max-w-[80%]">
                <div className="w-8 h-8 rounded-full bg-gray-300 flex items-center justify-center text-xs">
                  OP
                </div>
                <div>
                  <div className="bg-white p-3 rounded-lg shadow-sm">
                    <p className="text-sm">
                      Lorem Ipsum has been the industry's standard dummy text
                      ever since the 1500s.
                    </p>
                  </div>
                  <div className="text-xs text-gray-500 mt-1">8:00 PM</div>
                </div>
              </div>
            </div>

            {/* Fixed System Message at Bottom */}
            {/* Fixed System Message at Bottom - Will stick to bottom even when chat scrolls */}
            <div className="p-2 border-t bg-white sticky bottom-0 z-10">
              <div className="text-xs text-gray-500 text-center bg-gray-50 py-2 rounded border border-gray-200">
                Xin lỗi, việc nhận tin trực tiếp không được hỗ trợ. Vui lòng
                dùng Messenger.
              </div>
            </div>
          </div>
        </div>

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
