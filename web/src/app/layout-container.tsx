"use client";
import { useLayoutEffect, useRef } from "react";
import { useApp } from "@/context/app-context";
import { Navbar } from "@/components/navbar";

export default function LayoutContainer({
  children,
}: {
  children: React.ReactNode;
}) {
  const navbarRef = useRef<HTMLDivElement>(null);
  const { setContentHeight } = useApp();

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
  }, []);

  return (
    <div className="flex flex-col h-screen">
      <div className="sticky top-0 z-50" ref={navbarRef}>
        <Navbar />
      </div>
      <div className="flex-1 overflow-auto">{children}</div>
    </div>
  );
}
