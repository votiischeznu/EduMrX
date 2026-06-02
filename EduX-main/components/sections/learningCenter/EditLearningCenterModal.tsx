"use client";

import { useState, useEffect, useRef } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { API } from "@/services/api";
import { ILearningCenter } from "@/types";
import { X, Loader2, Building2, Upload } from "lucide-react";
import { toast } from "react-toastify";

interface EditModalProps {
    center: ILearningCenter;
    onClose: () => void;
}

export default function EditLearningCenterModal({ center, onClose }: EditModalProps) {
    const queryClient = useQueryClient();
    const fileInputRef = useRef<HTMLInputElement>(null);

    // State o'zgaruvchilari
    const [formData, setFormData] = useState({
        name: "",
        slug: "",
        phone: "",
        email: "",
        address: "",
        director: "",
        status: "active",
        subscription_expires: ""
    });

    // Tanlangan yangi fayl yoki mavjud logotipning eski URL manzili uchun alohida statelar
    const [logoFile, setLogoFile] = useState<File | null>(null);
    const [logoPreview, setLogoPreview] = useState<string>("");

    // Telefon raqamini real vaqtda formatlash maskasi
    const formatPhoneInput = (value: string) => {
        const digits = value.replace(/\D/g, "");
        if (!digits.startsWith("998")) {
            return "+998 ";
        }

        let formatted = "+998 ";
        if (digits.length > 3) formatted += `(${digits.slice(3, 5)}`;
        if (digits.length > 5) formatted += `) ${digits.slice(5, 8)}`;
        if (digits.length > 8) formatted += `-${digits.slice(8, 10)}`;
        if (digits.length > 10) formatted += `-${digits.slice(10, 12)}`;

        return formatted.trim();
    };

    // Komponent yuklanganda eski ma'lumotlarni formaga to'ldirish
    useEffect(() => {
        if (center) {
            setFormData({
                name: center.name || "",
                slug: center.slug || "",
                phone: center.phone ? formatPhoneInput(center.phone) : "+998 ",
                email: center.email || "",
                address: center.address || "",
                director: (center as any).director || "",
                status: center.status || "active",
                subscription_expires: center.subscription_expires ? center.subscription_expires.split("T")[0] : ""
            });
            // Agar backenddan eski rasm URL kelgan bo'lsa, uni ko'rsatib turamiz
            setLogoPreview(center.logo || "");
        }
    }, [center]);

    // Rasm tanlanganda ishga tushadigan funksiya
    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            setLogoFile(file);
            // Tanlangan rasmni ssenariyda vaqtinchalik ko'rish (Preview) uchun URL generatsiya qilish
            setLogoPreview(URL.createObjectURL(file));
        }
    };

    // Mutatsiya - Multipart/Form-Data ko'rinishida jo'natish
    const { mutate: updateCenter, isPending } = useMutation({
        mutationFn: async () => {
            // CRITICAL: Rasmlar bilan ishlash uchun FormData yaratamiz
            const data = new FormData();

            data.append("name", formData.name);
            data.append("slug", formData.slug);
            data.append("phone", formData.phone.replace(/\D/g, "")); // Toza raqam
            data.append("email", formData.email);
            data.append("address", formData.address);
            data.append("director", formData.director);
            data.append("status", formData.status);
            data.append("subscription_expires", formData.subscription_expires);

            // Agar foydalanuvchi yangi rasm tanlagan bo'lsa, faylni yuklaymiz
            if (logoFile) {
                data.append("logo", logoFile);
            }

            // API so'rovi headers qismida multipart/form-data ekanini ko'rsatish shart emas, 
            // brauzer FormData obyektini ko'rib o'zi avtomat qo'shib oladi.
            await API.put(`/api/v1/super-admin/centers/${center.id}/`, data);
        },
        onSuccess: () => {
            toast.success("O'quv markazi muvaffaqiyatli yangilandi!");
            queryClient.invalidateQueries({ queryKey: ["learning-centers"] });
            onClose();
        },
        onError: (err: any) => {
            toast.error(err?.response?.data?.message || err?.message || "Yangilashda xatolik yuz berdi");
        }
    });

    const handlePhoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const inputVal = e.target.value;
        if (inputVal.length < 5) {
            setFormData({ ...formData, phone: "+998 " });
            return;
        }
        setFormData({ ...formData, phone: formatPhoneInput(inputVal) });
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        updateCenter();
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs animate-fade-in">
            <div className="absolute inset-0" onClick={onClose} />

            <div className="relative bg-white w-full max-w-lg rounded-xl shadow-xl border border-slate-100 overflow-hidden z-10">

                {/* Header */}
                <div className="flex items-center justify-between p-5 border-b border-slate-100 bg-slate-50/50">
                    <div>
                        <h3 className="text-lg font-semibold text-slate-900">O'quv markazini tahrirlash</h3>
                        <p className="text-xs text-slate-500 mt-0.5">Markaz sozlamalari va ma'lumotlarini yangilash</p>
                    </div>
                    <button type="button" onClick={onClose} className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-all cursor-pointer">
                        <X className="w-4 h-4" />
                    </button>
                </div>

                {/* Body Form */}
                <form onSubmit={handleSubmit} className="p-5 space-y-4">

                    {/* LOGO UPLOAD COMPONENT (Add Learning Center bilan bir xil dizayn va logika) */}
                    <div className="space-y-1.5">
                        <label className="text-xs font-semibold text-slate-700 block">Markaz logotipi</label>
                        <div className="flex items-center gap-4 p-4 bg-slate-50 border border-dashed border-slate-300 rounded-xl">
                            {/* Preview Box */}
                            <div className="w-16 h-16 rounded-xl bg-white border border-slate-200 flex items-center justify-center overflow-hidden shrink-0 shadow-xs">
                                {logoPreview ? (
                                    // eslint-disable-next-line @next/next/no-img-element
                                    <img src={logoPreview} alt="Logo" className="w-full h-full object-cover" />
                                ) : (
                                    <Building2 className="w-6 h-6 text-slate-400" />
                                )}
                            </div>

                            {/* Upload Trigger Button */}
                            <div className="flex flex-col items-start gap-1">
                                <input
                                    type="file"
                                    ref={fileInputRef}
                                    onChange={handleFileChange}
                                    accept="image/*"
                                    className="hidden"
                                />
                                <button
                                    type="button"
                                    onClick={() => fileInputRef.current?.click()}
                                    className="inline-flex items-center gap-2 h-9 px-3 bg-white border border-slate-200 hover:border-slate-300 text-slate-700 text-xs font-semibold rounded-lg shadow-xs hover:bg-slate-50 transition-all cursor-pointer"
                                >
                                    <Upload className="w-3.5 h-3.5 text-slate-500" />
                                    Yangi rasm tanlash
                                </button>
                                <span className="text-[10px] text-slate-400 font-medium">
                                    Tavsiya etiladi: Kvadrat shaklidagi PNG, JPG (Maks. 2MB)
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* 2 Ustun: Nomi va Slug */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div className="space-y-1.5">
                            <label className="text-xs font-semibold text-slate-700 block">Markaz nomi *</label>
                            <input
                                type="text"
                                value={formData.name}
                                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                className="w-full h-10 px-3 text-sm bg-white border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 transition-all text-slate-800"
                                required
                            />
                        </div>
                        <div className="space-y-1.5">
                            <label className="text-xs font-semibold text-slate-700 block">Slug (Tizimli manzil) *</label>
                            <input
                                type="text"
                                value={formData.slug}
                                onChange={(e) => setFormData({ ...formData, slug: e.target.value.toLowerCase().replace(/\s+/g, "-") })}
                                className="w-full h-10 px-3 text-sm bg-white border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 transition-all text-slate-800 font-mono"
                                required
                            />
                        </div>
                    </div>

                    {/* 2 Ustun: Telefon va Email */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div className="space-y-1.5">
                            <label className="text-xs font-semibold text-slate-700 block">Telefon raqami *</label>
                            <input
                                type="tel"
                                value={formData.phone}
                                onChange={handlePhoneChange}
                                placeholder="+998 (90) 123-45-67"
                                maxLength={19}
                                className="w-full h-10 px-3 text-sm bg-white border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 transition-all text-slate-800 font-medium"
                                required
                            />
                        </div>
                        <div className="space-y-1.5">
                            <label className="text-xs font-semibold text-slate-700 block">Email pochta *</label>
                            <input
                                type="email"
                                value={formData.email}
                                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                                className="w-full h-10 px-3 text-sm bg-white border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 transition-all text-slate-800"
                                required
                            />
                        </div>
                    </div>

                    {/* Manzil */}
                    <div className="space-y-1.5">
                        <label className="text-xs font-semibold text-slate-700 block">O'quv markazi manzili *</label>
                        <input
                            type="text"
                            value={formData.address}
                            onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                            className="w-full h-10 px-3 text-sm bg-white border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 transition-all text-slate-800"
                            required
                        />
                    </div>

                    {/* 2 Ustun: Status va Obuna muddati */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div className="space-y-1.5">
                            <label className="text-xs font-semibold text-slate-700 block">Status *</label>
                            <select
                                value={formData.status}
                                onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                                className="w-full h-10 px-3 text-sm bg-white border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 transition-all text-slate-800 cursor-pointer"
                            >
                                <option value="active">Active</option>
                                <option value="pending">Pending</option>
                                <option value="inactive">Inactive</option>
                            </select>
                        </div>
                        <div className="space-y-1.5">
                            <label className="text-xs font-semibold text-slate-700 block">Obuna tugash sanasi *</label>
                            <input
                                type="date"
                                value={formData.subscription_expires}
                                onChange={(e) => setFormData({ ...formData, subscription_expires: e.target.value })}
                                className="w-full h-10 px-3 text-sm bg-white border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 transition-all text-slate-800"
                                required
                            />
                        </div>
                    </div>

                    {/* Footer tugmalari */}
                    <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100 mt-6">
                        <button type="button" onClick={onClose} className="h-10 px-4 border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 text-sm font-semibold rounded-lg shadow-xs cursor-pointer transition-colors">
                            Bekor qilish
                        </button>
                        <button type="submit" disabled={isPending} className="inline-flex items-center justify-center gap-2 h-10 px-5 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold rounded-lg shadow-xs disabled:bg-indigo-400 cursor-pointer transition-colors">
                            {isPending ? (
                                <>
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    <span>Saqlanmoqda...</span>
                                </>
                            ) : (
                                "O'zgarishlarni saqlash"
                            )}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}