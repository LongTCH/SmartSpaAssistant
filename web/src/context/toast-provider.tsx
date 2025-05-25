"use client";

import { createContext, useContext, useState, ReactNode } from "react";
import { CustomToast } from "@/components/custom-toast";

interface Toast {
  id: string;
  label: string;
  content: string;
  color?: string;
  duration?: number;
  onClick?: () => void;
}

interface ToastContextType {
  showToast: (toast: Omit<Toast, "id">) => void;
  dismissToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const showToast = (toast: Omit<Toast, "id">) => {
    const id = Date.now().toString();
    const newToast: Toast = { ...toast, id };

    setToasts((prev) => [...prev, newToast]);
  };

  const dismissToast = (id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  };

  return (
    <ToastContext.Provider value={{ showToast, dismissToast }}>
      {children}

      {/* Render toasts */}
      {toasts.map((toast, index) => (
        <CustomToast
          key={toast.id}
          id={index.toString()} // Use index for positioning
          label={toast.label}
          content={toast.content}
          color={toast.color}
          duration={toast.duration}
          onClick={toast.onClick}
          onDismiss={() => dismissToast(toast.id)}
        />
      ))}
    </ToastContext.Provider>
  );
}

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within ToastProvider");
  }
  return context;
};
