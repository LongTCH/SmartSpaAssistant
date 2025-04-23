"use client";

import { useEffect, useState } from "react";

export function LoadingScreen() {
  // Chỉ hiển thị loading screen nếu quá trình tải kéo dài
  // Tránh flash của màn hình loading khi trang tải nhanh
  const [showLoading, setShowLoading] = useState(false);

  useEffect(() => {
    // Đợi 300ms trước khi hiển thị loading
    const timer = setTimeout(() => {
      setShowLoading(true);
    }, 300);

    return () => clearTimeout(timer);
  }, []);

  if (!showLoading) {
    return null;
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-r from-blue-100 to-purple-100">
      <div className="flex flex-col items-center p-6 rounded-lg shadow-lg bg-white/80 backdrop-blur-sm">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent"></div>
        <p className="text-gray-600 mt-4">Đang tải...</p>
      </div>
    </div>
  );
}
