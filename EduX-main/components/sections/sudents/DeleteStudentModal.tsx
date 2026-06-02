"use client";

import { X, AlertTriangle, Loader2 } from "lucide-react";

interface DeleteStudentModalProps {
    studentName: string;
    isPending: boolean;
    onConfirm: () => void;
    onClose: () => void;
}

export default function DeleteStudentModal({
    studentName,
    isPending,
    onConfirm,
    onClose,
}: DeleteStudentModalProps) {
    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs">
            {/* Modal Card */}
            <div className="w-full max-w-md bg-white rounded-xl border border-slate-100 shadow-xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">

                {/* Header */}
                <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100 bg-slate-50/50">
                    <div className="flex items-center gap-2 text-red-600">
                        <AlertTriangle className="w-5 h-5" />
                        <h3 className="text-sm font-semibold text-slate-900">Talabani o'chirish</h3>
                    </div>
                    <button
                        onClick={onClose}
                        disabled={isPending}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors disabled:opacity-50"
                    >
                        <X className="w-4 h-4" />
                    </button>
                </div>

                {/* Body */}
                <div className="p-5">
                    <p className="text-sm text-slate-600 leading-relaxed">
                        Rostdan ham <span className="font-semibold text-slate-900">"{studentName}"</span> ismli talabani tizimdan butunlay o'chirib tashlamoqchimisiz?
                    </p>
                    <p className="text-xs text-red-500 font-medium mt-2 bg-red-50/50 border border-red-100/50 rounded-md p-2">
                        Ogohlantirish: Bu amalni ortga qaytarib bo'lmaydi va talabaga tegishli barcha ma'lumotlar o'chib ketadi.
                    </p>
                </div>

                {/* Footer */}
                <div className="flex items-center justify-end gap-2 px-5 py-3.5 bg-slate-50 border-t border-slate-100">
                    <button
                        type="button"
                        onClick={onClose}
                        disabled={isPending}
                        className="h-9 px-3.5 text-xs font-semibold text-slate-700 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors cursor-pointer disabled:opacity-50"
                    >
                        Bekor qilish
                    </button>
                    <button
                        type="button"
                        onClick={onConfirm}
                        disabled={isPending}
                        className="inline-flex items-center justify-center gap-1.5 h-9 px-4 text-xs font-semibold text-white bg-red-600 hover:bg-red-700 rounded-lg transition-colors cursor-pointer disabled:opacity-70 min-w-[100px]"
                    >
                        {isPending ? (
                            <>
                                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                                O'chirilmoqda...
                            </>
                        ) : (
                            "O'chirish"
                        )}
                    </button>
                </div>

            </div>
        </div>
    );
}