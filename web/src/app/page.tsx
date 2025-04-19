"use client";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to the authenticated conversations page
    router.push("/conversations");
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-r from-blue-100 to-purple-100">
      <div className="flex flex-col items-center p-6 rounded-lg shadow-lg bg-white/80 backdrop-blur-sm">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent"></div>
        <p className="text-gray-600 mt-4">Đang tải...</p>
      </div>
    </div>
  );
}
