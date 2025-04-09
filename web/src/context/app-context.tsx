"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  ReactNode,
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

interface AppContextType {
  isLoggedIn: boolean;
  isLoading: boolean;
  contentHeight: string;
  setContentHeight: (height: string) => void;
  logout: () => Promise<void>;
  checkAuth: () => Promise<boolean>;
  loginSuccess: (accessToken: string, user: User) => void;
  getAuthUser: () => User | null;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: ReactNode }) {
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [contentHeight, setContentHeight] = useState<string>("100vh");
  const router = useRouter();
  const pathname = usePathname();

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
