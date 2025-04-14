"use client";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { ChatContent, Conversation, ProviderType } from "@/types";
export const getBadge = (provider: ProviderType | undefined) => {
  switch (provider) {
    case "messenger":
      return (
        <Badge
          variant="outline"
          className="bg-[#0084FF]/10 text-[#0084FF] border-[#0084FF]/20 text-[10px] px-1.5 py-0 h-4 rounded-sm flex items-center"
        >
          Messenger
        </Badge>
      );
    case "web":
      return (
        <Badge
          variant="outline"
          className="bg-[#22C55E]/10 text-[#22C55E] border-[#22C55E]/20 text-[10px] px-1.5 py-0 h-4 rounded-sm flex items-center"
        >
          Web
        </Badge>
      );
    default:
      return null;
  }
};
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

  const getSentiment = () => {
    return Date.now() % 3 === 2
      ? "positive"
      : Date.now() % 3 === 1
      ? "negative"
      : "neutral";
  };

  const getLastMessage = (content: ChatContent) => {
    let message = "";
    if (content.side === "staff") {
      message += "You: ";
    }
    if (content.message.text) {
      message += content.message.text;
    }
    return message;
  };

  return (
    <div
      onClick={onClick}
      className={`p-3 border-b hover:bg-indigo-50 cursor-pointer ${
        isSelected ? "bg-indigo-50" : ""
      } ${
        getSentiment() === "negative"
          ? "border-l-4 border-l-red-500"
          : getSentiment() === "positive"
          ? "border-l-4 border-l-green-500"
          : "border-l-4"
      } ${isUnread ? "bg-blue-50/60" : ""}`}
    >
      <div className="flex items-start space-x-3">
        <Avatar>
          <AvatarImage src={item.avatar} />
          <AvatarFallback>?</AvatarFallback>
        </Avatar>
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
              {getBadge(item.provider)}
            </div>
            <span className="text-[10px] text-gray-500">
              {getTimeDifference(item.last_message_at)}
            </span>
          </div>
          <p
            className={`text-sm ${
              isUnread ? "text-black font-medium" : "text-gray-500"
            } truncate`}
          >
            {getLastMessage(item.last_message)}
          </p>
        </div>
      </div>
    </div>
  );
}
