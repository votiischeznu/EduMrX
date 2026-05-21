"use client";

import { useState } from "react";
import { Check, X, Minus, ChevronLeft, ChevronRight } from "lucide-react";

export default function AttendancePage() {
  // Mock holat: 1-15 kunlar uchun davomat
  const [attendance, setAttendance] = useState<Record<number, string>>({});

  const toggleAttendance = (day: number) => {
    const states = ["present", "absent", "excused", "none"];
    const currentIndex = states.indexOf(attendance[day] || "none");
    const nextState = states[(currentIndex + 1) % states.length];
    setAttendance({ ...attendance, [day]: nextState });
  };

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-extrabold text-foreground tracking-tight">Attendance</h1>
        <p className="text-muted-foreground">O'quvchilarning darslarga qatnashishini boshqarish</p>
      </div>

      {/* Taqvim Paneli */}
      <div className="bg-card border border-border rounded-2xl p-6 shadow-sm">
        <div className="flex items-center justify-between mb-8">
          <h2 className="text-xl font-bold">May 2026</h2>
          <div className="flex gap-2">
            <button className="p-2 hover:bg-secondary rounded-lg"><ChevronLeft size={20}/></button>
            <button className="p-2 hover:bg-secondary rounded-lg"><ChevronRight size={20}/></button>
          </div>
        </div>

        <div className="grid grid-cols-7 gap-2">
          {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map(day => (
            <div key={day} className="text-center text-xs font-bold text-muted-foreground uppercase py-2">{day}</div>
          ))}

          {Array.from({ length: 30 }).map((_, i) => {
            const day = i + 1;
            const status = attendance[day] || "none";

            return (
              <button
                key={day}
                onClick={() => toggleAttendance(day)}
                className={`h-24 border rounded-xl flex flex-col items-center justify-center transition-all ${
                  status === "present" ? "bg-emerald-50 border-emerald-200" :
                  status === "absent" ? "bg-red-50 border-red-200" :
                  status === "excused" ? "bg-amber-50 border-amber-200" :
                  "hover:bg-secondary border-border"
                }`}
              >
                <span className="font-bold text-lg">{day}</span>
                {status === "present" && <Check className="text-emerald-600 mt-2" size={20}/>}
                {status === "absent" && <X className="text-red-600 mt-2" size={20}/>}
                {status === "excused" && <Minus className="text-amber-600 mt-2" size={20}/>}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}