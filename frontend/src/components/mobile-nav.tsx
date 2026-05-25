"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Users, UsersRound, CalendarCheck, CreditCard } from "lucide-react";
import { cn } from "Frontend/frontend/src/lib/utils";

const mobileNavItems = [
  { href: "/dashboard", label: "Home", icon: LayoutDashboard },
  { href: "/students", label: "Students", icon: Users },
  { href: "/groups", label: "Groups", icon: UsersRound },
  { href: "/attendance", label: "Attend", icon: CalendarCheck },
  { href: "/payments", label: "Payments", icon: CreditCard },
];

export function MobileNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-40 flex items-center justify-around border-t bg-white/95 backdrop-blur-md px-2 py-1.5 lg:hidden">
      {mobileNavItems.map((item) => {
        const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex flex-col items-center gap-0.5 px-3 py-1 rounded-lg text-xs font-medium transition-colors",
              isActive ? "text-indigo-600" : "text-slate-400 hover:text-slate-600"
            )}
          >
            <item.icon className={cn("h-5 w-5", isActive && "text-indigo-600")} />
            <span>{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
