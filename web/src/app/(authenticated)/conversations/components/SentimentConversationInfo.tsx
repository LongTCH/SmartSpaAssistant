"use client";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Conversation } from "@/types";
import { useRouter } from "next/navigation";

interface SentimentConversationInfoProps {
  conversation: Conversation;
  onClick: () => void;
  isSelected?: boolean;
  isUnread?: boolean;
}

export default function SentimentConversationInfo(
  props: SentimentConversationInfoProps
) {
  const router = useRouter();

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

  const handleClick = () => {
    // Call the original onClick handler to update state
    props.onClick();

    // Update URL without triggering a full page reload
    window.history.pushState({}, "", `/conversations/${props.conversation.id}`);
  };

  return (
    <div
      key={props.conversation.id}
      onClick={handleClick}
      className={`border rounded-md p-2 flex hover:bg-indigo-50 items-center space-x-2 cursor-pointer justify-between ${
        props.isSelected ? "bg-indigo-100 border-indigo-500" : ""
      } ${props.isUnread ? "bg-yellow-50" : ""}`}
    >
      <div className="flex items-center space-x-2">
        <Avatar className="h-8 w-8">
          <AvatarImage src={props.conversation.avatar} />
          <AvatarFallback>?</AvatarFallback>
        </Avatar>
        <span className="text-sm font-medium">
          {props.conversation.account_name}
        </span>
        {props.isUnread && (
          <span
            className="ml-1 w-2 h-2 bg-yellow-400 rounded-full inline-block"
            title="Chưa đọc"
          ></span>
        )}
      </div>
      <span className="text-xs text-gray-500 ml-2 text-right min-w-[80px]">
        {getTimeDifference(props.conversation.last_message_at)}
      </span>
    </div>
  );
}
