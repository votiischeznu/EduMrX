import { create } from "zustand";
import { type Role, currentUser } from "./mock-data";

interface AppState {
  // Sidebar
  sidebarOpen: boolean;
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;
  toggleSidebarCollapse: () => void;
  setSidebarOpen: (open: boolean) => void;

  // Role
  currentRole: Role;
  setRole: (role: Role) => void;

  // User
  userName: string;
  userEmail: string;
}

export const useAppStore = create<AppState>((set) => ({
  sidebarOpen: false,
  sidebarCollapsed: false,
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  toggleSidebarCollapse: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),

  currentRole: currentUser.role,
  setRole: (role) => set({ currentRole: role }),

  userName: currentUser.name,
  userEmail: currentUser.email,
}));
