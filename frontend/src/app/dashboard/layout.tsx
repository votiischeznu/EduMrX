"use client";

import { useAppStore } from "Frontend/frontend/src/lib/store";
import { LayoutDashboard, Users, BookOpen, Users2, Calendar, CreditCard, FileText, Settings, ChevronLeft, ChevronRight } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Students", href: "/dashboard/students", icon: Users },
  { name: "Courses", href: "/dashboard/courses", icon: BookOpen },
  { name: "Groups", href: "/dashboard/groups", icon: Users2 },
  { name: "Attendance", href: "/dashboard/attendance", icon: Calendar },
  { name: "Payments", href: "/dashboard/payments", icon: CreditCard },
  { name: "Reports", href: "/dashboard/reports", icon: FileText },
  { name: "Settings", href: "/dashboard/settings", icon: Settings },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { sidebarCollapsed, toggleSidebarCollapse } = useAppStore();
  const pathname = usePathname();

  return (
    <div className="flex h-screen bg-background text-foreground">
      {/* Sidebar */}
      <aside className={`border-r bg-sidebar transition-all duration-300 flex flex-col ${sidebarCollapsed ? "w-20" : "w-64"}`}>
        <div className="p-6 font-bold text-2xl flex items-center justify-between">
          {!sidebarCollapsed && "EduMrX"}
          <button onClick={toggleSidebarCollapse} className="p-1 rounded-md hover:bg-accent">
            {sidebarCollapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
          </button>
        </div>

        <nav className="flex-1 px-4 space-y-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link key={item.name} href={item.href} className={`flex items-center gap-3 p-3 rounded-xl transition-all ${isActive ? "bg-primary text-primary-foreground" : "hover:bg-accent"}`}>
                <item.icon size={20} />
                {!sidebarCollapsed && <span className="font-medium">{item.name}</span>}
              </Link>
            );
          })}
        </nav>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="h-16 border-b flex items-center justify-end px-8 bg-card gap-4">
          <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center font-bold text-primary">J</div>
        </header>
        <main className="flex-1 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
}