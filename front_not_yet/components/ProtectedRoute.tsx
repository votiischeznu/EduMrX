"use client";

import { useAuthStore } from "@/store/authStore";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function ProtectedRoute({ children }: { children: React.ReactNode }) {
    const router = useRouter();
    const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
    const isInitialized = useAuthStore((state) => state.isInitialized);
    const initAuth = useAuthStore((state) => state.initAuth);

    useEffect(() => {
        initAuth();
    }, [initAuth]);

    useEffect(() => {
        if (isInitialized && !isAuthenticated) {
            router.push("/login");
        }
    }, [isInitialized, isAuthenticated, router]);

    if (!isInitialized) {
        return (
            <div className="flex h-screen items-center justify-center bg-gray-50">
                <p className="text-lg font-medium text-gray-600">Xavfsiz ulanish tekshirilmoqda...</p>
            </div>
        );
    }

    if (!isAuthenticated) return null;

    return <>{children}</>;
}