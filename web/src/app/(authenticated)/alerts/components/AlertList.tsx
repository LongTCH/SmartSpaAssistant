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
  // Use refs to prevent unnecessary re-renders and API calls
  const loadingRef = useRef(loading);
  const skipRef = useRef(skip);
  const activeFilterRef = useRef(activeFilter);
  const selectedNotificationIdRef = useRef(selectedNotificationId);
  const isFirstRender = useRef(true);
  const performFetchRef = useRef<any>(null);
  const prevActiveFilterForEffect = useRef(activeFilter);
  const prevSelectedNotificationIdForEffect = useRef(selectedNotificationId);

  // Update refs when values change
  useEffect(() => {
    loadingRef.current = loading;
  }, [loading]);

  useEffect(() => {
    skipRef.current = skip;
  }, [skip]);

  useEffect(() => {
    activeFilterRef.current = activeFilter;
  }, [activeFilter]);

  useEffect(() => {
    selectedNotificationIdRef.current = selectedNotificationId;
  }, [selectedNotificationId]);
  const performFetch = useCallback(
    async (fetchSkip: number, isReset: boolean) => {
      // Prevent multiple simultaneous calls
      if (loadingRef.current) {
        return;
      }

      setLoading(true);

      try {
        const apiType = activeFilterRef.current; // "all", "system", or "custom"
        const apiNotificationId =
          activeFilterRef.current === "custom"
            ? selectedNotificationIdRef.current
            : "all";

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
          if (isReset) {
            setSkip(0);
          }
        }
      } catch {
        setHasMore(false);
        if (isReset) {
          setAlerts([]);
          setSkip(0);
        }
      } finally {
        setLoading(false);
      }
    },
    [limit]
  );

  // Store function in ref to avoid dependency issues
  performFetchRef.current = performFetch;

  // Initial load and filter change effect
  useEffect(() => {
    if (isFirstRender.current) {
      performFetchRef.current?.(0, true);
      isFirstRender.current = false;
      prevActiveFilterForEffect.current = activeFilter;
      prevSelectedNotificationIdForEffect.current = selectedNotificationId;
      return; // Crucial for preventing fall-through on initial render
    }

    // This block runs for subsequent effect executions
    if (
      activeFilter !== prevActiveFilterForEffect.current ||
      selectedNotificationId !== prevSelectedNotificationIdForEffect.current
    ) {
      performFetchRef.current?.(0, true);
      prevActiveFilterForEffect.current = activeFilter;
      prevSelectedNotificationIdForEffect.current = selectedNotificationId;
    }
  }, [activeFilter, selectedNotificationId]);

  // Infinite scrolling effect
  useEffect(() => {
    if (inView && hasMore && !loading && skip > 0) {
      performFetchRef.current?.(skip, false);
    }
  }, [inView, hasMore, loading, skip]); // Track when new alerts are added via WebSocket
  const [hasNewWebSocketAlert, setHasNewWebSocketAlert] = useState(false);

  // WebSocket message handler for new alerts
  useEffect(() => {
    const unregister = registerMessageHandler(
      WS_MESSAGES.ALERT,
      (data: any) => {
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
      } catch {
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
