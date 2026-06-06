"use client";

import { useState, useEffect } from "react";
import { AlertTriangle, X, Loader2 } from "lucide-react";

interface DeleteTeacherModalProps {
    teacherName: string;
    isPending: boolean;
    onConfirm: () => void;
    onClose: () => void;
}

export default function DeleteTeacherModal({
    teacherName,
    isPending,
    onConfirm,
    onClose,
}: DeleteTeacherModalProps) {
    const [isMounted, setIsMounted] = useState(false);

    useEffect(() => {
        setIsMounted(true);
    }, []);

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            {/* Orqa fon (Backdrop) */}
            <div
                className={`fixed inset-0 bg-slate-900/40 backdrop-blur-sm transition-opacity duration-300 ${isMounted ? "opacity-100" : "opacity-0"
                    }`}
                onClick={!isPending ? onClose : undefined}
            />

            {/* Modal Oynasi */}
            <div
                className={`bg-white p-6 rounded-xl max-w-md w-full relative z-10 shadow-2xl border border-slate-100 transform transition-all duration-300 ease-out ${isMounted ? "opacity-100 translate-y-0 scale-100" : "opacity-0 -translate-y-8 scale-95"
                    }`}
            >
                {/* Yopish tugmasi */}
                {!isPending && (
                    <button
                        type="button"
                        onClick={onClose}
                        className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-50 transition-colors cursor-pointer"
                    >
                        <X className="w-5 h-5" />
                    </button>
                )}

                {/* Ogohlantirish ikonasi (Siz xohlagan qizil/amber minimalizm uslubida) */}
                <div className="mb-4 border-red-100 border shadow-sm w-11 h-11 rounded-lg flex justify-center items-center text-red-600 bg-red-50/50">
                    <AlertTriangle className="w-5 h-5" />
                </div>

                {/* Matn qismi */}
                <h3 className="text-[#313131] text-[18px] font-semibold mb-2">Delete Teacher Profile</h3>
                <p className="text-slate-500 text-sm mb-6 leading-relaxed">
                    Rostdan ham <span className="font-semibold text-slate-800">"{teacherName}"</span> ismli o'qituvchi profilini o'chirib tashlamoqchimisiz? Bu amalni ortga qaytarib bo'lmaydi.
                </p>

                {/* Amallar tugmalari */}
                <div className="flex flex-col sm:flex-row sm:justify-end gap-3">
                    <button
                        type="button"
                        disabled={isPending}
                        onClick={onClose}
                        className="h-10 px-4 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-lg text-sm font-semibold transition-colors disabled:opacity-50 cursor-pointer order-2 sm:order-1"
                    >
                        Cancel
                    </button>

                    <button
                        type="button"
                        disabled={isPending}
                        onClick={onConfirm}
                        className="h-10 px-4 bg-red-600 hover:bg-red-700 disabled:bg-red-400 text-white rounded-lg text-sm font-semibold transition-colors flex items-center justify-center gap-2 cursor-pointer order-1 sm:order-2"
                    >
                        {isPending ? (
                            <>
                                <Loader2 className="w-4 h-4 animate-spin" />
                                O'chirilmoqda...
                            </>
                        ) : (
                            "Delete Teacher"
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
}