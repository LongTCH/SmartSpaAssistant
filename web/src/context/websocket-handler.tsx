"use client";

import { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { useToast } from "@/context/toast-provider";
import { useApp } from "@/context/app-context";
import { WS_MESSAGES, APP_ROUTES } from "@/lib/constants";

// Define the structure of the alert data expected from WebSocket
interface AlertNotificationData {
  content: string;
  guest_id: string;
  notification?: {
    label: string;
    color: string;
  };
}

type WebSocketMessage = {
  message: string;
  data: any;
};

export function WebSocketHandler() {
  const router = useRouter();
  const { showToast } = useToast();
  const {
    isLoggedIn,
    setIsWebSocketConnected,
    setHasNewAlerts,
    messageHandlersRef,
  } = useApp();
  const webSocketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!isLoggedIn) return;

    const connectWebSocket = () => {
      const wsUrl = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8080/ws";
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setIsWebSocketConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const parsedMessage = JSON.parse(event.data) as WebSocketMessage;

          // Handle ALERT messages
          if (parsedMessage.message === WS_MESSAGES.ALERT) {
            setHasNewAlerts(true);
            const alertData = parsedMessage.data as AlertNotificationData;

            showToast({
              label: alertData.notification?.label || "Alert",
              content: alertData.content,
              color: alertData.notification?.color || "default",
              duration: 15000,
              onClick: () => {
                if (alertData.guest_id) {
                  router.push(
                    `${APP_ROUTES.CONVERSATIONS}/${alertData.guest_id}`
                  );
                }
              },
            });
          }

          // Notify all handlers registered for this message type
          const handlers = messageHandlersRef.current.get(
            parsedMessage.message
          );
          if (handlers) {
            handlers.forEach((handler) => {
              try {
                handler(parsedMessage.data);
              } catch {}
            });
          }
        } catch {}
      };

      ws.onerror = () => {
        setIsWebSocketConnected(false);
      };

      ws.onclose = () => {
        setIsWebSocketConnected(false);

        // Try to reconnect after a delay
        setTimeout(() => {
          if (isLoggedIn) connectWebSocket();
        }, 3000);
      };

      webSocketRef.current = ws;
    };

    connectWebSocket();

    return () => {
      if (webSocketRef.current) {
        webSocketRef.current.close();
        webSocketRef.current = null;
      }
    };
  }, [
    isLoggedIn,
    router,
    showToast,
    setIsWebSocketConnected,
    setHasNewAlerts,
    messageHandlersRef,
  ]);

  // Expose webSocket instance for sending messages
  useEffect(() => {
    // Store webSocket reference in a way that can be accessed by AppProvider
    (window as any).__webSocketRef = webSocketRef;
  }, []);

  return null; // This component doesn't render anything
}
