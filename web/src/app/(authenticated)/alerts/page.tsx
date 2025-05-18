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

export default function AlertsPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const { setPageLoading, setActiveNavTab } = useApp();

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
          <CardTitle>Quản lý thông báo</CardTitle>
          <CardDescription>
            Xem danh sách các thông báo từ khách hàng và hệ thống
          </CardDescription>
        </CardHeader>
        <CardContent>
          <AlertList onSelectAlert={handleSelectAlert} />
        </CardContent>
      </Card>
    </div>
  );
}
