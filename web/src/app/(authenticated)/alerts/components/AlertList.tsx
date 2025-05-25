"use client";

import { Alert } from "@/types";
import { useEffect, useState, useCallback, useRef } from "react"; // useRef added
import { useInView } from "react-intersection-observer";
import { alertService } from "@/services/api/alert.service";
import AlertItem from "./AlertItem";
import NotificationFilter from "./NotificationFilter";
import { useApp } from "@/context/app-context";
import { WS_MESSAGES } from "@/lib/constants";

interface AlertListProps {
  onSelectAlert: (alert: Alert) => void;
  activeFilter: string;
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

  const { ref, inView } = useInView({
    threshold: 0.1,
  });
  // Get WebSocket context
  const { registerMessageHandler, setHasNewAlerts } = useApp();

  // loadingRef to prevent calling performFetch if already loading, without adding loading to useCallback deps
  const loadingRef = useRef(loading);
  useEffect(() => {
    loadingRef.current = loading;
  }, [loading]);

  const performFetch = useCallback(
    async (fetchSkip: number, isReset: boolean) => {
      if (loadingRef.current && !isReset) {
        // Allow reset calls to interrupt, or use a more sophisticated queue/cancel
        // For simplicity, if loading and not a reset, just return.
        // A reset implies filter change, which should take precedence.
        // If it's a reset, we might want to cancel ongoing non-reset fetches.
        // For now, let's ensure loading state is respected.
        if (!isReset && fetchSkip > 0) return; // Don't interrupt for load more if already loading
      }
      setLoading(true);
      try {
        const apiType = activeFilter; // "all", "system", or "custom"
        // For "system" or "all" types, notification_id is "all".
        // For "custom" type, it's the selectedNotificationId (which can also be "all").
        const apiNotificationId =
          activeFilter === "custom" ? selectedNotificationId : "all";

        const response = await alertService.getPagingAlert(
          fetchSkip,
          limit,
          apiType,
          apiNotificationId
        );

        if (isReset) {
          setAlerts(response.data);
        } else {
          setAlerts((prev) => [...prev, ...response.data]);
        }

        setHasMore(response.has_next);
        if (response.has_next) {
          setSkip(fetchSkip + response.data.length);
        } else {
          // If no more data
          if (isReset) {
            setSkip(0); // Reset skip to 0 if it was a reset operation
          }
          // If it was a load more (isReset=false) and no more data,
          // skip is already fetchSkip + response.data.length (which is fetchSkip if data is empty)
          // and hasMore is false, so no further action on skip needed.
        }
      } catch (error) {
        console.error("Failed to fetch alerts:", error);
        setHasMore(false); // Stop trying to load more on error
        if (isReset) {
          setAlerts([]); // Clear alerts on error if it was a reset
          setSkip(0);
        }
      } finally {
        setLoading(false);
      }
    },
    [
      activeFilter,
      selectedNotificationId,
      limit,
      // setLoading, // Removed as per your manual edit, assuming loadingRef handles it
      // setAlerts, // Removed
      // setHasMore, // Removed
      // setSkip, // Removed
      // Ensure all dependencies used inside performFetch are listed if they can change and should trigger re-creation of performFetch
      // For example, if 'limit' could change, it should be here.
      // The state setters (setAlerts, setHasMore, setSkip, setLoading) are generally stable and don't need to be deps
      // but if you are directly using their state values (e.g. `skip` instead of `fetchSkip`) then those values should be deps.
      // Based on your provided snippet, activeFilter, selectedNotificationId, limit are direct deps.
    ]
  );

  // Effect for initial load and filter changes (always resets)
  useEffect(() => {
    performFetch(0, true); // Always fetch from skip 0 and reset
  }, [activeFilter, selectedNotificationId, performFetch]);
  // Effect for infinite scrolling (load more)
  useEffect(() => {
    if (inView && hasMore && !loading) {
      performFetch(skip, false); // Fetch from current `skip` and append
    }
  }, [inView, hasMore, loading, skip, performFetch]); // Track when new alerts are added via WebSocket
  const [hasNewWebSocketAlert, setHasNewWebSocketAlert] = useState(false);

  // WebSocket message handler for new alerts
  useEffect(() => {
    const unregister = registerMessageHandler(
      WS_MESSAGES.ALERT,
      (data: any) => {
        console.log("Received ALERT WebSocket message:", data);

        // Ensure data is a valid Alert object
        if (data && typeof data === "object" && data.id && data.content) {
          const newAlert = data as Alert;

          // Add the new alert to the beginning of the list (most recent first)
          setAlerts((prevAlerts) => {
            // Check if alert already exists to prevent duplicates
            const exists = prevAlerts.some((alert) => alert.id === newAlert.id);
            if (exists) {
              return prevAlerts;
            }

            // Add new alert to the beginning of the list
            return [newAlert, ...prevAlerts];
          });

          // Set flag to trigger notification in the next effect
          setHasNewWebSocketAlert(true);
        } else {
          console.error("Received invalid alert data:", data);
        }
      }
    );

    // Cleanup when component unmounts
    return () => {
      unregister();
    };
  }, [registerMessageHandler]);

  // Effect to handle notification when new WebSocket alert is added
  useEffect(() => {
    if (hasNewWebSocketAlert) {
      setHasNewAlerts(true);
      setHasNewWebSocketAlert(false); // Reset the flag
    }
  }, [hasNewWebSocketAlert, setHasNewAlerts]);

  const handleAlertItemClick = async (alert: Alert) => {
    if (alert.status === "unread") {
      try {
        const updatedAlert = await alertService.markAsRead(alert.id);
        setAlerts((prevAlerts) =>
          prevAlerts.map((a) =>
            a.id === updatedAlert.id ? { ...a, status: "read" } : a
          )
        );
        // Proceed with original navigation/selection logic
        onSelectAlert(updatedAlert); // Pass the updated alert
      } catch (error) {
        console.error("Failed to mark alert as read:", error);
        // Optionally, still proceed with navigation even if marking as read fails
        onSelectAlert(alert);
      }
    } else {
      // If already read, just proceed with original navigation/selection logic
      onSelectAlert(alert);
    }
  };

  const handleNotificationChange = (notificationId: string) => {
    setSelectedNotificationId(notificationId);
    // setSkip(0); // Not strictly needed as performFetch(0, true) will be called by the effect above
  };

  if (alerts.length === 0 && !loading) {
    return (
      <div className="flex flex-col space-y-4">
        {activeFilter === "custom" && ( // Changed "chat" to "custom"
          <NotificationFilter
            onNotificationChange={handleNotificationChange}
            selectedNotificationId={selectedNotificationId}
            allowedNotificationTypes={["all", "Chat"]} // "Chat" is likely a label for custom type
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
      {activeFilter === "custom" && ( // Changed "chat" to "custom"
        <NotificationFilter
          onNotificationChange={handleNotificationChange}
          selectedNotificationId={selectedNotificationId}
          allowedNotificationTypes={["all", "Chat"]}
        />
      )}

      <div className="space-y-3">
        {alerts.map((alert) => (
          <AlertItem
            key={alert.id}
            alert={alert}
            onClick={() => handleAlertItemClick(alert)} // Updated onClick handler
          />
        ))}

        {loading && (
          <div className="flex justify-center py-4">
            <div className="w-6 h-6 border-2 border-t-indigo-500 border-l-indigo-500 rounded-full animate-spin"></div>
          </div>
        )}

        {hasMore && !loading && alerts.length > 0 && (
          <div ref={ref} className="h-10" />
        )}
      </div>
    </div>
  );
}
