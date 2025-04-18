"use client";
import { useApp } from "@/context/app-context";

import { Sidebar } from "./components/Sidebar";
import { OverviewTab } from "./components/OverviewTab";
import { ScriptsTab } from "./components/scripts/ScriptsTab";
import { SpreadsheetsTab } from "./components/spreadsheets/SpreadsheetsTab";
import { useEffect, useState } from "react";

export default function SettingsInterface() {
  const [activeSidebar, setActiveSidebar] = useState("overview");
  const { setActiveNavTab } = useApp();
  useEffect(() => {
    setActiveNavTab("settings");
  }, [setActiveNavTab]);

  return (
    <div className="bg-background flex flex-1 overflow-hidden">
      <Sidebar
        activeSidebar={activeSidebar}
        setActiveSidebar={setActiveSidebar}
      />

      <div className="flex-1 overflow-auto">
        <div className="p-6">
          {activeSidebar === "overview" && <OverviewTab />}
          {activeSidebar === "scripts" && <ScriptsTab />}
          {activeSidebar === "spreadsheets" && <SpreadsheetsTab />}
        </div>
      </div>
    </div>
  );
}
