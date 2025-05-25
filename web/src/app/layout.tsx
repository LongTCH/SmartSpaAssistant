import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AppProvider } from "@/context/app-context";
import { ToastProvider } from "@/context/toast-provider";
import { WebSocketHandler } from "@/context/websocket-handler";

import LayoutContainer from "@/app/layout-container";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Smart Spa Assistant",
  description: "Dashboard",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <TooltipProvider>
          <ToastProvider>
            <AppProvider>
              <WebSocketHandler />
              <LayoutContainer>{children}</LayoutContainer>
            </AppProvider>
          </ToastProvider>
        </TooltipProvider>
      </body>
    </html>
  );
}
