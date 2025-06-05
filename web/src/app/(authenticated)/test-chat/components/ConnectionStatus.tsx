import React from "react";
import { Wifi, WifiOff, RefreshCw } from "lucide-react";

interface ConnectionStatusProps {
  isConnected: boolean;
  showReconnectButton?: boolean;
  onReconnect?: () => void;
}

export function ConnectionStatus({
  isConnected,
  showReconnectButton = false,
  onReconnect,
}: ConnectionStatusProps) {
  if (isConnected) {
    return null; // Don't show anything when connected
  }

  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <WifiOff className="h-4 w-4 text-red-600 mr-2" />
          <div>
            <span className="text-red-800 text-sm font-medium">
              Mất kết nối với máy chủ
            </span>
            <div className="text-red-700 text-xs mt-1">
              Đang cố gắng kết nối lại...
            </div>
          </div>
        </div>
        {showReconnectButton && onReconnect && (
          <button
            onClick={onReconnect}
            className="flex items-center px-3 py-1 text-xs bg-red-100 hover:bg-red-200 text-red-800 rounded-md transition-colors"
          >
            <RefreshCw className="h-3 w-3 mr-1" />
            Làm mới
          </button>
        )}
      </div>
    </div>
  );
}

export function ReconnectingStatus({
  onReconnect,
}: {
  onReconnect?: () => void;
}) {
  return (
    <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mb-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-amber-600 mr-2"></div>
          <div>
            <span className="text-amber-800 text-sm font-medium">
              Đang kết nối lại với máy chủ...
            </span>
            <div className="text-amber-700 text-xs mt-1">
              Vui lòng đợi trong giây lát. Nếu vấn đề vẫn tiếp tục, hãy làm mới
              trang.
            </div>
          </div>
        </div>
        {onReconnect && (
          <button
            onClick={onReconnect}
            className="flex items-center px-3 py-1 text-xs bg-amber-100 hover:bg-amber-200 text-amber-800 rounded-md transition-colors"
          >
            <RefreshCw className="h-3 w-3 mr-1" />
            Làm mới
          </button>
        )}
      </div>
    </div>
  );
}

export function ConnectedStatus() {
  return (
    <div className="bg-green-50 border border-green-200 rounded-lg p-3 mb-4">
      <div className="flex items-center">
        <Wifi className="h-4 w-4 text-green-600 mr-2" />
        <span className="text-green-800 text-sm font-medium">
          ✅ Kết nối đã được khôi phục
        </span>
      </div>
    </div>
  );
}
