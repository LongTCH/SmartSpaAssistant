"use client";

import { Alert } from "@/types";
import { useEffect, useRef, useState, useCallback } from "react"; // Import useCallback
import { useInView } from "react-intersection-observer";
import { alertService } from "@/services/api/alert.service";
import AlertItem from "./AlertItem";
import NotificationFilter from "./NotificationFilter";

interface AlertListProps {
  onSelectAlert: (alert: Alert) => void;
  activeFilter: string; // Add activeFilter prop
}

export default function AlertList({
  onSelectAlert,
  activeFilter,
}: AlertListProps) {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(false);
  const [skip, setSkip] = useState(0);
  const [limit] = useState(20);
  const [hasMore, setHasMore] = useState(true);
  const [selectedNotificationId, setSelectedNotificationId] =
    useState<string>("all");
  // Remove activeTab state, as it's now passed as activeFilter prop
  // const [activeTab, setActiveTab] = useState<string>("all");

  const { ref, inView } = useInView({
    threshold: 0.1,
  });
  const fetchAlerts = useCallback(
    async (reset = false) => {
      if (loading) return;

      setLoading(true);
      try {
        const currentSkip = reset ? 0 : skip;
        // Modify getPagingAlert to potentially use activeFilter if your API supports it
        // For now, it still uses selectedNotificationId which is controlled by NotificationFilter
        const response = await alertService.getPagingAlert(
          currentSkip,
          limit,
          // If activeFilter is 'all' or 'system', selectedNotificationId should reflect that,
          // or your API needs to handle 'all' and 'system' directly.
          // For now, we assume selectedNotificationId is correctly set by NotificationFilter or defaults to 'all'.
          activeFilter === "chat" ? selectedNotificationId : activeFilter
        );

        if (reset) {
          setAlerts(response.data);
        } else {
          setAlerts((prev) => [...prev, ...response.data]);
        }

        setHasMore(response.has_next);
        if (response.has_next) {
          setSkip(currentSkip + limit);
        }
      } catch {
      } finally {
        setLoading(false);
      }
    },
    [loading, skip, limit, activeFilter, selectedNotificationId] // Add dependencies to useCallback
  );

  // Track previous notification ID to prevent redundant API calls
  const prevNotificationIdRef = useRef<string>(selectedNotificationId);
  const initialFetchRef = useRef<boolean>(false);

  useEffect(() => {
    if (!initialFetchRef.current) {
      initialFetchRef.current = true;
      fetchAlerts(true);
    } else if (
      prevNotificationIdRef.current !== selectedNotificationId ||
      activeFilter !== prevNotificationIdRef.current
    ) {
      // Also refetch if activeFilter changes
      prevNotificationIdRef.current =
        activeFilter === "chat" ? selectedNotificationId : activeFilter;
      fetchAlerts(true);
    }
  }, [selectedNotificationId, activeFilter, fetchAlerts]); // Add fetchAlerts to dependency array

  useEffect(() => {
    if (inView && hasMore && !loading) {
      fetchAlerts();
    }
  }, [inView, hasMore, loading, fetchAlerts]); // Add fetchAlerts to dependency array
  const handleNotificationChange = (notificationId: string) => {
    setSelectedNotificationId(notificationId);
    setSkip(0);
    // No longer setting activeTab here
  };

  if (alerts.length === 0 && !loading) {
    return (
      <div className="flex flex-col space-y-4">
        {/* Conditionally render NotificationFilter only if activeFilter is "chat" */}
        {activeFilter === "chat" && (
          <NotificationFilter
            onNotificationChange={handleNotificationChange}
            selectedNotificationId={selectedNotificationId}
            // Ensure allowedNotificationTypes is appropriate for the chat filter
            allowedNotificationTypes={["all", "Chat"]}
          />
        )}
        <div className="flex flex-col items-center justify-center h-64 text-gray-500">
          <p>Không có thông báo nào</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col space-y-4">
      {/* Conditionally render NotificationFilter only if activeFilter is "chat" */}
      {activeFilter === "chat" && (
        <NotificationFilter
          onNotificationChange={handleNotificationChange}
          selectedNotificationId={selectedNotificationId}
          allowedNotificationTypes={["all", "Chat"]} // Or just ["Chat"] if "all" within chat is not a concept
        />
      )}
      {/* When activeFilter is "all" or "system", NotificationFilter is not rendered */}

      <div className="space-y-3">
        {alerts.map((alert) => (
          <AlertItem
            key={alert.id}
            alert={alert}
            onClick={() => onSelectAlert(alert)}
          />
        ))}

        {loading && (
          <div className="flex justify-center py-4">
            <div className="w-6 h-6 border-2 border-t-indigo-500 border-l-indigo-500 rounded-full animate-spin"></div>
          </div>
        )}

        {hasMore && !loading && <div ref={ref} className="h-10" />}
      </div>
    </div>
  );
}
