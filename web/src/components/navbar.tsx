"use client";
import { useState } from "react";
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

export function Navbar() {
  const [activeTab, setActiveTab] = useState("messages");

  return (
    <header className="flex items-center justify-between px-4 py-2 bg-indigo-600 text-white">
      <div className="flex items-center space-x-2">
        <div className="w-8 h-8 rounded-full bg-red-500 flex items-center justify-center">
          <span className="text-white font-bold">?</span>
        </div>

        <Tabs
          defaultValue="messages"
          value={activeTab}
          onValueChange={setActiveTab}
          className="w-auto"
        >
          <TabsList className="bg-transparent h-10">
            <TabsTrigger
              value="messages"
              className="data-[state=active]:bg-indigo-700 data-[state=active]:text-white text-white cursor-pointer"
            >
              Tin nhắn
            </TabsTrigger>
            <TabsTrigger
              value="analysis"
              className="data-[state=active]:bg-indigo-700 data-[state=active]:text-white text-white cursor-pointer"
            >
              Phân tích bài đăng
            </TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      <div className="flex items-center space-x-4">
        <Button variant="ghost" size="icon" className="text-white">
          <Bell className="h-5 w-5" />
        </Button>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="text-white">
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
