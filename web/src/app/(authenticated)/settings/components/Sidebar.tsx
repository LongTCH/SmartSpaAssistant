"use client";

import { LayoutDashboard, FileText, Table2, Tag } from "lucide-react";

interface SidebarProps {
  activeSidebar: string;
  setActiveSidebar: (sidebar: string) => void;
}

export function Sidebar({ activeSidebar, setActiveSidebar }: SidebarProps) {
  return (
    <div className="w-48 border-r border-[#E5E7EB] flex flex-col bg-[#F9F5FF] h-full overflow-hidden">
      <div className="flex-1 overflow-y-auto">
        <button
          className={`w-full flex items-center space-x-3 px-4 py-3 text-left cursor-pointer ${
            activeSidebar === "overview"
              ? "bg-[#f1e2f9] text-fuchsia-800 border-r-4 border-r-fuchsia-800"
              : "hover:bg-[#EDE9FE] text-[#4B5563]"
          }`}
          onClick={() => setActiveSidebar("overview")}
        >
          <LayoutDashboard className="h-5 w-5" />
          <span>Tổng quan</span>
        </button>
        <button
          className={`w-full flex items-center space-x-3 px-4 py-3 text-left cursor-pointer ${
            activeSidebar === "scripts"
              ? "bg-[#f1e2f9] text-fuchsia-800 border-r-4 border-r-fuchsia-800"
              : "hover:bg-[#EDE9FE] text-[#4B5563]"
          }`}
          onClick={() => setActiveSidebar("scripts")}
        >
          <FileText className="h-5 w-5" />
          <span>Kịch bản</span>
        </button>
        <button
          className={`w-full flex items-center space-x-3 px-4 py-3 text-left cursor-pointer ${
            activeSidebar === "spreadsheets"
              ? "bg-[#f1e2f9] text-fuchsia-800 border-r-4 border-r-fuchsia-800"
              : "hover:bg-[#EDE9FE] text-[#4B5563]"
          }`}
          onClick={() => setActiveSidebar("spreadsheets")}
        >
          <Table2 className="h-5 w-5" />
          <span>Bảng tính</span>
        </button>
        <button
          className={`w-full flex items-center space-x-3 px-4 py-3 text-left cursor-pointer ${
            activeSidebar === "interests"
              ? "bg-[#f1e2f9] text-fuchsia-800 border-r-4 border-r-fuchsia-800"
              : "hover:bg-[#EDE9FE] text-[#4B5563]"
          }`}
          onClick={() => setActiveSidebar("interests")}
        >
          <Tag className="h-5 w-5" />
          <span>Nhãn</span>
        </button>
      </div>
    </div>
  );
}
