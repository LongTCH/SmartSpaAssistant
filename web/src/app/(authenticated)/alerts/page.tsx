"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Alert } from "@/types";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import AlertList from "./components/AlertList";
import { useApp } from "@/context/app-context";
import { Button } from "@/components/ui/button"; // Import Button
import { Bell, MessageSquare, Settings } from "lucide-react"; // Import icons

export default function AlertsPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const { setPageLoading, setActiveNavTab } = useApp();
  const [activeFilter, setActiveFilter] = useState("all"); // State for active filter

  useEffect(() => {
    // Set the active tab
    setActiveNavTab("alerts");

    // Simulate loading for initial page render
    const timer = setTimeout(() => {
      setLoading(false);
      setPageLoading(false); // Turn off the page loading indicator
    }, 500);

    return () => clearTimeout(timer);
  }, [setPageLoading, setActiveNavTab]);

  const handleSelectAlert = (alert: Alert) => {
    if (alert.guest_id) {
      // Navigate to the conversation with this guest
      router.push(`/conversations/${alert.guest_id}`);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="w-10 h-10 border-4 border-t-indigo-500 border-indigo-200 rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8">
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <CardTitle>Quản lý thông báo</CardTitle>
            {/* Add Mark all as read and Clear all buttons here if needed */}
          </div>
          <CardDescription>
            Xem danh sách các thông báo từ khách hàng và hệ thống
          </CardDescription>
          {/* Tabs for All, System, Chat */}
          <div className="flex space-x-2 pt-4">
            <Button
              variant={activeFilter === "all" ? "default" : "outline"}
              onClick={() => setActiveFilter("all")}
              className={`flex items-center space-x-2 ${
                activeFilter === "all" ? "bg-blue-500 text-white" : ""
              }`}
            >
              <Bell className="h-4 w-4" />
              <span>All</span>
              {/* Add count here if available */}
            </Button>
            <Button
              variant={activeFilter === "system" ? "default" : "outline"}
              onClick={() => setActiveFilter("system")}
              className={`flex items-center space-x-2 ${
                activeFilter === "system" ? "bg-blue-500 text-white" : ""
              }`}
            >
              <Settings className="h-4 w-4" />
              <span>System</span>
              {/* Add count here if available */}
            </Button>
            <Button
              variant={activeFilter === "chat" ? "default" : "outline"}
              onClick={() => setActiveFilter("chat")}
              className={`flex items-center space-x-2 ${
                activeFilter === "chat" ? "bg-blue-500 text-white" : ""
              }`}
            >
              <MessageSquare className="h-4 w-4" />
              <span>Chat</span>
              {/* Add count here if available */}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <AlertList
            onSelectAlert={handleSelectAlert}
            activeFilter={activeFilter}
          />
        </CardContent>
      </Card>
    </div>
  );
}
