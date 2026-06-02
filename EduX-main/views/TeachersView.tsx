"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { API } from "@/services/api";
import {
  GraduationCap,
  Phone,
  Mail,
  Building2,
  Plus,
  Trash2,
  Edit3,
  Loader2,
  AlertCircle,
  Briefcase,
  Star
} from "lucide-react";
import { toast } from "react-toastify";
import { useState } from "react";
import AddTeacherModal from "@/components/sections/teachers/AddTeacherModal";
import EditTeacherModal from "@/components/sections/teachers/EditTeacherModal";
import DeleteTeacherModal from "@/components/sections/teachers/DeleteTeacherModal"; // Yangi modal
import Title from "@/components/ui/Title";
import Text from "@/components/ui/Text";

interface Teacher {
  id: string;
  full_name: string;
  email: string;
  phone: string;
  specialization: string;
  experience: number;
  avatar?: string | null;
  center_name?: string;
}

export default function TeachersView() {
  const queryClient = useQueryClient();
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [editingTeacher, setEditingTeacher] = useState<Teacher | null>(null);
  const [deletingTeacher, setDeletingTeacher] = useState<Teacher | null>(null);

  const { data: teachers, isLoading, isError, error } = useQuery<Teacher[]>({
    queryKey: ["teachers"],
    queryFn: async () => {
      const res = await API.get("/api/v1/super-admin/teachers/");
      return res?.data?.results || res?.data || [];
    },
  });

  const { mutate: deleteTeacher, isPending: isDeletePending } = useMutation({
    mutationFn: async (id: string) => {
      await API.delete(`/api/v1/super-admin/teachers/${id}/`);
    },
    onSuccess: () => {
      toast.success("Teacher successfully deleted");
      queryClient.invalidateQueries({ queryKey: ["teachers"] });
      setDeletingTeacher(null);
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.message || "Error deleting teacher");
    },
  });

  const formatPhoneView = (phone: string) => {
    const clean = phone.replace(/\D/g, "");
    if (clean.length === 12) {
      return `+998 (${clean.slice(3, 5)}) ${clean.slice(5, 8)}-${clean.slice(8, 10)}-${clean.slice(10)}`;
    }
    return phone;
  };

  return (
    <div className="w-full">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <Title text="Teachers" />
          <Text text="Manage educator profiles, specializations, and center assignments." />
        </div>
        <button
          onClick={() => setIsAddOpen(true)}
          className="inline-flex items-center justify-center gap-2 h-10 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm rounded-lg shadow-sm transition-colors cursor-pointer shrink-0"
        >
          <Plus className="w-4 h-4" /> Add Teacher
        </button>
      </div>

      {isLoading && (
        <div className="flex flex-col items-center justify-center py-20 bg-white rounded-xl border border-slate-100 shadow-sm">
          <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
          <p className="text-sm text-slate-500 mt-3 font-medium">Loading teachers list...</p>
        </div>
      )}

      {isError && (
        <div className="flex flex-col items-center justify-center py-12 px-4 bg-red-50/50 rounded-xl border border-red-100 text-center">
          <AlertCircle className="w-10 h-10 text-red-500 mb-3" />
          <h3 className="text-base font-semibold text-red-900">Failed to load data</h3>
          <p className="text-sm text-red-600 mt-1 max-w-md">
            {(error as any)?.message || "Connection error with backend."}
          </p>
        </div>
      )}

      {!isLoading && !isError && (!teachers || teachers.length === 0) && (
        <div className="flex flex-col items-center justify-center py-20 bg-white rounded-xl border border-dashed border-slate-300 text-center">
          <div className="p-3 bg-slate-50 rounded-full text-slate-400 mb-4">
            <GraduationCap className="w-8 h-8" />
          </div>
          <h3 className="text-base font-semibold text-slate-900">Teacherlar Topilmadi</h3>
          <p className="text-sm text-slate-500 mt-1 max-w-xs">Hozircha tizimga hech qanday teacher ma'lumotlari kiritilmagan.</p>
          <button
            onClick={() => setIsAddOpen(true)}
            className="mt-4 inline-flex items-center gap-2 h-9 px-4 bg-white border border-slate-200 text-slate-700 rounded-lg text-xs font-semibold shadow-sm hover:bg-slate-50 transition-all cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5" /> Add Teacher
          </button>
        </div>
      )}

      {/* Table */}
      {!isLoading && !isError && teachers && teachers.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-100 text-slate-600 text-xs font-semibold uppercase tracking-wider">
                  <th className="py-3.5 px-5">Teacher Details</th>
                  <th className="py-3.5 px-5">Contact Info</th>
                  <th className="py-3.5 px-5">Specialization / Experience</th>
                  <th className="py-3.5 px-5">Learning Center</th>
                  <th className="py-3.5 px-5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-sm text-slate-700">
                {teachers.map((teacher) => {
                  const initial = (teacher.full_name || "N").charAt(0).toUpperCase();

                  {
                    console.log(teacher);
                  }


                  return (
                    <tr key={teacher.id} className="hover:bg-slate-50/50 transition-colors group">
                      <td className="py-4 px-5">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center overflow-hidden shrink-0">
                            {teacher.avatar ? (
                              <img src={teacher.avatar} alt={teacher.full_name} className="w-full h-full object-cover" />
                            ) : (
                              <span className="font-semibold text-slate-500 text-sm">{initial}</span>
                            )}
                          </div>
                          <div>
                            <div className="font-semibold text-slate-900 leading-tight">{teacher.full_name}</div>
                            <div className="text-[11px] text-slate-400 mt-0.5">ID: {teacher.id.slice(0, 8)}</div>
                          </div>
                        </div>
                      </td>

                      <td className="py-4 px-5">
                        <div className="space-y-1 text-xs">
                          <div className="flex items-center gap-2 text-slate-600">
                            <Phone className="w-3.5 h-3.5 text-slate-400" />
                            <span>{formatPhoneView(teacher.phone)}</span>
                          </div>
                          <div className="flex items-center gap-2 text-slate-600">
                            <Mail className="w-3.5 h-3.5 text-slate-400" />
                            <span className="truncate max-w-[160px]">{teacher.email}</span>
                          </div>
                        </div>
                      </td>

                      <td className="py-4 px-5">
                        <div className="space-y-1 text-xs">
                          <div className="flex items-center gap-1.5 text-slate-700 font-medium">
                            <Briefcase className="w-3.5 h-3.5 text-slate-400" />
                            <span>{teacher.specialization || "—"}</span>
                          </div>
                          <div className="flex items-center gap-1.5 text-slate-500">
                            <Star className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
                            <span>{teacher.experience} years exp</span>
                          </div>
                        </div>
                      </td>

                      <td className="py-4 px-5">
                        <div className="flex items-center gap-1.5 text-xs text-slate-600 max-w-[180px]">
                          <Building2 className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                          <span className="truncate">{teacher.center_name || "—"}</span>
                        </div>
                      </td>

                      <td className="py-4 px-5 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => setEditingTeacher(teacher)}
                            className="inline-flex items-center justify-center w-8 h-8 rounded-lg text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 border border-transparent hover:border-indigo-100 transition-all cursor-pointer"
                            title="Edit"
                          >
                            <Edit3 className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => setDeletingTeacher(teacher)} // Eski handleDelete o'rniga stateni yangilaymiz
                            className="inline-flex items-center justify-center w-8 h-8 rounded-lg text-slate-400 hover:text-red-600 hover:bg-red-50 border border-transparent hover:border-red-100 transition-all cursor-pointer"
                            title="Delete"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {isAddOpen && <AddTeacherModal onClose={() => setIsAddOpen(false)} />}

      {editingTeacher && (
        <EditTeacherModal
          teacher={editingTeacher}
          onClose={() => setEditingTeacher(null)}
        />
      )}

      {deletingTeacher && (
        <DeleteTeacherModal
          teacherName={deletingTeacher.full_name}
          isPending={isDeletePending}
          onConfirm={() => deleteTeacher(deletingTeacher.id)}
          onClose={() => setDeletingTeacher(null)}
        />
      )}
    </div>
  );
}