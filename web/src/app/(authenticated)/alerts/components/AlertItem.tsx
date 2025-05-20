"use client";

import { Alert } from "@/types";
import { formatDistanceToNow } from "date-fns";
import { vi } from "date-fns/locale";

interface AlertItemProps {
  alert: Alert;
  onClick: () => void;
}

export default function AlertItem({ alert, onClick }: AlertItemProps) {
  const formattedDate = formatDistanceToNow(new Date(alert.created_at), {
    addSuffix: true,
    locale: vi,
  });

  return (
    <div
      className="p-4 border rounded-lg bg-white hover:bg-gray-100 cursor-pointer transition-colors"
      onClick={onClick}
    >
      <div className="flex items-start">
        <div
          className="w-3 h-3 rounded-full mt-1.5 mr-3 flex-shrink-0"
          style={{ backgroundColor: alert.notification.color || "#6366F1" }}
        />

        <div className="flex-1">
          <div className="flex justify-between items-start">
            <h3 className="font-medium text-gray-900">
              {alert.notification.label}
            </h3>
            <span className="text-xs text-gray-500">{formattedDate}</span>
          </div>
          <p className="text-sm text-gray-600 mt-1 whitespace-pre-wrap">
            {alert.content}
          </p>
        </div>
      </div>
    </div>
  );
}
