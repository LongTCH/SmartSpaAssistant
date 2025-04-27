import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Info } from "lucide-react";
import { Conversation, SentimentType, ChatAssignmentType } from "@/types";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { conversationService } from "@/services/api/conversation.service";
import { toast } from "sonner";
import { getBadge } from "../ConversationInfo";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { useState, useEffect } from "react";
import { Frown, Smile } from "lucide-react";

interface ChatHeaderProps {
  conversationData: Conversation | null;
  setShowUserInfo: (show: boolean) => void;
  selectedConversationId: string | null;
  onConversationUpdated?: (conversation: Conversation) => void; // Add this prop
}
export default function ChatHeader(props: ChatHeaderProps) {
  const [currentAssignment, setCurrentAssignment] = useState<string>("ai");

  // Update currentAssignment when conversationData changes
  useEffect(() => {
    if (props.conversationData && props.conversationData.assigned_to) {
      setCurrentAssignment(props.conversationData.assigned_to);
    }
  }, [props.conversationData]);

  const getSentimentPopover = (sentiment: string) => {
    if (sentiment === "neutral") {
      return <></>;
    }

    return (
      <Popover>
        {sentiment === "negative" ? (
          <PopoverTrigger asChild>
            <Button variant="link" size="icon" className="w-5 h-5 rounded-full">
              <Frown className="h-6 w-6 text-red-500" />
            </Button>
          </PopoverTrigger>
        ) : (
          <PopoverTrigger asChild>
            <Button variant="link" size="icon" className="w-5 h-5 rounded-full">
              <Smile className="h-6 w-6 text-green-500" />
            </Button>
          </PopoverTrigger>
        )}
        {/* Popover content */}
        <PopoverContent className="w-80 p-4">
          <div className="space-y-2">
            <h4 className="font-medium">Dự đoán cảm xúc</h4>
            <p className="text-sm text-gray-500">
              AI dự đoán cảm xúc của người dùng trong đoạn hội thoại là{" "}
              <strong>
                {props.conversationData?.sentiment === "negative"
                  ? "tiêu cực"
                  : "tích cực"}
              </strong>
              .
            </p>
          </div>
        </PopoverContent>
      </Popover>
    );
  };
  return (
    <div className="p-3 border-b bg-white flex items-center gap-2">
      <div className="flex items-center justify-between flex-1">
        <div className="flex items-center space-x-2">
          <Avatar className="w-10 h-10">
            <AvatarImage src="/placeholder.svg?height=40&width=40" />
            <AvatarFallback>?</AvatarFallback>
          </Avatar>
          <span className="text-sm font-medium text-gray-800">
            {props.conversationData?.account_name || "Khách hàng"}
          </span>
          {getBadge(props.conversationData?.provider)}
          {props.conversationData?.sentiment &&
            getSentimentPopover(props.conversationData?.sentiment as string)}
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-600">Giao cho</span>
          <Select
            value={currentAssignment}
            onValueChange={async (value: string) => {
              if (props.selectedConversationId) {
                try {
                  // Cập nhật state trước để UI phản hồi ngay lập tức

                  // Cập nhật trạng thái phụ trách trên server
                  const updatedConversation =
                    await conversationService.updateAssignment(
                      props.selectedConversationId,
                      value
                    );
                  setCurrentAssignment(value);

                  // Notify parent component about the update
                  if (props.onConversationUpdated) {
                    props.onConversationUpdated(updatedConversation);
                  }

                  // Hiển thị thông báo thành công
                  toast.success(`Đã giao cho ${value === "ai" ? "AI" : "Tôi"}`);
                } catch (error) {
                  // Revert state if update fails (optional, depending on desired UX)
                  // setCurrentAssignment(props.conversationData?.assigned_to || 'ai');
                  toast.error("Lỗi khi cập nhật người phụ trách");
                }
              }
            }}
            disabled={!props.selectedConversationId}
          >
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

      <div className="flex items-center space-x-2">
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 rounded-full bg-primary/10 text-primary hover:bg-primary/20 transition-colors"
          onClick={() => props.setShowUserInfo(true)}
        >
          <Info className="h-4 w-4" />
          <span className="sr-only">Information</span>
        </Button>
      </div>
    </div>
  );
}
