"use client";

import { useState, useEffect, useRef } from "react";
import {
    AreaChart, Area, XAxis, YAxis,
    ResponsiveContainer, Tooltip, CartesianGrid,
} from "recharts";
import { ChevronDown, CalendarDays } from "lucide-react";
import { useAuthStore } from "@/store/authStore";

type Period = "This Week" | "Last Week" | "This Month";

interface DayData {
    day: string;
    date: string;
    present: number;
    absent: number;
}

interface CustomTooltipProps {
    active?: boolean;
    payload?: { value: number; name: string }[];
    label?: string;
}

const PERIOD_MAP: Record<Period, string> = {
    "This Week": "this_week",
    "Last Week": "last_week",
    "This Month": "this_month",
};

function CustomTooltip({ active, payload, label }: CustomTooltipProps) {
    if (active && payload && payload.length) {
        return (
            <div className="bg-slate-900 text-white shadow-xl rounded-xl px-4 py-2.5 text-xs border border-slate-800">
                <p className="font-semibold text-slate-400 mb-1">{label} kuni</p>
                <p className="text-indigo-300 font-bold">Keldi: {payload[0]?.value ?? 0} ta</p>
                <p className="text-red-400 font-bold">Kelmadi: {payload[1]?.value ?? 0} ta</p>
            </div>
        );
    }
    return null;
}

export default function AttendanceOverview() {
    const tokens = useAuthStore((state) => state.tokens);
    const [isOpen, setIsOpen] = useState(false);
    const [selected, setSelected] = useState<Period>("This Week");
    const [data, setData] = useState<DayData[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);
    const periods: Period[] = ["This Week", "Last Week", "This Month"];

    useEffect(() => {
        if (!tokens?.access_token) return;

        const fetchData = async () => {
            setLoading(true);
            setError(false);
            try {
                const res = await fetch(
                    `/api/v1/attendance/overview/?period=${PERIOD_MAP[selected]}`,
                    {
                        headers: {
                            Authorization: `Bearer ${tokens.access_token}`,
                        },
                    }
                );
                if (!res.ok) throw new Error();
                const json: DayData[] = await res.json();
                setData(json);
            } catch {
                setError(true);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [selected, tokens]);

    useEffect(() => {
        const handleClickOutside = (e: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
                setIsOpen(false);
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const totalPresent = data.reduce((sum, d) => sum + d.present, 0);
    const totalAbsent = data.reduce((sum, d) => sum + d.absent, 0);
    const total = totalPresent + totalAbsent;
    const rate = total > 0 ? Math.round((totalPresent / total) * 100) : 0;

    return (
        <div className="bg-white rounded-2xl p-6 shadow-xs border border-slate-200 w-full flex flex-col h-full justify-between">

            {/* Header */}
            <div className="flex justify-between items-center mb-4">
                <div>
                    <h2 className="text-base font-bold text-slate-900 tracking-wide">
                        Attendance Overview
                    </h2>
                    <p className="text-xs text-slate-500 mt-0.5">
                        Haqiqiy davomat statistikasi
                    </p>
                </div>

                {/* Dropdown */}
                <div ref={dropdownRef} className="relative">
                    <button
                        onClick={() => setIsOpen((prev) => !prev)}
                        className="bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5 text-xs font-bold text-slate-700 flex items-center gap-2 hover:bg-slate-100 transition-all cursor-pointer shadow-xs"
                    >
                        <CalendarDays className="w-3.5 h-3.5 text-indigo-600" />
                        {selected}
                        <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
                    </button>
                    {isOpen && (
                        <div className="absolute right-0 mt-2 bg-white border border-slate-200 rounded-xl shadow-xl z-20 overflow-hidden w-36 py-1">
                            {periods.map((period) => (
                                <button
                                    key={period}
                                    onClick={() => {
                                        setSelected(period);
                                        setIsOpen(false);
                                    }}
                                    className={`block w-full text-left px-4 py-2 text-xs font-semibold transition-colors ${selected === period
                                        ? "text-indigo-600 bg-indigo-50"
                                        : "text-slate-600 hover:bg-slate-50"
                                        }`}
                                >
                                    {period}
                                </button>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-3 mb-4">
                <div className="bg-slate-50 rounded-xl p-3">
                    <p className="text-xs text-slate-500 mb-1">Keldi</p>
                    <p className="text-xl font-bold text-indigo-600">{totalPresent}</p>
                </div>
                <div className="bg-slate-50 rounded-xl p-3">
                    <p className="text-xs text-slate-500 mb-1">Kelmadi</p>
                    <p className="text-xl font-bold text-red-500">{totalAbsent}</p>
                </div>
                <div className="bg-slate-50 rounded-xl p-3">
                    <p className="text-xs text-slate-500 mb-1">Davomat %</p>
                    <p className="text-xl font-bold text-emerald-600">{rate}%</p>
                </div>
            </div>

            {/* Chart */}
            <div className="w-full h-[220px]">
                {loading ? (
                    <div className="flex items-center justify-center h-full">
                        <div className="w-full h-full bg-slate-100 rounded-xl animate-pulse" />
                    </div>
                ) : error ? (
                    <div className="flex items-center justify-center h-full text-red-400 text-sm">
                        Ma&apos;lumot yuklanmadi
                    </div>
                ) : (
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart
                            data={data}
                            margin={{ bottom: 0, left: -25, right: 10, top: 10 }}
                        >
                            <defs>
                                <linearGradient id="presentGlow" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#4F46E5" stopOpacity={0.2} />
                                    <stop offset="95%" stopColor="#4F46E5" stopOpacity={0} />
                                </linearGradient>
                                <linearGradient id="absentGlow" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#EF4444" stopOpacity={0.15} />
                                    <stop offset="95%" stopColor="#EF4444" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid
                                strokeDasharray="3 3"
                                vertical={false}
                                stroke="#E2E8F0"
                                opacity={0.7}
                            />
                            <XAxis
                                dataKey="day"
                                axisLine={false}
                                tickLine={false}
                                tick={{ fill: "#64748B", fontSize: 11, fontWeight: "600" }}
                            />
                            <YAxis
                                axisLine={false}
                                tickLine={false}
                                tick={{ fill: "#64748B", fontSize: 11 }}
                                allowDecimals={false}
                            />
                            <Tooltip content={<CustomTooltip />} />
                            <Area
                                type="monotone"
                                dataKey="present"
                                stroke="#4F46E5"
                                strokeWidth={2.5}
                                fill="url(#presentGlow)"
                            />
                            <Area
                                type="monotone"
                                dataKey="absent"
                                stroke="#EF4444"
                                strokeWidth={2.5}
                                fill="url(#absentGlow)"
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                )}
            </div>

            {/* Legend */}
            <div className="flex gap-4 mt-3">
                <span className="flex items-center gap-1.5 text-xs text-slate-500">
                    <span className="w-3 h-3 rounded-sm bg-indigo-500 inline-block" />
                    Keldi
                </span>
                <span className="flex items-center gap-1.5 text-xs text-slate-500">
                    <span className="w-3 h-3 rounded-sm bg-red-400 inline-block" />
                    Kelmadi
                </span>
            </div>
        </div>
    );
}
