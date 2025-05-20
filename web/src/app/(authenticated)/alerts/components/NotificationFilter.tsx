"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { Notification } from "@/types";
import { notificationService } from "@/services/api/notification.service";
import { Button } from "@/components/ui/button";
import { ChevronDown, Check } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface NotificationFilterProps {
  onNotificationChange: (notificationId: string) => void;
  selectedNotificationId: string;
  // Add a new prop to control the tabs displayed
  allowedNotificationTypes?: string[];
}

export default function NotificationFilter({
  onNotificationChange,
  selectedNotificationId,
  allowedNotificationTypes = ["all", "System", "Chat"], // Default to new requirement
}: NotificationFilterProps) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [page, setPage] = useState(1);
  const [limit] = useState(20);
  const [hasMore, setHasMore] = useState(true);
  const [loading, setLoading] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const selectedNotification = notifications.find(
    (notif) => notif.id === selectedNotificationId
  );
  const fetchNotifications = useCallback(async () => {
    if (loading) return;

    setLoading(true);
    try {
      const response = await notificationService.getPaginationNotification(
        page,
        limit,
        "published" // Assuming 'published' status is desired for all types
      );

      // Filter out duplicates when adding new notifications
      setNotifications((prev) => {
        const existingIds = new Set(prev.map((n) => n.id));
        // Filter by allowedNotificationTypes if provided
        const filteredData = allowedNotificationTypes
          ? response.data.filter(
              (notification) =>
                allowedNotificationTypes.includes("all") || // Always include "all"
                allowedNotificationTypes.includes(notification.label)
            )
          : response.data;
        const newNotifications = filteredData.filter(
          (n) => !existingIds.has(n.id)
        );
        return [...prev, ...newNotifications];
      });

      setHasMore(response.has_next);

      if (response.has_next) {
        setPage((prevPage) => prevPage + 1);
      }
    } catch {
    } finally {
      setLoading(false);
    }
  }, [loading, page, limit, allowedNotificationTypes]); // Add dependencies

  // Using useRef to track if the component has been mounted to prevent double fetching
  const isMounted = useRef(false);

  useEffect(() => {
    if (!isMounted.current) {
      isMounted.current = true;
      if (notifications.length === 0) {
        // Add notifications.length to dependency array
        fetchNotifications();
      }
    }
  }, [fetchNotifications, notifications.length]);

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const { scrollTop, scrollHeight, clientHeight } = e.currentTarget;

    if (scrollHeight - scrollTop - clientHeight < 50 && hasMore && !loading) {
      fetchNotifications();
    }
  };

  return (
    <div className="flex items-center space-x-2">
      {/* Remove the "Lọc theo thông báo:" label for a cleaner look like the image */}
      {/* <span className="text-sm font-medium text-gray-600">
        Lọc theo thông báo:
      </span> */}

      <DropdownMenu open={dropdownOpen} onOpenChange={setDropdownOpen}>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" className="w-[200px] justify-between">
            {selectedNotificationId !== "all" ? (
              <div className="flex items-center">
                <div
                  className="w-2 h-2 rounded-full mr-2"
                  style={{
                    backgroundColor: selectedNotification?.color || "#6366F1",
                  }}
                />
                <span className="truncate">
                  {selectedNotification?.label || "Tất cả"}
                </span>
              </div>
            ) : (
              "Tất cả"
            )}
            <ChevronDown className="h-4 w-4 ml-2" />
          </Button>
        </DropdownMenuTrigger>

        <DropdownMenuContent
          className="w-[300px] max-h-[300px] overflow-y-auto"
          onScroll={handleScroll}
        >
          <DropdownMenuItem
            className="flex items-center justify-between"
            onClick={() => {
              onNotificationChange("all");
              setDropdownOpen(false);
            }}
          >
            <span>Tất cả</span>
            {selectedNotificationId === "all" && <Check className="h-4 w-4" />}
          </DropdownMenuItem>
          {notifications
            .filter(
              (notification) =>
                allowedNotificationTypes.includes(notification.label) ||
                allowedNotificationTypes.includes("all")
            )
            .map((notification) => (
              <DropdownMenuItem
                key={`notification-${notification.id}`}
                className="flex items-center justify-between"
                onClick={() => {
                  onNotificationChange(notification.id);
                  setDropdownOpen(false);
                }}
              >
                <div className="flex items-center">
                  <div
                    className="w-2 h-2 rounded-full mr-2"
                    style={{ backgroundColor: notification.color || "#6366F1" }}
                  />
                  <span className="truncate">{notification.label}</span>
                </div>
                {selectedNotificationId === notification.id && (
                  <Check className="h-4 w-4" />
                )}
              </DropdownMenuItem>
            ))}
          {loading && (
            <div className="flex justify-center py-2">
              <div className="w-4 h-4 border-2 border-t-indigo-500 border-l-indigo-500 rounded-full animate-spin"></div>
            </div>
          )}
          <div ref={bottomRef} />
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}
