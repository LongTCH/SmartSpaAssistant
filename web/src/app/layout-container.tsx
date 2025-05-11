"use client";
import { useLayoutEffect, useRef, useEffect } from "react";
import { useApp } from "@/context/app-context";
import { Navbar } from "@/components/navbar";
import { LoadingScreen } from "@/components/loading-screen";
import { usePathname } from "next/navigation";

export default function LayoutContainer({
  children,
}: {
  children: React.ReactNode;
}) {
  const navbarRef = useRef<HTMLDivElement>(null);
  const { contentHeight, setContentHeight, isPageLoading, setPageLoading } =
    useApp();
  const pathname = usePathname();

  // Khi pathname thay đổi, tắt trạng thái loading
  useEffect(() => {
    // Đặt timeout nhỏ để đảm bảo UI đã render
    const timeoutId = setTimeout(() => {
      setPageLoading(false);
    }, 100);

    return () => clearTimeout(timeoutId);
  }, [pathname, setPageLoading]);

  useLayoutEffect(() => {
    const updateHeight = () => {
      const navbarHeight = navbarRef.current?.offsetHeight || 0;
      setContentHeight(`calc(100vh - ${navbarHeight}px)`);
    };

    updateHeight();
    window.addEventListener("resize", updateHeight);

    return () => {
      window.removeEventListener("resize", updateHeight);
    };
  }, [setContentHeight]);

  return (
    <div className="flex flex-col h-screen">
      <div className="sticky top-0 z-50" ref={navbarRef}>
        <Navbar />
      </div>
      <div className="flex-1 overflow-auto">
        <div className="flex flex-col" style={{ height: contentHeight }}>
          {isPageLoading ? <LoadingScreen /> : children}
        </div>
      </div>
    </div>
  );
}
