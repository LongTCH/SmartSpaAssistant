"use client";

import Link from "next/link";
import { useState } from "react";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useAuth } from "@/context/app-context";
import {
  LayoutDashboard,
  User,
  LogOut,
  SpaceIcon,
  ChevronDown,
  ChevronRight,
  Users,
  Folder,
  Plus,
} from "lucide-react";
import ThemeToggle from "./theme-toggle";
import { API_ROUTES, APP_ROUTES } from "@/lib/constants";

interface SidebarNavProps extends React.HTMLAttributes<HTMLElement> {
  items: {
    href?: string;
    title: string;
    icon: React.ReactNode;
    subItems?: { title: string; href: string; icon: React.ReactNode }[];
  }[];
}

export function Sidebar() {
  const { logout } = useAuth();

  const sidebarNavItems = [
    {
      title: "Dashboard",
      href: APP_ROUTES.DASHBOARD,
      icon: <LayoutDashboard className="mr-2 h-4 w-4" />,
    },
    {
      title: "Profile",
      href: APP_ROUTES.PROFILE,
      icon: <User className="mr-2 h-4 w-4" />,
    },
    {
      title: "Spaces",
      icon: <SpaceIcon className="mr-2 h-4 w-4" />,
      subItems: [
        {
          title: "Create Spaces",
          href: API_ROUTES.SPACE.CREATE,
          icon: <Plus className="mr-2 h-4 w-4" />,
        },
        {
          title: "Public Spaces",
          href: API_ROUTES.SPACE.PUBLIC,
          icon: <Users className="mr-2 h-4 w-4" />,
        },
        {
          title: "My Spaces",
          href: API_ROUTES.SPACE.MINE,
          icon: <Folder className="mr-2 h-4 w-4" />,
        },
      ],
    },
  ];

  return (
    <aside className="w-64 fixed top-0 left-0 h-screen flex flex-col border-r bg-background z-50">
      <div className="flex h-14 items-center justify-between border-b px-4">
        <Link href="/" className="flex items-center gap-2 font-semibold">
          <span className="text-xl font-bold">DUT Grad</span>
        </Link>
        <ThemeToggle />
      </div>
      <ScrollArea className="flex-1">
        <div className="flex flex-col gap-1 p-2">
          <SidebarNav items={sidebarNavItems} />
        </div>
      </ScrollArea>
      <div className="border-t p-4">
        <Button
          variant="destructive"
          className="w-full flex items-center justify-center"
          onClick={() => logout()}
        >
          <LogOut className="mr-2 h-4 w-4" />
          Log out
        </Button>
      </div>
    </aside>
  );
}

export function SidebarNav({ items, className, ...props }: SidebarNavProps) {
  const pathname = usePathname();
  const [openMenus, setOpenMenus] = useState<Record<string, boolean>>({});

  const toggleMenu = (title: string) => {
    setOpenMenus((prev) => ({
      ...prev,
      [title]: !prev[title],
    }));
  };

  return (
    <nav className={cn("flex flex-col gap-1", className)} {...props}>
      {items.map((item) => (
        <div key={item.title}>
          {item.href ? (
            <Link
              href={item.href}
              className={cn(
                "flex items-center rounded-md px-3 py-2.5 text-sm font-medium transition-all hover:bg-accent hover:text-accent-foreground",
                pathname === item.href
                  ? "bg-accent text-accent-foreground"
                  : "transparent"
              )}
            >
              {item.icon}
              {item.title}
            </Link>
          ) : (
            <div>
              <button
                onClick={() => toggleMenu(item.title)}
                className="flex w-full items-center rounded-md px-3 py-2.5 text-sm font-medium transition-all hover:bg-accent hover:text-accent-foreground"
              >
                {item.icon}
                {item.title}
                <span className="ml-auto">
                  {openMenus[item.title] ? (
                    <ChevronDown className="h-4 w-4" />
                  ) : (
                    <ChevronRight className="h-4 w-4" />
                  )}
                </span>
              </button>
              {openMenus[item.title] && item.subItems && (
                <div className="ml-6 mt-1 flex flex-col gap-1">
                  {item.subItems.map((subItem) => (
                    <Link
                      key={subItem.href}
                      href={subItem.href}
                      className={cn(
                        "flex items-center rounded-md px-3 py-2 text-sm font-medium transition-all hover:bg-muted",
                        pathname === subItem.href
                          ? "bg-muted text-primary"
                          : "transparent"
                      )}
                    >
                      {subItem.icon}
                      {subItem.title}
                    </Link>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      ))}
    </nav>
  );
}
