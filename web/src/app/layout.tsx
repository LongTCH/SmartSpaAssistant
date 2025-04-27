import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AppProvider } from "@/context/app-context";
import { Toaster } from "sonner";

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
      ><TooltipProvider>
        <AppProvider>
          <LayoutContainer>{children}</LayoutContainer>
          <Toaster position="top-right" richColors />
        </AppProvider>
        </TooltipProvider>
      </body>
    </html>
  );
}
