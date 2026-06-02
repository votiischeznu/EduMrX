"use client";

import { create } from "zustand";
import axios from "axios";

interface Tokens {
  access_token: string;
  refresh_token: string;
}

interface User {
  id: string;
  phone: string;
  email: string | null;
  first_name: string;
  last_name: string;
  full_name: string;
  role: string;
  avatar: string | null;
  is_active: boolean;
  is_staff: boolean;
}

interface AuthState {
  user: User | null;
  tokens: Tokens | null;
  isAuthenticated: boolean;
  isInitialized: boolean;

  login: (user: User, tokens: Tokens) => void;
  logout: () => void;
  initAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  tokens: null,
  isAuthenticated: false,
  isInitialized: false,

  login: (user, tokens) => {
    localStorage.setItem("tokens", JSON.stringify(tokens));
    set({ user, tokens, isAuthenticated: true, isInitialized: true });
  },

  logout: () => {
    localStorage.removeItem("tokens");
    set({
      user: null,
      tokens: null,
      isAuthenticated: false,
      isInitialized: true,
    });
  },

  initAuth: async () => {
    if (typeof window === "undefined") return;

    // Katta plyus: Agar allaqachon tekshirilgan bo'lsa, qayta ishga tushmaydi
    if (get().isInitialized) return;

    const storedTokens = localStorage.getItem("tokens");

    if (!storedTokens) {
      set({ isInitialized: true, isAuthenticated: false, user: null });
      return;
    }

    try {
      const tokens: Tokens = JSON.parse(storedTokens);

      const response = await axios.get(
        `${process.env.NEXT_PUBLIC_DataBaseURL}/api/v1/me/`,
        {
          headers: {
            Authorization: `Bearer ${tokens.access_token}`,
          },
        },
      );

      set({
        user: response.data,
        tokens,
        isAuthenticated: true,
        isInitialized: true,
      });
    } catch (error) {
      console.error("Auth initialization error:", error); // Xatolikni konsolda ko'rish uchun

      // Faqat token eskirgan bo'lsagina o'chirish ma'qul, lekin hozircha xavfsizlik uchun:
      localStorage.removeItem("tokens");
      set({
        user: null,
        tokens: null,
        isAuthenticated: false,
        isInitialized: true,
      });
    }
  },
}));
