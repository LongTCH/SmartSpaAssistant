"use client";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { ChatContent, Conversation, ProviderType } from "@/types";
import Image from "next/image";

export default function ConversationInfo({
  item,
  isSelected,
  isUnread = false,
  onClick,
}: {
  item: Conversation;
  isSelected: boolean;
  isUnread?: boolean;
  onClick: () => void;
}) {
  const getTimeDifference = (date: string) => {
    const now = new Date();
    const messageDate = new Date(date);
    const timeDiff = now.getTime() - messageDate.getTime();
    const seconds = Math.floor(timeDiff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    const months = Math.floor(days / 30);
    const years = Math.floor(months / 12);

    if (years > 0) return `${years} year${years > 1 ? "s" : ""} ago`;
    if (months > 0) return `${months} month${months > 1 ? "s" : ""} ago`;
    if (days > 0) return `${days} day${days > 1 ? "s" : ""} ago`;
    if (hours > 0) return `${hours} hour${hours > 1 ? "s" : ""} ago`;
    if (minutes > 0) return `${minutes} minute${minutes > 1 ? "s" : ""} ago`;
    if (seconds > 0) return `${seconds} second${seconds > 1 ? "s" : ""} ago`;
    return "just now";
  };

  const getLastMessage = (content: ChatContent) => {
    if (!content || !content.message) return "No messages yet";
    let message = "";
    if (content.side === "staff") {
      message += "You: ";
    }
    if (content.message.text) {
      message += content.message.text;
    }
    return message;
  };

  const handleClick = () => {
    // Call the original onClick handler to update state
    onClick();

    // Update URL without triggering a full page reload
    window.history.pushState({}, "", `/conversations/${item.id}`);
  };

  // Function to get the provider icon path
  const getProviderIcon = (provider: ProviderType | undefined) => {
    switch (provider) {
      case "messenger":
        return "/messenger.svg";
      case "web":
        return "/web.svg";
      default:
        return null;
    }
  };

  return (
    <div
      onClick={handleClick}
      className={`p-3 border-b hover:bg-indigo-50 cursor-pointer ${
        isSelected ? "bg-indigo-50" : ""
      } ${isUnread ? "bg-blue-50/60" : ""}`}
    >
      <div className="flex items-start space-x-3">
        <div className="relative">
          <Avatar>
            <AvatarImage src={item.avatar} />
            <AvatarFallback>?</AvatarFallback>
          </Avatar>
          {/* Provider icon indicator positioned in bottom right of avatar */}
          {item.provider && getProviderIcon(item.provider) && (
            <div className="absolute -bottom-1 -right-1 w-5 h-5 rounded-full bg-white p-0.5 shadow-sm">
              <Image
                src={getProviderIcon(item.provider) || ""}
                alt={item.provider || ""}
                width={16}
                height={16}
                className="w-full h-full object-contain"
                title={item.provider || ""}
              />
            </div>
          )}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex justify-between">
            <div className="flex items-center space-x-2">
              <div className="flex items-center">
                <p
                  className={`font-medium truncate ${
                    isUnread ? "font-bold" : ""
                  }`}
                >
                  {item.account_name}
                </p>
                {isUnread && (
                  <div className="ml-2 w-2 h-2 bg-blue-500 rounded-full"></div>
                )}
              </div>
            </div>
            <span className="text-[10px] text-gray-500">
              {getTimeDifference(item.last_chat_message.created_at)}
            </span>
          </div>
          <p
            className={`text-sm ${
              isUnread ? "text-black font-medium" : "text-gray-500"
            } truncate`}
          >
            {getLastMessage(item.last_chat_message.content)}
          </p>
        </div>
      </div>
    </div>
  );
}
