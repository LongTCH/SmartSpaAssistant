"use client";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import Image from "next/image";

interface GuestInfoHeaderProps {
  avatarUrl: string | null | undefined;
  accountName: string | null | undefined;
}

export function GuestInfoHeader({
  avatarUrl,
  accountName,
}: GuestInfoHeaderProps) {
  return (
    <div className="flex flex-col items-center pt-8 pb-6 bg-white">
      <div className="relative">
        <Avatar className="h-24 w-24 border-2 border-[#6366F1]">
          {avatarUrl ? (
            <Image
              src={avatarUrl}
              alt="User avatar"
              width={96}
              height={96}
              className="object-cover h-full w-full"
            />
          ) : (
            <AvatarFallback className="text-4xl">
              {accountName?.charAt(0).toUpperCase() || "?"}
            </AvatarFallback>
          )}
        </Avatar>
        <div className="absolute bottom-0 right-0 h-5 w-5 rounded-full bg-[#0084FF] border-2 border-white"></div>
      </div>
      <h2 className="text-2xl font-bold mt-4">{accountName || "Khách hàng"}</h2>
    </div>
  );
}
