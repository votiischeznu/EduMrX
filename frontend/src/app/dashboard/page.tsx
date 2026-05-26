"use client";

import {BarChart, Bar, XAxis, Tooltip, ResponsiveContainer} from "recharts";

const data = [
    {name: "Mon", attendance: 40},
    {name: "Tue", attendance: 65},
    {name: "Wed", attendance: 45},
    {name: "Thu", attendance: 80},
    {name: "Fri", attendance: 55},
];

export default function DashboardPage() {
    return (
        <div className="p-8 space-y-8 animate-fade-in">
            <h1 className="text-3xl font-bold">Dashboard</h1>

            {/* Statistika kartalari */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-card p-6 rounded-2xl border border-border shadow-sm">
                    <p className="text-muted-foreground text-sm">Total Students</p>
                    <h2 className="text-3xl font-bold mt-1">1,248</h2>
                </div>
                <div className="bg-card p-6 rounded-2xl border border-border shadow-sm">
                    <p className="text-muted-foreground text-sm">Active Courses</p>
                    <h2 className="text-3xl font-bold mt-1">12</h2>
                </div>
                <div className="bg-card p-6 rounded-2xl border border-border shadow-sm">
                    <p className="text-muted-foreground text-sm">Revenue This Month</p>
                    <h2 className="text-3xl font-bold mt-1 text-primary">85M UZS</h2>
                </div>
            </div>

            {/* Grafik */}
            <div className="bg-card p-8 rounded-2xl border border-border shadow-sm">
                <h3 className="font-bold text-lg mb-6">Attendance Trend</h3>
                <div className="h-64 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={data}>
                            <XAxis dataKey="name"/>
                            <Tooltip/>
                            <Bar dataKey="attendance" fill="#4f46e5" radius={[6, 6, 0, 0]}/>
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
    );
}