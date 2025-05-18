"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { conversationService } from "@/services/api/conversation.service";
import { LoadingScreen } from "@/components/loading-screen";
import { Button } from "@/components/ui/button";
import { MessageSquare } from "lucide-react";

export default function ConversationsPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [hasConversations, setHasConversations] = useState<boolean | null>(
    null
  );

  // Fetch first conversation and redirect when the page loads
  useEffect(() => {
    conversationService
      .getPagingConversation(0, 1)
      .then((response) => {
        if (response.data && response.data.length > 0) {
          const firstConversation = response.data[0];
          router.push(`/conversations/${firstConversation.id}`);
        } else {
          // Handle case when no conversations exist
          setHasConversations(false);
          setLoading(false);
        }
      })
      .catch(() => {
        setLoading(false);
        setHasConversations(false);
      });
  }, [router]);

  // Show empty state if no conversations exist
  if (!loading && hasConversations === false) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-6">
        <div className="flex flex-col items-center justify-center max-w-md text-center">
          <div className="bg-primary/10 p-3 rounded-full mb-4">
            <MessageSquare className="h-10 w-10 text-primary" />
          </div>
          <h2 className="text-2xl font-bold mb-2">
            Chưa có cuộc trò chuyện nào
          </h2>
          <p className="text-muted-foreground mb-4">
            Bạn chưa có cuộc trò chuyện nào. Hãy tạo cuộc trò chuyện mới để bắt
            đầu.
          </p>
          <Button
            onClick={() => router.push("/customers")}
            className="bg-primary hover:bg-primary/90"
          >
            Tìm khách hàng
          </Button>
        </div>
      </div>
    );
  }

  // Show loading screen while redirecting
  return <LoadingScreen />;
}
