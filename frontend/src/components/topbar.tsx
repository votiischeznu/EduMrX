"use client";

import React from "react";
import { Bell, Menu, Search, Shield } from "lucide-react";
import { Button } from "Frontend/frontend/src/components/ui/button";
import { Input } from "Frontend/frontend/src/components/ui/input";
import { Badge } from "Frontend/frontend/src/components/ui/badge";
import { Avatar, AvatarFallback } from "Frontend/frontend/src/components/ui/avatar";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger,
} from "Frontend/frontend/src/components/ui/dropdown-menu";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "Frontend/frontend/src/components/ui/select";
import { useAppStore } from "Frontend/frontend/src/lib/store";
import { getInitials } from "Frontend/frontend/src/lib/utils";
import type { Role } from "Frontend/frontend/src/lib/mock-data";

export function Topbar() {
  const { toggleSidebar, currentRole, setRole, userName } = useAppStore();

  const roleLabels: Record<Role, string> = {
    admin: "Admin",
    teacher: "Teacher",
    student: "Student",
    parent: "Parent",
  };

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b bg-white/80 backdrop-blur-md px-4 md:px-6">
      {/* Mobile menu button */}
      <Button
        variant="ghost"
        size="icon"
        className="lg:hidden shrink-0"
        onClick={toggleSidebar}
      >
        <Menu className="h-5 w-5" />
      </Button>

      {/* Search */}
      <div className="relative hidden md:flex flex-1 max-w-md">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
        <Input
          placeholder="Search students, groups..."
          className="pl-9 bg-slate-50 border-slate-200 focus:bg-white"
        />
      </div>

      <div className="flex-1 md:hidden" />

      {/* Right side */}
      <div className="flex items-center gap-2">
        {/* Role Switcher */}
        <div className="hidden sm:flex items-center gap-2">
          <Shield className="h-4 w-4 text-slate-400" />
          <Select value={currentRole} onValueChange={(v) => setRole(v as Role)}>
            <SelectTrigger className="w-[130px] h-8 text-xs bg-slate-50">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="admin">Admin</SelectItem>
              <SelectItem value="teacher">Teacher</SelectItem>
              <SelectItem value="student">Student</SelectItem>
              <SelectItem value="parent">Parent</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Notifications */}
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-5 w-5 text-slate-500" />
          <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-red-500" />
        </Button>

        {/* User menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="relative h-9 w-9 rounded-full">
              <Avatar className="h-9 w-9">
                <AvatarFallback>{getInitials(userName)}</AvatarFallback>
              </Avatar>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="w-56" align="end" forceMount>
            <DropdownMenuLabel className="font-normal">
              <div className="flex flex-col space-y-1">
                <p className="text-sm font-medium leading-none">{userName}</p>
                <p className="text-xs leading-none text-muted-foreground">
                  {roleLabels[currentRole]}
                </p>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem>Profile</DropdownMenuItem>
            <DropdownMenuItem>Settings</DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="text-red-600">Log out</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
