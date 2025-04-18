"use client";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Bell, User, LogOut } from "lucide-react";
import ThemeToggle from "@/components/theme-toggle";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useRouter } from "next/navigation";
import { useApp } from "@/context/app-context";

export function Navbar() {
  const { activeNavTab, setActiveNavTab } = useApp();
  const router = useRouter();

  // Không cần theo dõi pathname nữa vì mỗi trang sẽ tự set activeNavTab

  const handleTabChange = (value: string) => {
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
      default:
        break;
    }
  };

  return (
    <header className="flex items-center justify-between px-6 py-3 bg-indigo-600 text-white">
      <div className="flex items-center space-x-4">
        <div className="w-9 h-9 rounded-full bg-white/10 flex items-center justify-center">
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM12 5C13.66 5 15 6.34 15 8C15 9.66 13.66 11 12 11C10.34 11 9 9.66 9 8C9 6.34 10.34 5 12 5ZM12 19.2C9.5 19.2 7.29 17.92 6 15.98C6.03 13.99 10 12.9 12 12.9C13.99 12.9 17.97 13.99 18 15.98C16.71 17.92 14.5 19.2 12 19.2Z"
              fill="white"
            />
          </svg>
        </div>

        <Tabs
          value={activeNavTab}
          onValueChange={handleTabChange}
          className="w-auto"
        >
          <TabsList className="bg-white/10 h-10 p-1 rounded-full">
            <TabsTrigger
              value="messages"
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
              className={`px-4 text-sm font-medium rounded-full cursor-pointer ${
                activeNavTab === "settings"
                  ? "bg-white text-[#6366F1]"
                  : "text-white/90"
              }`}
            >
              Cài đặt
            </TabsTrigger>
            <TabsTrigger
              value="analysis"
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
        >
          <Bell className="h-5 w-5" />
        </Button>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="text-white/90 hover:text-white hover:bg-white/10 rounded-full"
            >
              <User className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>My Account</DropdownMenuLabel>
            <DropdownMenuItem className="text-destructive">
              <LogOut className="h-4 w-4 mr-2" />
              Logout
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
