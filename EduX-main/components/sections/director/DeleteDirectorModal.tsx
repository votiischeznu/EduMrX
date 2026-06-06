"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { API } from "@/services/api";
import { AlertTriangle, Loader2 } from "lucide-react";
import { toast } from "react-toastify";

interface DeleteProps {
    id: string;
    name: string;
    onClose: () => void;
}

export default function DeleteDirectorModal({ id, name, onClose }: DeleteProps) {
    const queryClient = useQueryClient();

    const { mutate: deleteDirector, isPending } = useMutation({
        mutationFn: async () => {
            await API.delete(`/api/v1/super-admin/directors/${id}/`);
        },
        onSuccess: () => {
            toast.success("Direktor tizimdan muvaffaqiyatli o'chirildi.");
            queryClient.invalidateQueries({ queryKey: ["directors"] });
            onClose();
        },
        onError: (err: any) => {
            toast.error(err?.message || "O'chirishda xatolik");
        }
    });

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs animate-fade-in">
            <div className="absolute inset-0" onClick={onClose} />
            <div className="relative bg-white w-full max-w-sm rounded-xl shadow-xl border border-slate-100 p-6 text-center z-10">
                <div className="w-12 h-12 rounded-full bg-red-50 border border-red-100 flex items-center justify-center text-red-500 mx-auto mb-4">
                    <AlertTriangle className="w-6 h-6" />
                </div>
                <h3 className="text-base font-bold text-slate-900">Direktorni o'chirish</h3>
                <p className="text-sm text-slate-500 mt-2">
                    Rostdan ham <span className="font-semibold text-slate-800">"{name}"</span>ni o'chirmoqchimisiz?
                </p>
                <div className="flex items-center gap-3 mt-6">
                    <button type="button" onClick={onClose} className="flex-1 h-10 border border-slate-200 bg-white text-slate-700 text-sm font-semibold rounded-lg cursor-pointer">
                        Bekor qilish
                    </button>
                    <button type="button" onClick={() => deleteDirector()} disabled={isPending} className="flex-1 h-10 bg-red-600 text-white text-sm font-semibold rounded-lg disabled:bg-red-400 cursor-pointer">
                        {isPending ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : "O'chirilsin"}
                    </button>
                </div>
            </div>
        </div>
    );
}