import { Menu } from "lucide-react";

interface ChatHeaderProps {
  title: string;
  toggleMobileSidebar: () => void;
  isMobile: boolean;
}

export function ChatHeader({
  title,
  toggleMobileSidebar,
  isMobile,
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
        <div className="hidden sm:flex items-center text-xs text-gray-500 bg-gray-50 py-1 px-2.5 rounded-full">
          <span className="w-1.5 h-1.5 bg-green-500 rounded-full mr-1.5"></span>
          Online
        </div>
      </div>
    </div>
  );
}
