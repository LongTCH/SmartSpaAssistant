import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Info } from "lucide-react";
import { Conversation, ProviderType } from "@/types";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { conversationService } from "@/services/api/conversation.service";
import { toast } from "sonner";


import { useState, useEffect } from "react";
import Image from "next/image";

interface ChatHeaderProps {
  conversationData: Conversation | null;
  toggleSupportPanel?: () => void; // Added
  selectedConversationId: string | null;
  onConversationUpdated?: (conversation: Conversation) => void;
}

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

export default function ChatHeader(props: ChatHeaderProps) {
  const [currentAssignment, setCurrentAssignment] = useState<string>("ai");

  // Update currentAssignment when conversationData changes
  useEffect(() => {
    if (props.conversationData && props.conversationData.assigned_to) {
      setCurrentAssignment(props.conversationData.assigned_to);
    }
  }, [props.conversationData]);

  return (
    <div className="p-3 border-b bg-white flex items-center gap-2">
      <div className="flex items-center justify-between flex-1">
        <div className="flex items-center space-x-2">
          <div className="relative">
            <Avatar className="w-10 h-10">
              <AvatarImage src={props.conversationData?.avatar} />
              <AvatarFallback>?</AvatarFallback>
            </Avatar>
            {/* Provider icon indicator positioned in bottom right of avatar */}
            {props.conversationData?.provider &&
              getProviderIcon(props.conversationData?.provider) && (
                <div className="absolute -bottom-1 -right-1 w-5 h-5 rounded-full bg-white p-0.5 shadow-sm">
                  <Image
                    src={
                      getProviderIcon(props.conversationData?.provider) || ""
                    }
                    alt={props.conversationData?.provider || ""}
                    width={16}
                    height={16}
                    className="w-full h-full object-contain"
                    title={props.conversationData?.provider || ""}
                  />
                </div>
              )}
          </div>
          <span className="text-sm font-medium text-gray-800">
            {props.conversationData?.account_name || "Khách hàng"}
          </span>
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
                } catch {
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
          onClick={props.toggleSupportPanel} // Changed from onClick={() => props.setShowUserInfo(true)}
        >
          <Info className="h-4 w-4" />
          <span className="sr-only">Information</span>
        </Button>
      </div>
    </div>
  );
}
