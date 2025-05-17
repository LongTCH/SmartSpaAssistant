"use client";

import { Sidebar } from "./components/Sidebar";
import { OverviewTab } from "./components/OverviewTab";
import { ScriptsTab } from "./components/scripts/ScriptsTab";
import { SpreadsheetsTab } from "./components/spreadsheets/SpreadsheetsTab";
import { InterestsTab } from "./components/interests/InterestsTab";
import { NotificationsTab } from "./components/notifications/NotificationsTab";
import { useState, Suspense } from "react";
import { LoadingScreen } from "@/components/loading-screen";

export default function SettingsInterface() {
  const [activeSidebar, setActiveSidebar] = useState("overview");

  return (
    <Suspense fallback={<LoadingScreen />}>
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
            {activeSidebar === "interests" && <InterestsTab />}
            {activeSidebar === "notifications" && <NotificationsTab />}
          </div>
        </div>
      </div>
    </Suspense>
  );
}
