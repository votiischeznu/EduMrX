"use client";

import { Bell } from "lucide-react";
import { useState } from "react";

export default function NotificationBell() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative">
      <button onClick={() => setIsOpen(!isOpen)} className="p-2 text-muted-foreground hover:bg-secondary rounded-full transition-all">
        <Bell size={20} />
        <span className="absolute top-2 right-2 w-2 h-2 bg-rose-500 rounded-full"></span>
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-72 bg-card border border-border rounded-xl shadow-xl p-4 animate-scale-in">
          <h4 className="font-bold mb-3">Notifications</h4>
          <div className="space-y-3">
            <div className="text-sm">
              <p className="font-semibold text-foreground">Payment Received</p>
              <p className="text-muted-foreground">Jasur Aliyev paid 500,000 UZS</p>
            </div>
            <div className="text-sm">
              <p className="font-semibold text-foreground">New Student</p>
              <p className="text-muted-foreground">Nilufar joined the English group</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}