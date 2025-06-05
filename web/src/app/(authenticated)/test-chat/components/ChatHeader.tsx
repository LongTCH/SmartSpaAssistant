import { Menu, Wifi, WifiOff } from "lucide-react";

interface ChatHeaderProps {
  title: string;
  toggleMobileSidebar: () => void;
  isMobile: boolean;
  isWebSocketConnected?: boolean;
}

export function ChatHeader({
  title,
  toggleMobileSidebar,
  isMobile,
  isWebSocketConnected = false,
}: ChatHeaderProps) {
  return (
    <div className="py-2 px-4 sm:px-6 border-b flex items-center justify-between bg-white z-10 relative">
      <div className="flex items-center">
        {isMobile && (
          <button
            onClick={toggleMobileSidebar}
            className="p-1.5 rounded-md hover:bg-gray-100 mr-2"
          >
            <Menu size={18} />
          </button>
        )}
        <h2 className="text-lg font-medium text-gray-800">{title}</h2>
      </div>
      <div className="flex items-center space-x-2">
        <div
          className={`flex items-center text-xs py-1 px-2.5 rounded-full ${
            isWebSocketConnected
              ? "text-green-700 bg-green-50"
              : "text-red-700 bg-red-50"
          }`}
        >
          {isWebSocketConnected ? (
            <>
              <Wifi size={12} className="mr-1.5" />
              <span className="hidden sm:inline">Đã kết nối</span>
              <span className="sm:hidden">Online</span>
            </>
          ) : (
            <>
              <WifiOff size={12} className="mr-1.5" />
              <span className="hidden sm:inline">Mất kết nối</span>
              <span className="sm:hidden">Offline</span>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
