"use client";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Bell, User, LogOut, MessageSquare } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useApp } from "@/context/app-context";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Image from "next/image";

export function Navbar() {
  const {
    activeNavTab,
    setActiveNavTab,
    logout,
    setPageLoading,
    isPageLoading,
  } = useApp();
  const router = useRouter();
  const handleTabChange = (value: string) => {
    // Nếu đang loading, không cho phép chuyển tab
    if (isPageLoading) return;

    // Nếu tab đã active, không cần chuyển đổi
    if (activeNavTab === value) {
      return;
    }

    // Đặt tab active ngay lập tức
    setActiveNavTab(value);

    // Bắt đầu hiển thị loading
    setPageLoading(true);

    // Chuyển hướng đến trang tương ứng
    switch (value) {
      case "messages":
        router.push("/conversations");
        break;
      case "settings":
        router.push("/settings");
        break;
      case "analysis":
        router.push("/analysis");
        break;
      case "customers":
        router.push("/customers");
        break;
      case "test-chat":
        router.push("/test-chat");
        break;
      case "notifications":
        router.push("/notifications");
        break;
      default:
        setPageLoading(false); // Ensure loading is stopped for unhandled cases
        break;
    }
  };

  // Helper function to get URL from tab value
  const getTabUrl = (tab: string) => {
    switch (tab) {
      case "messages":
        return "/conversations";
      case "settings":
        return "/settings";
      case "analysis":
        return "/analysis";
      case "customers":
        return "/customers";
      case "test-chat":
        return "/test-chat";
      case "notifications": // Added new case for notifications
        return "/notifications";
      default:
        return "#";
    }
  };

  return (
    <header className="flex items-center justify-between px-6 py-3 bg-indigo-600 text-white">
      <div className="flex items-center space-x-4">
        <div className="flex items-center mr-4">
          <Link href="/" className="flex items-center space-x-2">
            <Image
              width={32}
              height={32}
              src="/smart-spa.png"
              alt="Smart SPA Logo"
            />
          </Link>
        </div>

        <Tabs
          value={activeNavTab}
          onValueChange={handleTabChange}
          className="w-auto"
        >
          <TabsList
            className={`bg-white/10 h-10 p-1 rounded-full ${
              isPageLoading ? "opacity-70 pointer-events-none" : ""
            }`}
          >
            <TabsTrigger
              value="messages"
              disabled={isPageLoading}
              className={`px-4 text-sm font-medium rounded-full cursor-pointer ${
                activeNavTab === "messages"
                  ? "bg-white text-[#6366F1]"
                  : "text-white/90"
              }`}
            >
              <Link
                href={getTabUrl("messages")}
                className="w-full h-full block"
                onClick={(e) => e.preventDefault()}
              >
                Tin nhắn
              </Link>
            </TabsTrigger>
            <TabsTrigger
              value="settings"
              disabled={isPageLoading}
              className={`px-4 text-sm font-medium rounded-full cursor-pointer ${
                activeNavTab === "settings"
                  ? "bg-white text-[#6366F1]"
                  : "text-white/90"
              }`}
            >
              <Link
                href={getTabUrl("settings")}
                className="w-full h-full block"
                onClick={(e) => e.preventDefault()}
              >
                Cài đặt
              </Link>
            </TabsTrigger>
            <TabsTrigger
              value="customers"
              disabled={isPageLoading}
              className={`px-4 text-sm font-medium rounded-full cursor-pointer ${
                activeNavTab === "customers"
                  ? "bg-white text-[#6366F1]"
                  : "text-white/90"
              }`}
            >
              <Link
                href={getTabUrl("customers")}
                className="w-full h-full block"
                onClick={(e) => e.preventDefault()}
              >
                QL Khách hàng
              </Link>
            </TabsTrigger>{" "}
            <TabsTrigger
              value="analysis"
              disabled={isPageLoading}
              className={`px-4 text-sm font-medium rounded-full cursor-pointer ${
                activeNavTab === "analysis"
                  ? "bg-white text-[#6366F1]"
                  : "text-white/90"
              }`}
            >
              <Link
                href={getTabUrl("analysis")}
                className="w-full h-full block"
                onClick={(e) => e.preventDefault()}
              >
                Phân tích bài đăng
              </Link>
            </TabsTrigger>
          </TabsList>
        </Tabs>
      </div>{" "}
      <div className="flex items-center space-x-4">
        {" "}
        <Button
          variant="ghost"
          size="icon"
          className={`${
            activeNavTab === "test-chat"
              ? "bg-white text-[#6366F1]"
              : "text-white/90 hover:text-white hover:bg-white/10"
          } rounded-full`}
          disabled={isPageLoading}
          onClick={() => {
            if (isPageLoading) return;
            router.push("/test-chat");
            setActiveNavTab("test-chat");
          }}
          title="Test Chat"
        >
          <MessageSquare className="h-5 w-5" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className={`${
            activeNavTab === "notifications"
              ? "bg-white text-[#6366F1]"
              : "text-white/90 hover:text-white hover:bg-white/10"
          } rounded-full`}
          disabled={isPageLoading}
          onClick={() => {
            if (isPageLoading) return;
            router.push("/notifications");
            setActiveNavTab("notifications");
          }}
          title="Notifications"
        >
          <Bell className="h-5 w-5" />
        </Button>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="text-white/90 hover:text-white hover:bg-white/10 rounded-full"
              disabled={isPageLoading}
            >
              <User className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>My Account</DropdownMenuLabel>
            <DropdownMenuItem
              className="text-destructive"
              onClick={logout}
              disabled={isPageLoading}
            >
              <LogOut className="h-4 w-4 mr-2" />
              Logout
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
