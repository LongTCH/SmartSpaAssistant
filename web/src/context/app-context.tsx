"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  ReactNode,
  useCallback,
  useRef,
} from "react";
import { useRouter, usePathname } from "next/navigation";
import {
  isAuthenticated,
  clearAuthTokens,
  setAuthTokens,
  setAuthUser,
  clearAuthUser,
} from "@/lib/auth";
import { APP_ROUTES } from "@/lib/constants";
import { logoutUser } from "./action";
import { User } from "@/schemas/auth";
import Cookies from "js-cookie";

type WebSocketMessage = {
  message: string;
  data: any;
};

type MessageHandler = (data: any) => void;

interface AppContextType {
  isLoggedIn: boolean;
  isLoading: boolean;
  contentHeight: string;
  setContentHeight: (height: string) => void;
  logout: () => Promise<void>;
  checkAuth: () => Promise<boolean>;
  loginSuccess: (accessToken: string, user: User) => void;
  getAuthUser: () => User | null;
  registerMessageHandler: (
    messageType: string,
    handler: MessageHandler
  ) => () => void;
  sendWebSocketMessage: (message: WebSocketMessage) => void;
  isWebSocketConnected: boolean;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: ReactNode }) {
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [contentHeight, setContentHeight] = useState<string>("100vh");
  const [isWebSocketConnected, setIsWebSocketConnected] =
    useState<boolean>(false);
  const router = useRouter();
  const pathname = usePathname();
  const webSocketRef = useRef<WebSocket | null>(null);
  const messageHandlersRef = useRef<Map<string, Set<MessageHandler>>>(
    new Map()
  );

  // WebSocket connection setup
  useEffect(() => {
    // if (!isLoggedIn) return;

    const connectWebSocket = () => {
      const wsUrl = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8080/ws";
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setIsWebSocketConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as WebSocketMessage;
          console.log("WebSocket message received:", data);

          // Notify all handlers registered for this message type
          const handlers = messageHandlersRef.current.get(data.message);
          if (handlers) {
            handlers.forEach((handler) => {
              try {
                handler(data.data);
              } catch (err) {
                console.error(
                  `Error in WebSocket message handler for ${data.message}:`,
                  err
                );
              }
            });
          }
        } catch (err) {
          console.error("Error parsing WebSocket message:", err);
        }
      };

      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
      };

      ws.onclose = () => {
        console.log("WebSocket connection closed");
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
  }, []);

  const registerMessageHandler = useCallback(
    (messageType: string, handler: MessageHandler) => {
      if (!messageHandlersRef.current.has(messageType)) {
        messageHandlersRef.current.set(messageType, new Set());
      }

      messageHandlersRef.current.get(messageType)!.add(handler);

      // Return a function to unregister this handler
      return () => {
        const handlers = messageHandlersRef.current.get(messageType);
        if (handlers) {
          handlers.delete(handler);
          if (handlers.size === 0) {
            messageHandlersRef.current.delete(messageType);
          }
        }
      };
    },
    []
  );

  const sendWebSocketMessage = useCallback(
    (message: WebSocketMessage) => {
      if (webSocketRef.current && isWebSocketConnected) {
        webSocketRef.current.send(JSON.stringify(message));
      } else {
        console.warn(
          "Attempted to send message but WebSocket is not connected"
        );
      }
    },
    [isWebSocketConnected]
  );

  useEffect(() => {
    const checkInitialAuth = async () => {
      const authenticated = await checkAuth();
      setIsLoggedIn(authenticated);
      setIsLoading(false);
    };

    checkInitialAuth();
  }, [pathname]);

  const checkAuth = async () => {
    const authenticated = isAuthenticated();
    setIsLoggedIn(authenticated);
    return authenticated;
  };

  const loginSuccess = (accessToken: string, user: User) => {
    setAuthTokens({ accessToken });
    setAuthUser(user);
    setIsLoggedIn(true);
  };

  const getAuthUser = () => {
    let userStr = null;
    if (typeof window !== "undefined") {
      userStr = Cookies.get("auth-user");
    } else {
      userStr = localStorage.getItem("authUser");
    }

    if (!userStr) {
      return null;
    }

    return JSON.parse(userStr) as User;
  };

  const logout = async () => {
    try {
      await logoutUser();
    } catch (error) {
      console.error("Error during logout:", error);
    } finally {
      clearAuthTokens();
      clearAuthUser();
      setIsLoggedIn(false);
      router.push(APP_ROUTES.LOGIN);
    }
  };

  const value = {
    isLoggedIn,
    isLoading,
    logout,
    checkAuth,
    loginSuccess,
    getAuthUser,
    contentHeight,
    setContentHeight,
    registerMessageHandler,
    sendWebSocketMessage,
    isWebSocketConnected,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export const useApp = () => {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error("useApp must be used within an AppProvider");
  }
  return context;
};

export const useAuth = () => {
  const { isLoggedIn, isLoading, logout, loginSuccess, getAuthUser } = useApp();
  return { isLoggedIn, isLoading, logout, loginSuccess, getAuthUser };
};
