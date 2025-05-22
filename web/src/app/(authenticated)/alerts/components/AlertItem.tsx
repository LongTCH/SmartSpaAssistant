"use client";

import { Alert } from "@/types";
import { formatDistanceToNow } from "date-fns";
import { vi } from "date-fns/locale";

interface AlertItemProps {
  alert: Alert;
  onClick: () => void;
}

// Helper function to determine if a hex color is light or dark
// Returns true if light, false if dark
function isColorLight(hexColor: string): boolean {
  // Remove # if present
  const hex = hexColor.replace("#", "");
  // Convert hex to RGB
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);
  // Calculate HSP (Highly Sensitive Poo) brightness
  // HSP < 127.5 is dark, >= 127.5 is light
  // Using a common brightness formula: (0.299*R + 0.587*G + 0.114*B)
  // Threshold can be adjusted, 128 or 149 are common. Let's use 149 for better bias towards black text on mid-tones.
  const brightness = Math.sqrt(
    0.299 * (r * r) + 0.587 * (g * g) + 0.114 * (b * b)
  );
  return brightness > 149; // Adjust threshold if needed
}

export default function AlertItem({ alert, onClick }: AlertItemProps) {
  const formattedDate = formatDistanceToNow(new Date(alert.created_at), {
    addSuffix: true,
    locale: vi,
  });

  const isSystemAlert = alert.type === "system";
  const isUnread = alert.status === "unread";

  const notificationLabelText = isSystemAlert
    ? "Thông báo hệ thống"
    : alert.notification?.label || "Thông báo";

  const isCustomTypeWithColor =
    alert.type === "custom" && alert.notification?.color;

  let textColorForBadge = "#FFFFFF"; // Default to white
  if (isCustomTypeWithColor && alert.notification!.color) {
    textColorForBadge = isColorLight(alert.notification!.color)
      ? "#000000" // Black text for light backgrounds
      : "#FFFFFF"; // White text for dark backgrounds
  }

  return (
    <div
      className={`p-3 border rounded-lg hover:bg-gray-100 cursor-pointer transition-colors ${
        isUnread ? "bg-white" : "bg-gray-50"
      } border-gray-200`}
      onClick={onClick}
    >
      <div className="flex items-start">
        <div className="flex-1">
          <div className="flex justify-between items-start">
            {isCustomTypeWithColor ? (
              <span
                className="px-1.5 py-0.5 text-[11px] font-semibold rounded-md" // Removed text-white
                style={{
                  backgroundColor: alert.notification!.color,
                  color: textColorForBadge, // Apply dynamic text color
                  display: "inline-block",
                }}
              >
                {notificationLabelText}
              </span>
            ) : (
              <h3
                className={`text-sm ${
                  isUnread
                    ? "font-semibold text-gray-900"
                    : "font-medium text-gray-700"
                }`}
              >
                {notificationLabelText}
              </h3>
            )}
            <span
              className={`text-xs flex items-center ${
                isUnread ? "text-gray-600" : "text-gray-400"
              }`}
            >
              {formattedDate}
              {isUnread && (
                <span className="w-1.5 h-1.5 bg-blue-600 rounded-full ml-2 flex-shrink-0"></span>
              )}
            </span>
          </div>
          <p
            className={`text-xs mt-0.5 whitespace-pre-wrap ${
              isUnread ? "text-gray-700" : "text-gray-500"
            }`}
          >
            {alert.content}
          </p>
        </div>
      </div>
    </div>
  );
}
