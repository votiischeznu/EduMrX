
"use client";

import { useAuthStore } from "@/store/authStore";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { toast } from "react-toastify";

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
    const router = useRouter();
    const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
    const isInitialized = useAuthStore((state) => state.isInitialized);
    const initAuth = useAuthStore((state) => state.initAuth);

    useEffect(() => {
        initAuth();
    }, []);

    useEffect(() => {
        if (isInitialized && !isAuthenticated) {
            toast.warn("Siz tizimga kirmagansiz yoki seans muddati tugagan!");
            router.push("/login");
        }
    }, [isInitialized, isAuthenticated, router]);