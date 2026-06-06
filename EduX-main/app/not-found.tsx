"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, Home, HelpCircle } from "lucide-react";

export default function NotFound() {
    const router = useRouter();

    return (
        <div className="min-h-screen bg-[#F8FAFC] flex items-center justify-center p-6 text-slate-800">
            <div className="max-w-md w-full text-center space-y-8">

                <div className="relative flex justify-center items-center h-44">
                    <div className="absolute inset-0 bg-indigo-500/5 blur-3xl rounded-full max-w-xs mx-auto h-40 -z-10" />

                    <div className="text-9xl font-black text-indigo-600 tracking-tight select-none flex items-center justify-center gap-2">
                        <span>4</span>

                        <div className="flex items-center justify-center px-2">
                            <div className="w-24 h-24 rounded-full bg-white border border-slate-200/80 shadow-md flex items-center justify-center transition-transform hover:scale-105 duration-300">
                                <HelpCircle className="w-12 h-12 text-indigo-600 animate-bounce" />
                            </div>
                        </div>

                        <span>4</span>
                    </div>
                </div>

                <div className="space-y-3">
                    <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">
                        Sahifa topilmadi
                    </h2>
                    <p className="text-sm text-slate-500 max-w-sm mx-auto font-medium leading-relaxed">
                        Kechirasiz, siz qidirayotgan sahifa mavjud emas, o'chirilgan yoki manzili o'zgartirilgan bo'lishi mumkin.
                    </p>
                </div>

                <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
                    <button
                        onClick={() => router.back()}
                        className="w-full sm:w-auto px-6 py-2.5 bg-white border border-slate-200 hover:border-slate-300 rounded-xl font-bold text-sm text-slate-700 flex items-center justify-center gap-2 transition-all cursor-pointer shadow-xs active:scale-98"
                    >
                        <ArrowLeft className="w-4 h-4 text-slate-500" />
                        <span>Orqaga qaytish</span>
                    </button>

                    <Link
                        href="/"
                        className="w-full sm:w-auto px-6 py-2.5 bg-[#4F46E5] hover:bg-[#4338CA] rounded-xl font-bold text-sm text-white flex items-center justify-center gap-2 transition-all cursor-pointer shadow-sm active:scale-98"
                    >
                        <Home className="w-4 h-4" />
                        <span>Bosh sahifa</span>
                    </Link>
                </div>

                <div className="pt-8 border-t border-slate-200/60">
                    <p className="text-xs text-slate-400 font-semibold tracking-wider uppercase">
                        eduX boshqaruv tizimi
                    </p>
                </div>

            </div>
        </div>
    );
}