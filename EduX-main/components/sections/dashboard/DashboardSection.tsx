"use client";

import AttendanceOverview from "@/components/sections/dashboard/DashboardChart";
import Text from "@/components/ui/Text";
import { API } from "@/services/api";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Users, LayoutGrid, DollarSign, Activity, ArrowUpRight, TrendingUp } from "lucide-react";
import Title from "@/components/ui/Title";

export default function DashboardSection() {
    const { data: dashboard } = useQuery({
        queryFn: async () => {
            const res = await API.get("api/v1/super-admin/dashboard/");
            return res?.data;
        },
        queryKey: ["dashboard"]
    });

    const status = [
        {
            id: 1,
            icon: <Users className="w-5 h-5 text-indigo-600" />,
            label: "Total Students",
            degree: dashboard?.students?.total_active ?? 0,
            color: "bg-indigo-50 border-indigo-100 text-indigo-600",
            hoverBorder: "hover:border-indigo-300",
            path: "/students",
            extraData: [
                { key: "Active Students", value: dashboard?.students?.total_active ?? 0 },
                { key: "New this month", value: "+28 ta" },
                { key: "Trial lessons", value: "14 ta" }
            ]
        },
        {
            id: 2,
            icon: <LayoutGrid className="w-5 h-5 text-emerald-600" />,
            label: "Active Groups",
            degree: dashboard?.groups?.active ?? 0,
            color: "bg-emerald-50 border-emerald-100 text-emerald-600",
            hoverBorder: "hover:border-emerald-300",
            path: "/groups",
            extraData: [
                { key: "General Groups", value: dashboard?.groups?.active ?? 0 },
                { key: "Bootcamp", value: "4 ta" },
                { key: "Evening slots", value: "8 ta" }
            ]
        },
        {
            id: 3,
            icon: <DollarSign className="w-5 h-5 text-amber-600" />,
            label: "Monthly Income",
            degree: dashboard?.finance?.monthly_income
                ? `${Number(dashboard.finance.monthly_income).toLocaleString("uz-UZ")} UZS`
                : "0 UZS",
            color: "bg-amber-50 border-amber-100 text-amber-600",
            hoverBorder: "hover:border-amber-300",
            path: "/payments",
            extraData: [
                { key: "Paid via Payme", value: "45%" },
                { key: "Paid via Cash", value: "55%" },
                { key: "Debts (Qarzdorlik)", value: "12.4M" }
            ]
        },
        {
            id: 4,
            icon: <Activity className="w-5 h-5 text-rose-600" />,
            label: "Attendance Rate",
            degree: dashboard?.attendance?.present_count ? `${dashboard.attendance.present_count}%` : "0%",
            color: "bg-rose-50 border-rose-100 text-rose-600",
            hoverBorder: "hover:border-rose-300",
            path: "/attendance",
            extraData: [
                { key: "Present (Kelgan)", value: "92%" },
                { key: "Absent (Kelmagan)", value: "5%" },
                { key: "With Reason", value: "3%" }
            ]
        },
    ];

    return (
        <div className="space-y-8">

            <div className="flex items-center justify-between">
                <div>
                    <Title text="Dashboard Overview" />
                    <div className="mt-1">
                        <Text text="Tizimdagi bugungi umumiy ko'rsatkichlar va jonli tahlillar bilan tanishing." />
                    </div>
                </div>
                <div className="flex items-center gap-2 text-xs font-bold text-indigo-600 bg-indigo-50 border border-indigo-100 px-3 py-1.5 rounded-xl self-start sm:self-center">
                    <TrendingUp className="w-3.5 h-3.5" />
                    <span>Jonli rejim faol</span>
                </div>
            </div>

            {/* Statistika Grid Tizimi */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 relative z-10">
                {status.map((item) => (
                    /* Butun karta Link qilingan, bosganda sahifaga o'tadi */
                    <Link
                        href={item.path}
                        key={item.id}
                        className={`bg-white border border-slate-200 rounded-2xl p-5 shadow-xs hover:shadow-md transition-all duration-300 block group relative h-[140px] ${item.hoverBorder}`}
                    >
                        {/* Asosiy ko'rinib turuvchi kontent */}
                        <div className="flex items-center justify-between mb-3">
                            <div className={`w-11 h-11 rounded-xl border flex items-center justify-center shadow-xs ${item.color}`}>
                                {item.icon}
                            </div>
                            <span className="text-[11px] text-slate-400 font-bold flex items-center gap-0.5 group-hover:text-indigo-600 transition-colors">
                                Ko'rish
                                <ArrowUpRight className="w-3.5 h-3.5" />
                            </span>
                        </div>

                        <div className="space-y-0.5">
                            <p className="text-[11px] font-bold text-slate-400 tracking-wider uppercase">{item.label}</p>
                            <h2 className="text-2xl font-black text-slate-900 tracking-tight truncate">
                                {item.degree}
                            </h2>
                        </div>

                        {/* HOVER BO'LGANDA KARTANING PASTIDAN ABSOLUTE CHIQUVCHI JADVAL */}
                        {/* 'top-full' orqali u pastdagi elementlarning ustiga suzib chiqadi va UI o'lchamini o'zgartirmaydi */}
                        <div className="absolute left-0 right-0 top-full bg-white border border-slate-200 border-t-0 p-4 rounded-b-2xl opacity-0 -translate-y-2 pointer-events-none group-hover:pointer-events-auto group-hover:opacity-100 group-hover:translate-y-0 transition-all duration-300 ease-out z-50 shadow-xl">
                            <p className="text-[10px] font-bold text-slate-400 mb-2 uppercase tracking-widest border-t border-slate-100 pt-2">Kengaytirilgan ma'lumotlar:</p>
                            <div className="space-y-1.5 text-xs">
                                {item.extraData.map((row, idx) => (
                                    <div key={idx} className="flex justify-between items-center py-0.5 border-b border-slate-50 last:border-0">
                                        <span className="text-slate-500 font-medium">{row.key}</span>
                                        <span className="font-bold text-slate-900">{row.value}</span>
                                    </div>
                                ))}
                            </div>
                        </div>

                    </Link>
                ))}
            </div>

            {/* Grafik va Monitoring Bo'limi */}
            {/* 'relative z-0' gridni yuqoridagi hover jadval ostida qolishini ta'minlaydi */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 relative z-0">
                <div className="lg:col-span-2">
                    <AttendanceOverview />
                </div>

                <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-xs flex flex-col justify-between">
                    <div>
                        <h3 className="text-base font-bold text-slate-900 mb-1">Tezkor Monitoring</h3>
                        <p className="text-xs text-slate-400 mb-5">Hozirgi faol dars jarayonlari</p>

                        <div className="space-y-3">
                            <div className="p-3 bg-slate-50 border border-slate-100 rounded-xl flex items-center justify-between hover:bg-slate-100/70 transition-colors">
                                <span className="text-xs font-semibold text-slate-600">Yangi o'quvchilar</span>
                                <span className="text-xs font-bold text-indigo-600 bg-indigo-50 border border-indigo-100 px-2 py-0.5 rounded-md">+24 ta</span>
                            </div>
                            <div className="p-3 bg-slate-50 border border-slate-100 rounded-xl flex items-center justify-between hover:bg-slate-100/70 transition-colors">
                                <span className="text-xs font-semibold text-slate-600">Guruhlar to'lishi</span>
                                <span className="text-xs font-bold text-emerald-600 bg-emerald-50 border border-emerald-100 px-2 py-0.5 rounded-md">84%</span>
                            </div>
                        </div>
                    </div>
                    <div className="mt-6 pt-4 border-t border-slate-100 text-center">
                        <p className="text-[11px] text-slate-400">Tizim ma'lumotlari real vaqtda yangilanadi</p>
                    </div>
                </div>
            </div>
        </div >
    );
}