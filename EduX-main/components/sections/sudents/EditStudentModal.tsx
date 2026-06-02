"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { API } from "@/services/api";
import { toast } from "react-toastify";
import { useForm } from "react-hook-form";
import { X, Loader2 } from "lucide-react";
import { IStudent } from "./StudentItem";

interface EditStudentModalProps {
    student: IStudent;
    onClose: () => void;
}

interface IEditStudentPayload {
    first_name: string;
    last_name: string;
    phone: string;
    email: string;
    center: string;
    date_of_birth: string;
    address: string;
    notes?: string;
    status: "active" | "inactive" | "pending";
}

export default function EditStudentModal({ student, onClose }: EditStudentModalProps) {
    const queryClient = useQueryClient();

    // Ism familiyani ajratish
    const nameParts = student.full_name ? student.full_name.split(" ") : [];
    const defaultFirstName = student.first_name || nameParts[0] || "";
    const defaultLastName = student.last_name || nameParts.slice(1).join(" ") || "";

    // Telefon raqamni vizual chiroyli ko'rsatish funksiyasi
    const formatPhone = (phone: string) => {
        const clean = phone.replace(/\D/g, "");
        if (clean.length === 12) {
            return `+998 (${clean.slice(3, 5)}) ${clean.slice(5, 8)}-${clean.slice(8, 10)}-${clean.slice(10)}`;
        }
        return phone;
    };

    const {
        register,
        handleSubmit,
        formState: { errors },
    } = useForm<IEditStudentPayload>({
        defaultValues: {
            first_name: defaultFirstName,
            last_name: defaultLastName,
            phone: student.phone || "",
            email: student.email || "",
            center: "a8c590b8-2b54-4e94-bbe4-0bb006093ecd",
            date_of_birth: student.date_of_birth || "",
            address: student.address || "",
            status: student.status || "active",
            notes: "",
        },
    });

    const { mutate: updateStudent, isPending } = useMutation({
        mutationFn: async (payload: IEditStudentPayload) => {
            return await API.put(`/api/v1/students/${student.id}/`, payload);
        },
        onSuccess: () => {
            toast.success("Talaba ma'lumotlari muvaffaqiyatli yangilandi");
            queryClient.invalidateQueries({ queryKey: ["students"] });
            onClose();
        },
        onError: (err: any) => {
            toast.error(err?.response?.data?.message || "Yangilashda xatolik yuz berdi");
        },
    });

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs animate-in fade-in duration-150">
            <div className="w-full max-w-2xl bg-white rounded-xl shadow-xl overflow-hidden animate-in zoom-in-95 duration-150">

                {/* Modal Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/50">
                    <div>
                        <h3 className="text-base font-semibold text-slate-900">Talaba ma'lumotlarini tahrirlash</h3>
                        <p className="text-xs text-slate-400 mt-0.5">Tizimdagi ma'lumotlarni yangilash</p>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors cursor-pointer"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                <form onSubmit={handleSubmit((data) => updateStudent(data))} className="p-6 space-y-5">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                        {/* First Name */}
                        <div>
                            <label className="block text-xs font-semibold text-slate-600 uppercase mb-1.5 tracking-wider">Ism</label>
                            <input
                                type="text"
                                {...register("first_name", { required: "Ism kiritilishi shart" })}
                                className="w-full h-11 px-3.5 text-sm bg-white border border-slate-200 rounded-lg focus:outline-hidden focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all text-slate-800 shadow-xs"
                                placeholder="John"
                            />
                            {errors.first_name && <p className="text-[11px] text-red-500 mt-1">{errors.first_name.message}</p>}
                        </div>

                        {/* Last Name */}
                        <div>
                            <label className="block text-xs font-semibold text-slate-600 uppercase mb-1.5 tracking-wider">Familiya</label>
                            <input
                                type="text"
                                {...register("last_name", { required: "Familiya kiritilishi shart" })}
                                className="w-full h-11 px-3.5 text-sm bg-white border border-slate-200 rounded-lg focus:outline-hidden focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all text-slate-800 shadow-xs"
                                placeholder="Doe"
                            />
                            {errors.last_name && <p className="text-[11px] text-red-500 mt-1">{errors.last_name.message}</p>}
                        </div>

                        {/* Phone Number - Add modal ko'rinishida lekin disabled */}
                        <div>
                            <label className="block text-xs font-semibold text-slate-400 uppercase mb-1.5 tracking-wider">Telefon raqam</label>
                            <input
                                type="text"
                                disabled
                                value={formatPhone(student.phone)}
                                className="w-full h-11 px-3.5 text-sm bg-slate-50 border border-slate-200 rounded-lg text-slate-400 cursor-not-allowed font-medium shadow-xs"
                            />
                        </div>

                        {/* Email */}
                        <div>
                            <label className="block text-xs font-semibold text-slate-600 uppercase mb-1.5 tracking-wider">Email</label>
                            <input
                                type="email"
                                {...register("email", { required: "Email manzili shart" })}
                                className="w-full h-11 px-3.5 text-sm bg-white border border-slate-200 rounded-lg focus:outline-hidden focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all text-slate-800 shadow-xs"
                                placeholder="user@example.com"
                            />
                            {errors.email && <p className="text-[11px] text-red-500 mt-1">{errors.email.message}</p>}
                        </div>

                        {/* Status */}
                        <div>
                            <label className="block text-xs font-semibold text-slate-600 uppercase mb-1.5 tracking-wider">Status</label>
                            <select
                                {...register("status")}
                                className="w-full h-11 px-3.5 text-sm bg-white border border-slate-200 rounded-lg focus:outline-hidden focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all text-slate-800 cursor-pointer shadow-xs"
                            >
                                <option value="active">Active</option>
                                <option value="inactive">Inactive</option>
                                <option value="pending">Pending</option>
                            </select>
                        </div>

                        {/* Date of Birth */}
                        <div>
                            <label className="block text-xs font-semibold text-slate-600 uppercase mb-1.5 tracking-wider">Tug'ilgan sana</label>
                            <input
                                type="date"
                                {...register("date_of_birth")}
                                className="w-full h-11 px-3.5 text-sm bg-white border border-slate-200 rounded-lg focus:outline-hidden focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all text-slate-800 shadow-xs"
                            />
                        </div>
                    </div>

                    {/* Address */}
                    <div>
                        <label className="block text-xs font-semibold text-slate-600 uppercase mb-1.5 tracking-wider">Manzil</label>
                        <input
                            type="text"
                            {...register("address")}
                            className="w-full h-11 px-3.5 text-sm bg-white border border-slate-200 rounded-lg focus:outline-hidden focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all text-slate-800 shadow-xs"
                            placeholder="Toshkent sh., Yunusobod d-7"
                        />
                    </div>

                    {/* Notes */}
                    <div>
                        <label className="block text-xs font-semibold text-slate-600 uppercase mb-1.5 tracking-wider">Eslatmalar (Notes)</label>
                        <textarea
                            rows={3}
                            {...register("notes")}
                            className="w-full p-3.5 text-sm bg-white border border-slate-200 rounded-lg focus:outline-hidden focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all text-slate-800 resize-none shadow-xs"
                            placeholder="Qo'shimcha ma'lumotlar..."
                        />
                    </div>

                    {/* Modal Footer - Add Modal bilan 1:1 bir xil kulrang blokli o'ram */}
                    <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100 bg-slate-50/50 -mx-6 -mb-6 p-6">
                        <button
                            type="button"
                            onClick={onClose}
                            disabled={isPending}
                            className="h-10 px-4 text-xs font-semibold text-slate-700 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors cursor-pointer disabled:opacity-50 shadow-xs"
                        >
                            Bekor qilish
                        </button>
                        <button
                            type="submit"
                            disabled={isPending}
                            className="inline-flex items-center justify-center gap-2 h-10 px-5 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors cursor-pointer disabled:opacity-70 min-w-[120px] shadow-sm"
                        >
                            {isPending ? (
                                <>
                                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                                    Saqlanmoqda...
                                </>
                            ) : (
                                "Saqlash"
                            )}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}