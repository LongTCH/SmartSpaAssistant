"use client";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Bell, User, LogOut } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useApp } from "@/context/app-context";
import { useRouter } from "next/navigation";

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
      default:
        break;
    }
  };

  return (
    <header className="flex items-center justify-between px-6 py-3 bg-indigo-600 text-white">
      <div className="flex items-center space-x-4">
        <div className="flex items-center mr-4">
          <img
            src="/smart-spa.png"
            alt="Smart Spa Logo"
            className="h-10 w-auto rounded"
          />
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
              Tin nhắn
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
              Cài đặt
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
              QL Khách hàng
            </TabsTrigger>
            <TabsTrigger
              value="analysis"
              disabled={isPageLoading}
              className={`px-4 text-sm font-medium rounded-full cursor-pointer ${
                activeNavTab === "analysis"
                  ? "bg-white text-[#6366F1]"
                  : "text-white/90"
              }`}
            >
              Phân tích bài đăng
            </TabsTrigger>
          </TabsList>
        </Tabs>
      </div>
      <div className="flex items-center space-x-4">
        <Button
          variant="ghost"
          size="icon"
          className="text-white/90 hover:text-white hover:bg-white/10 rounded-full"
          disabled={isPageLoading}
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
