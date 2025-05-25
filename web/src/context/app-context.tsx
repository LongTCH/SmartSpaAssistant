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
  activeNavTab: string;
  isPageLoading: boolean;
  hasNewAlerts: boolean;
  setActiveNavTab: (tab: string) => void;
  setContentHeight: (height: string) => void;
  setPageLoading: (loading: boolean) => void;
  setHasNewAlerts: (hasAlerts: boolean) => void;
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
  setIsWebSocketConnected: (connected: boolean) => void;
  messageHandlersRef: React.MutableRefObject<Map<string, Set<MessageHandler>>>;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: ReactNode }) {
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(true);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isPageLoading, setPageLoading] = useState<boolean>(false);
  const [contentHeight, setContentHeight] = useState<string>("100vh");
  const [activeNavTab, setActiveNavTab] = useState<string>("");
  const [hasNewAlerts, setHasNewAlerts] = useState<boolean>(false);
  const [isWebSocketConnected, setIsWebSocketConnected] =
    useState<boolean>(false);
  const router = useRouter();
  const pathname = usePathname();
  const messageHandlersRef = useRef<Map<string, Set<MessageHandler>>>(
    new Map()
  );

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
      const wsRef = (window as any).__webSocketRef;
      if (wsRef?.current && isWebSocketConnected) {
        wsRef.current.send(JSON.stringify(message));
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

    // Đặt activeNavTab dựa trên pathname hiện tại
    if (pathname === "/conversations") {
      setActiveNavTab("messages");
    } else if (pathname === "/settings") {
      setActiveNavTab("settings");
    } else if (pathname === "/analysis") {
      setActiveNavTab("analysis");
    } else if (pathname === "/customers") {
      setActiveNavTab("customers");
    }
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
    } catch {
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
    activeNavTab,
    setActiveNavTab,
    isPageLoading,
    setPageLoading,
    hasNewAlerts,
    setHasNewAlerts,
    registerMessageHandler,
    sendWebSocketMessage,
    isWebSocketConnected,
    setIsWebSocketConnected,
    messageHandlersRef,
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
