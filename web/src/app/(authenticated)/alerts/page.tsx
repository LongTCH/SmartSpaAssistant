"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Alert } from "@/types";
import {
  Card,
  CardContent,
  // CardDescription, // No longer used directly here for main description
  // CardHeader, // No longer used for main page structure
  // CardTitle, // No longer used directly here for main title
} from "@/components/ui/card";
import AlertList from "./components/AlertList";
import { useApp } from "@/context/app-context";
import { Button } from "@/components/ui/button";
import { Bell, MessageSquare, Settings } from "lucide-react";

export default function AlertsPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const { setPageLoading, setActiveNavTab } = useApp();
  const [activeFilter, setActiveFilter] = useState("all"); // State for active filter

  useEffect(() => {
    setActiveNavTab("alerts");
    const timer = setTimeout(() => {
      setLoading(false);
      setPageLoading(false);
    }, 500);
    return () => clearTimeout(timer);
  }, [setPageLoading, setActiveNavTab]);

  const handleSelectAlert = (alert: Alert) => {
    if (alert.guest_id) {
      router.push(`/conversations/${alert.guest_id}`);
    }
    // If you implement marking as read on selection at this page level,
    // ensure AlertList also updates its local state or refetches.
    // For now, AlertList handles its own markAsRead via handleAlertItemClick.
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="w-10 h-10 border-4 border-t-indigo-500 border-indigo-200 rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-4">
      {/* New Standalone Header Section */}
      <div className="mb-5">
        {" "}
        {/* Increased bottom margin slightly for better separation */}
        <div className="flex justify-between items-center mb-1">
          {" "}
          {/* Adjusted margin bottom */}
          <h2 className="text-xl font-semibold text-gray-900">
            Quản lý thông báo
          </h2>
          {/* Placeholder for future buttons like "Mark all as read" */}
        </div>
        <p className="text-sm text-gray-600 mb-3">
          Xem danh sách các thông báo từ khách hàng và hệ thống
        </p>
        {/* Filter Buttons */}
        <div className="flex space-x-1">
          <Button
            variant={activeFilter === "all" ? "default" : "outline"}
            size="sm"
            onClick={() => setActiveFilter("all")}
            className={`flex items-center ${
              activeFilter === "all" ? "bg-blue-500 text-white" : ""
            }`}
          >
            <Bell className="h-3.5 w-3.5 mr-1.5" />
            <span>All</span>
          </Button>
          <Button
            variant={activeFilter === "system" ? "default" : "outline"}
            size="sm"
            onClick={() => setActiveFilter("system")}
            className={`flex items-center ${
              activeFilter === "system" ? "bg-blue-500 text-white" : ""
            }`}
          >
            <Settings className="h-3.5 w-3.5 mr-1.5" />
            <span>System</span>
          </Button>
          <Button
            variant={activeFilter === "custom" ? "default" : "outline"}
            size="sm"
            onClick={() => setActiveFilter("custom")}
            className={`flex items-center ${
              activeFilter === "custom" ? "bg-blue-500 text-white" : ""
            }`}
          >
            <MessageSquare className="h-3.5 w-3.5 mr-1.5" />
            <span>Chat</span>
          </Button>
        </div>
      </div>

      {/* Alert List Section */}
      <Card className="shadow-sm">
        <CardContent className="p-3">
          {/* Content padding for the list card */}
          <AlertList
            onSelectAlert={handleSelectAlert}
            activeFilter={activeFilter}
          />
        </CardContent>
      </Card>
    </div>
  );
}
