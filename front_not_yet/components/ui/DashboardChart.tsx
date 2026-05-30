"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { navigate } from "next/dist/client/components/segment-cache/navigation";
import { useState } from "react";
import { toast } from "react-toastify";
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    Cell,
    ResponsiveContainer,
    Tooltip,
} from "recharts";

type Period = "This Week" | "Last Week" | "This Month";

const weekData: Record<Period, { day: string; value: number }[]> = {
    "This Week": [
        { day: "Mon", value: 45 },
        { day: "Tue", value: 65 },
        { day: "Wed", value: 90 },
        { day: "Thu", value: 60 },
        { day: "Fri", value: 40 },
        { day: "Sat", value: 25 },
    ],
    "Last Week": [
        { day: "Mon", value: 70 },
        { day: "Tue", value: 50 },
        { day: "Wed", value: 80 },
        { day: "Thu", value: 30 },
        { day: "Fri", value: 55 },
        { day: "Sat", value: 20 },
    ],
    "This Month": [
        { day: "Mon", value: 55 },
        { day: "Tue", value: 75 },
        { day: "Wed", value: 60 },
        { day: "Thu", value: 85 },
        { day: "Fri", value: 45 },
        { day: "Sat", value: 30 },
    ],
};

const ACTIVE_DAY = "Wed";
const ACTIVE_COLOR = "#3730A3";
const DEFAULT_COLOR = "#C7C2F0";

interface CustomTooltipProps {
    active?: boolean;
    payload?: { value: number }[];
    label?: string;
}

function CustomTooltip({ active, payload, label }: CustomTooltipProps) {
    if (active && payload && payload.length) {
        return (
            <div className="bg-white border border-gray-100 shadow-lg rounded-xl px-4 py-2 text-sm">
                <p className="font-semibold text-gray-800">{label}</p>
                <p className="text-indigo-600 font-bold">{payload[0].value} students</p>
            </div>
        );
    }
    return null;
}

export default function AttendanceOverview() {
    const [isOpen, setIsOpen] = useState(false);
    const [selected, setSelected] = useState<Period>("This Week");

    const data = weekData[selected];
    const periods: Period[] = ["This Week", "Last Week", "This Month"];

    return (
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 w-full max-full">
            {/* Header */}
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-bold text-gray-900">Attendance Overview</h2>

                {/* Dropdown */}
                <div className="relative">
                    <button
                        onClick={() => setIsOpen((prev) => !prev)}
                        className="border border-gray-200 rounded-xl px-4 py-2 text-sm text-gray-600 flex items-center gap-2 hover:bg-gray-50 transition-colors"
                    >
                        {selected}
                        <svg
                            className={`w-4 h-4 transition-transform ${isOpen ? "rotate-180" : ""}`}
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M19 9l-7 7-7-7"
                            />
                        </svg>
                    </button>

                    {isOpen && (
                        <div className="absolute right-0 mt-2 bg-white border border-gray-100 rounded-xl shadow-lg z-10 overflow-hidden">
                            {periods.map((period) => (
                                <button
                                    key={period}
                                    onClick={() => {
                                        setSelected(period);
                                        setIsOpen(false);
                                    }}
                                    className={`block w-full text-left px-4 py-2 text-sm hover:bg-indigo-50 transition-colors ${selected === period
                                        ? "text-indigo-600 font-semibold bg-indigo-50"
                                        : "text-gray-600"
                                        }`}
                                >
                                    {period}
                                </button>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* Chart */}
            <ResponsiveContainer width="100%" height={300}>
                <BarChart data={data} barCategoryGap="35%" margin={{ bottom: 8 }}>
                    <XAxis
                        dataKey="day"
                        axisLine={false}
                        tickLine={false}
                        tick={({ x, y, payload }) => (
                            <text
                                x={x}
                                y={Number(y) + 16}
                                textAnchor="middle"
                                fill={payload.value === ACTIVE_DAY ? ACTIVE_COLOR : "#9CA3AF"}
                                fontWeight={payload.value === ACTIVE_DAY ? "700" : "400"}
                                fontSize={14}
                            >
                                {payload.value}
                            </text>
                        )}
                    />
                    <YAxis hide />
                    <Tooltip content={<CustomTooltip />} cursor={false} />
                    <Bar dataKey="value" radius={[8, 8, 8, 8]}>
                        {data.map((entry) => (
                            <Cell
                                key={entry.day}
                                fill={entry.day === ACTIVE_DAY ? ACTIVE_COLOR : DEFAULT_COLOR}
                            />
                        ))}
                    </Bar>
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
}