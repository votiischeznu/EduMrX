"use client";

import { groups, teachers } from "Frontend/frontend/src/lib/mock-data";
import { FolderGit2, Users, Calendar, Clock, User, ChevronRight } from "lucide-react";

export default function GroupsPage() {
  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-extrabold text-foreground tracking-tight">Groups & Courses</h1>
          <p className="text-muted-foreground mt-1">Manage educational offerings and class cohorts.</p>
        </div>
        <button className="bg-primary text-primary-foreground px-5 py-2.5 rounded-xl font-semibold flex items-center gap-2 hover:bg-primary/90 shadow-lg">
          + Create Group
        </button>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {groups.map((group) => {
          const teacher = teachers.find((t) => t.id === group.teacherId);
          return (
            <div key={group.id} className="group bg-card border border-border p-6 rounded-2xl shadow-sm hover:shadow-xl hover:border-primary/20 transition-all duration-300">
              <div className="flex justify-between items-start mb-6">
                <div className="p-3 bg-primary/10 text-primary rounded-xl">
                  <FolderGit2 size={24} />
                </div>
                <div className="px-3 py-1 bg-emerald-50 text-emerald-700 rounded-full text-xs font-bold border border-emerald-100 flex items-center gap-1.5">
                   <span className="w-2 h-2 rounded-full bg-emerald-500"></span> Active
                </div>
              </div>

              <h3 className="text-xl font-bold text-foreground mb-4 group-hover:text-primary transition-colors">{group.name}</h3>

              <div className="space-y-3 text-sm text-muted-foreground">
                <div className="flex items-center gap-2.5"><Calendar size={18} className="text-primary"/> {group.schedule}</div>
                <div className="flex items-center gap-2.5"><Clock size={18} className="text-primary"/> {group.time}</div>
                <div className="flex items-center gap-2.5"><User size={18} className="text-primary"/> {teacher?.name}</div>
              </div>

              <div className="mt-6 pt-6 border-t border-border flex justify-between items-center">
                <span className="text-sm font-semibold text-foreground flex items-center gap-2">
                  <Users size={16} /> {group.studentIds.length} Students
                </span>
                <button className="text-primary hover:bg-primary/10 p-2 rounded-lg transition-colors">
                  <ChevronRight size={20} />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}