"use client";

import { useEffect, useState } from "react";
import { useAuthStore } from "@/store/authStore";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

export default function Provider({ children }: { children: React.ReactNode }) {
    const [queryClient] = useState(() => new QueryClient());

    const initAuth = useAuthStore((state) => state.initAuth);

    useEffect(() => {
        if (typeof initAuth === "function") {
            initAuth();
        }
    }, [initAuth]);

    return (
        <QueryClientProvider client={queryClient}>
            {children}
            <ToastContainer position="top-right" autoClose={3000} />
        </QueryClientProvider>
    );
}