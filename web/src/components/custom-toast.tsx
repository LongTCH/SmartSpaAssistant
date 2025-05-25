"use client";

import { useState, useEffect, useCallback } from "react";
import { X } from "lucide-react";
import { Button } from "@/components/ui/button";

interface CustomToastProps {
  id: string;
  label: string;
  content: string;
  color?: string;
  duration?: number;
  onDismiss: (id: string) => void;
  onClick?: () => void;
}

export function CustomToast({
  id,
  label,
  content,
  color,
  duration = 15000,
  onDismiss,
  onClick,
}: CustomToastProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [isLeaving, setIsLeaving] = useState(false);
  useEffect(() => {
    // Trigger animation after component mounts
    const timer = setTimeout(() => setIsVisible(true), 100);
    return () => clearTimeout(timer);
  }, []);

  const handleDismiss = useCallback(() => {
    setIsLeaving(true);
    setTimeout(() => {
      onDismiss(id);
    }, 300); // Match animation duration
  }, [id, onDismiss]);

  const handleClick = () => {
    if (onClick) {
      onClick();
      handleDismiss();
    }
  };
  useEffect(() => {
    // Auto dismiss after duration
    const timer = setTimeout(() => {
      handleDismiss();
    }, duration);

    return () => clearTimeout(timer);
  }, [duration, handleDismiss]);
  return (
    <div
      className={`
        fixed bottom-4 right-4 z-50 max-w-sm w-full
        transform transition-all duration-300 ease-in-out
        ${
          isVisible && !isLeaving
            ? "translate-x-0 opacity-100"
            : "translate-x-full opacity-0"
        }
      `}
      style={{ marginBottom: `${parseInt(id) * 80}px` }} // Stack multiple toasts
    >
      {" "}
      <div
        className={`
          bg-white shadow-xl rounded-lg border border-gray-200
          ${onClick ? "cursor-pointer hover:shadow-2xl hover:scale-105" : ""}
          transition-all duration-300 ease-in-out
        `}
        onClick={handleClick}
        style={{
          borderLeftWidth: color ? "5px" : "1px",
          borderLeftColor: color || "#3B82F6",
          borderLeftStyle: "solid",
        }}
      >
        <div className="p-4 pr-12">
          <div className="flex flex-col space-y-2">
            <div className="flex items-start">
              <span
                className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium text-white"
                style={{ backgroundColor: color || "#3B82F6" }}
              >
                {label}
              </span>
            </div>
            {content && (
              <div className="text-gray-700 text-sm leading-relaxed">
                {content}
              </div>
            )}
          </div>
        </div>{" "}
        <Button
          variant="ghost"
          size="icon"
          className="absolute top-3 right-3 h-7 w-7 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-full"
          onClick={(e) => {
            e.stopPropagation();
            handleDismiss();
          }}
        >
          <X className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
