"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { API } from "@/services/api";
import { LayoutGrid, List, Plus, Loader2, AlertCircle, User, ChevronLeft, ChevronRight, Search } from "lucide-react";
import Title from "@/components/ui/Title";
import Text from "@/components/ui/Text";
import DeleteDirectorModal from "@/components/sections/director/DeleteDirectorModal";
import DirectorItem from "@/components/sections/director/DirectorItem";
import AddDirectorModal from "@/components/sections/director/addDirectorModal";
import EditDirectorModal from "@/components/sections/director/EditDirectorModal";
import { IAPIResponse, IDirector } from "@/types";

export default function DirectorsList() {
    const [viewMode, setViewMode] = useState<"list" | "grid">("list");
    const [page, setPage] = useState(1);
    const [search, setSearch] = useState("");

    const [isAddOpen, setIsAddOpen] = useState(false);
    const [editTarget, setEditTarget] = useState<IDirector | null>(null);
    const [deleteTarget, setDeleteTarget] = useState<{ id: string; name: string } | null>(null);

    const { data, isLoading, isError, error } = useQuery<IAPIResponse<IDirector[]>>({
        queryKey: ["directors", page, search],
        queryFn: async () => {
            const res = await API.get(`/api/v1/super-admin/directors/?page=${page}&search=${search}`);
            return res?.data;
        }
    });

    console.log("directors", data);


    const directors = data?.results || [];
    const totalPages = data?.total_pages || 1;

    const formatPhoneView = (phone: string) => {
        const clean = phone?.replace(/\D/g, "") || "";
        if (clean.length === 12) {
            return `+998 (${clean.slice(3, 5)}) ${clean.slice(5, 8)}-${clean.slice(8, 10)}-${clean.slice(10)}`;
        }
        return phone ? `+${phone}` : "—";
    };

    return (
        <div className="w-full space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                    <Title text="Directors Management" />
                    <Text text="Tizimdagi barcha o'quv markazi direktorlarini boshqarish va tahrirlash." />
                </div>
                <button
                    onClick={() => setIsAddOpen(true)}
                    className="inline-flex items-center justify-center gap-2 h-10 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm rounded-lg shadow-xs cursor-pointer self-start sm:self-auto transition-colors"
                >
                    <Plus className="w-4 h-4" /> Add Director
                </button>
            </div>



            {/* Yuklanish holatlari */}
            {isLoading && (
                <div className="flex flex-col items-center justify-center py-24 bg-white rounded-xl border border-slate-100">
                    <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
                </div>
            )}

            {isError && (
                <div className="flex flex-col items-center justify-center py-12 bg-red-50/50 rounded-xl border border-red-100 text-center">
                    <AlertCircle className="w-10 h-10 text-red-500 mb-2" />
                    <p className="text-sm text-red-600">{(error as any)?.message || "Ma'lumot yuklashda xatolik yuz berdi"}</p>
                </div>
            )}

            {/* Empty State */}
            {!isLoading && !isError && directors.length === 0 && (
                <div className="flex flex-col items-center justify-center py-20 bg-white rounded-xl border border-dashed border-slate-300 text-center min-h-[380px]">
                    <div className="w-14 h-14 bg-slate-50 border border-slate-100 rounded-full flex items-center justify-center text-slate-400 mb-4 shadow-xs">
                        <User className="w-7 h-7" />
                    </div>
                    <h3 className="text-base font-semibold text-slate-900">Direktorlar topilmadi</h3>
                    <p className="text-xs text-slate-500 mt-1 max-w-xs">Hozircha tizimga hech qanday direktor ma'lumotlari kiritilmagan.</p>

                    <button
                        onClick={() => setIsAddOpen(true)}
                        className="mt-4 inline-flex items-center gap-2 h-9 px-4 bg-white border border-slate-200 text-slate-700 rounded-lg text-xs font-semibold shadow-sm hover:bg-slate-50 transition-all cursor-pointer"
                    >
                        <Plus className="w-3.5 h-3.5" /> Direktor qo'shish
                    </button>
                </div>
            )}

            {/* Ma'lumot bor holatda jadval / karta */}
            {!isLoading && !isError && directors.length > 0 && (
                <>
                    {viewMode === "list" ? (
                        <div className="bg-white rounded-xl shadow-xs border border-slate-100 overflow-hidden">
                            <div className="overflow-x-auto">
                                <table className="w-full text-left border-collapse">
                                    <thead>
                                        <tr className="bg-slate-50 border-b border-slate-100 text-slate-500 text-[11px] font-bold uppercase tracking-wider">
                                            <th className="py-3 px-5">Director Details</th>
                                            <th className="py-3 px-5">Contact</th>
                                            <th className="py-3 px-5">Created At</th>
                                            <th className="py-3 px-5 text-right">Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-100 text-sm">
                                        {directors.map((director) => (
                                            <DirectorItem
                                                key={director.id}
                                                director={director}
                                                viewMode="list"
                                                onEdit={(d) => setEditTarget(d)}
                                                onDelete={(id, name) => setDeleteTarget({ id, name })}
                                                formatPhone={formatPhoneView}
                                            />
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
                            {directors.map((director) => (
                                <DirectorItem
                                    key={director.id}
                                    director={director}
                                    viewMode="grid"
                                    onEdit={(d) => setEditTarget(d)}
                                    onDelete={(id, name) => setDeleteTarget({ id, name })}
                                    formatPhone={formatPhoneView}
                                />
                            ))}
                        </div>
                    )}

                    {/* Pagination bar */}
                    {totalPages > 1 && (
                        <div className="flex items-center justify-between pt-4 border-t border-slate-100">
                            <span className="text-xs text-slate-500">Sahifa {page} / {totalPages}</span>
                            <div className="flex items-center gap-2">
                                <button onClick={() => setPage((p) => Math.max(p - 1, 1))} disabled={page === 1} className="w-9 h-9 border rounded-lg flex items-center justify-center bg-white cursor-pointer disabled:opacity-50">
                                    <ChevronLeft className="w-4 h-4" />
                                </button>
                                <button onClick={() => setPage((p) => Math.min(p + 1, totalPages))} disabled={page === totalPages} className="w-9 h-9 border rounded-lg flex items-center justify-center bg-white cursor-pointer disabled:opacity-50">
                                    <ChevronRight className="w-4 h-4" />
                                </button>
                            </div>
                        </div>
                    )}
                </>
            )}

            {/* Modallarni ulash */}
            {isAddOpen && <AddDirectorModal onClose={() => setIsAddOpen(false)} />}
            {editTarget && <EditDirectorModal director={editTarget} onClose={() => setEditTarget(null)} />}
            {deleteTarget && (
                <DeleteDirectorModal id={deleteTarget.id} name={deleteTarget.name} onClose={() => setDeleteTarget(null)} />
            )}
        </div>
    );
}