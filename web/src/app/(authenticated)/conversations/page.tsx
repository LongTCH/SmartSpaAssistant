"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { conversationService } from "@/services/api/conversation.service";
import { LoadingScreen } from "@/components/loading-screen";

export default function ConversationsPage() {
  const router = useRouter();

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
          // You might want to show a different screen or create a new conversation
        }
      })
      .catch((error) => {
      });
  }, [router]);

  // Show loading screen while redirecting
  return <LoadingScreen />;
}
