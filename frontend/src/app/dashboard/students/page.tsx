"use client";

import { students } from "@/lib/mock-data";
import { Search, Plus, Filter, MoreHorizontal, User } from "lucide-react";

export default function StudentsPage() {
  return (
    <div className="p-8 space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-extrabold text-foreground tracking-tight">Students</h1>
          <p className="text-muted-foreground mt-1">Manage and track student enrollment, performance, and status.</p>
        </div>
        <button className="bg-primary hover:bg-primary/90 text-primary-foreground px-5 py-2.5 rounded-lg font-semibold flex items-center gap-2 transition-all hover:shadow-lg hover:shadow-primary/20">
          <Plus size={18} /> Add Student
        </button>
      </div>

      {/* Main Content Area */}
      <div className="bg-card border border-border rounded-xl shadow-sm overflow-hidden">
        {/* Toolbar */}
        <div className="p-4 border-b border-border flex items-center gap-3">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={18} />
            <input
              className="w-full pl-10 pr-4 py-2 bg-secondary border border-border rounded-lg focus:ring-2 focus:ring-primary/20 outline-none transition-all"
              placeholder="Search students..."
            />
          </div>
          <button className="flex items-center gap-2 px-4 py-2 border border-border rounded-lg hover:bg-secondary transition-colors">
            <Filter size={18} /> All Groups
          </button>
        </div>

        {/* Table */}
        <table className="w-full text-left">
          <thead className="bg-muted/50 text-muted-foreground text-xs uppercase font-semibold">
            <tr>
              <th className="px-6 py-4">Student</th>
              <th className="px-6 py-4">Group</th>
              <th className="px-6 py-4">Contact</th>
              <th className="px-6 py-4">Balance</th>
              <th className="px-6 py-4">Status</th>
              <th className="px-6 py-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {students.map((s) => (
              <tr key={s.id} className="hover:bg-accent/50 transition-colors cursor-pointer group">
                <td className="px-6 py-4 font-medium flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                    <User size={16} />
                  </div>
                  {s.name}
                </td>
                <td className="px-6 py-4 text-sm">Mathematics</td>
                <td className="px-6 py-4 text-sm text-muted-foreground">{s.phone}</td>
                <td className={`px-6 py-4 font-bold ${s.balance < 0 ? 'text-destructive' : 'text-foreground'}`}>
                  {s.balance.toLocaleString()} UZS
                </td>
                <td className="px-6 py-4">
                  <span className="px-2.5 py-1 bg-emerald-100 text-emerald-700 rounded-full text-xs font-semibold">Active</span>
                </td>
                <td className="px-6 py-4 text-right">
                  <button className="text-muted-foreground hover:text-primary transition-colors">
                    <MoreHorizontal size={20} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}