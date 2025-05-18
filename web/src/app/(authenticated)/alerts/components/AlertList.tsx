"use client";

import { Alert } from "@/types";
import { useEffect, useRef, useState } from "react";
import { useInView } from "react-intersection-observer";
import { alertService } from "@/services/api/alert.service";
import AlertItem from "./AlertItem";
import NotificationFilter from "./NotificationFilter";

interface AlertListProps {
  onSelectAlert: (alert: Alert) => void;
}

export default function AlertList({ onSelectAlert }: AlertListProps) {
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
  const fetchAlerts = async (reset = false) => {
    if (loading) return;

    setLoading(true);
    try {
      const currentSkip = reset ? 0 : skip;
      const response = await alertService.getPagingAlert(
        currentSkip,
        limit,
        selectedNotificationId
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
    } catch (error) {
      console.error("Failed to fetch alerts:", error);
    } finally {
      setLoading(false);
    }
  }; // Track previous notification ID to prevent redundant API calls
  const prevNotificationIdRef = useRef<string>(selectedNotificationId);
  const initialFetchRef = useRef<boolean>(false);

  useEffect(() => {
    if (!initialFetchRef.current) {
      // Initial fetch
      initialFetchRef.current = true;
      fetchAlerts(true);
    } else if (prevNotificationIdRef.current !== selectedNotificationId) {
      // Fetch only when notification ID changes
      prevNotificationIdRef.current = selectedNotificationId;
      fetchAlerts(true);
    }
  }, [selectedNotificationId]);

  useEffect(() => {
    if (inView && hasMore && !loading) {
      fetchAlerts();
    }
  }, [inView, hasMore, loading]);
  const handleNotificationChange = (notificationId: string) => {
    setSelectedNotificationId(notificationId);
    setSkip(0);
  };

  if (alerts.length === 0 && !loading) {
    return (
      <div className="flex flex-col space-y-4">
        <NotificationFilter
          onNotificationChange={handleNotificationChange}
          selectedNotificationId={selectedNotificationId}
        />
        <div className="flex flex-col items-center justify-center h-64 text-gray-500">
          <p>Không có thông báo nào</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col space-y-4">
      <NotificationFilter
        onNotificationChange={handleNotificationChange}
        selectedNotificationId={selectedNotificationId}
      />

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
