"use client";

import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { yupResolver } from "@hookform/resolvers/yup";
import * as yup from "yup";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { API } from "@/services/api";
import { ShieldAlert, X, Eye, EyeOff, Loader2 } from "lucide-react";
import { toast } from "react-toastify";
import { IDirector } from "./DirectorItem";

function formatUzPhone(raw: string): string {
    const d = raw.slice(0, 9);
    if (d.length <= 2) return d;
    if (d.length <= 5) return `${d.slice(0, 2)}-${d.slice(2, 5)}`;
    if (d.length <= 7) return `${d.slice(0, 2)}-${d.slice(2, 5)}-${d.slice(5, 7)}`;
    return `${d.slice(0, 2)}-${d.slice(2, 5)}-${d.slice(5, 7)}-${d.slice(7)}`;
}

const schema = yup.object({
    first_name: yup.string().required("Ism kiritilishi shart"),
    last_name: yup.string().required("Familiya kiritilishi shart"),
    phone: yup
        .string()
        .required("Telefon raqami majburiy")
        .test("phone-complete", "Raqamni to'liq kiriting", (val) => {
            const digits = val?.replace(/\D/g, "") ?? "";
            return digits.length === 12;
        }),
    email: yup.string().email("Xato email formati").required("Email kiritilishi shart"),
    password: yup.string().required("Tahrirlash uchun yangi parol kiritishingiz shart").min(6, "Parol kamida 6 ta belgi bo'lishi kerak")
}).required();

type FormData = yup.InferType<typeof schema>;

export default function EditDirectorModal({ director, onClose }: { director: IDirector; onClose?: () => void }) {
    const queryClient = useQueryClient();
    const [isMounted, setIsMounted] = useState(false);
    const [phoneDisplay, setPhoneDisplay] = useState("");
    const [showPassword, setShowPassword] = useState(false);

    const {
        register,
        handleSubmit,
        setValue,
        setError,
        formState: { errors },
    } = useForm<FormData>({
        resolver: yupResolver(schema)
    });

    useEffect(() => {
        setIsMounted(true);
        if (director) {
            const nameParts = director.full_name ? director.full_name.trim().split(" ") : [];
            const firstName = nameParts[0] || "";
            const lastName = nameParts.slice(1).join(" ") || "";

            setValue("first_name", firstName);
            setValue("last_name", lastName);
            setValue("email", director.email);

            // Telefon raqamini o'rnatish
            const rawPhone = director.phone ? director.phone.replace(/\D/g, "") : "";
            const localPart = rawPhone.startsWith("998") ? rawPhone.slice(3) : rawPhone;
            setPhoneDisplay(formatUzPhone(localPart));
            setValue("phone", "998" + localPart);
            setValue("password", ""); // Xavfsizlik sababli bo'sh turadi, kiritish majburiy
        }
    }, [director, setValue]);

    const { mutate: updateDirector, isPending } = useMutation({
        mutationFn: async (body: FormData) => {
            const payload = {
                ...body,
                phone: body.phone.replace(/\D/g, "")
            };
            const res = await API.put(`/api/v1/super-admin/directors/${director.id}/`, payload);
            return res.data;
        },
        onSuccess: () => {
            toast.success("Director muvaffaqiyatli yangilandi!");
            queryClient.invalidateQueries({ queryKey: ["directors"] });
            onClose?.();
        },
        onError: (err: any) => {
            const serverErrors = err?.response?.data;
            if (serverErrors && typeof serverErrors === "object") {
                const firstKey = Object.keys(serverErrors)[0];
                const errorValue = serverErrors[firstKey];
                if (Array.isArray(errorValue) && errorValue.length > 0) {
                    toast.error(`${errorValue[0]}`);
                    setError(firstKey as any, { type: "server", message: errorValue[0] });
                    return;
                }
            }
            toast.error(serverErrors?.message || err?.message || "Xatolik yuz berdi.");
        }
    });

    const handlePhoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const raw = e.target.value.replace(/\D/g, "");
        const withPrefix = raw.startsWith("998") ? raw : "998" + raw.replace(/^998/, "");
        const local = withPrefix.slice(3, 12);
        setPhoneDisplay(formatUzPhone(local));
        const full = "998" + local;
        setValue("phone", full, { shouldValidate: true });
    };

    const onSubmit = (data: FormData) => {
        updateDirector(data);
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div className={`fixed inset-0 bg-slate-900/40 backdrop-blur-sm transition-opacity duration-500 ${isMounted ? "opacity-100" : "opacity-0"}`} onClick={onClose} />

            <div className={`bg-white p-6 rounded-xl max-w-xl w-full max-h-[90vh] overflow-y-auto relative z-10 shadow-2xl border border-slate-100 transform transition-all duration-500 ease-out scrollbar-thin scrollbar-thumb-slate-200 ${isMounted ? "opacity-100 translate-y-0 scale-100" : "opacity-0 -translate-y-12 scale-95"}`}>

                {onClose && (
                    <button type="button" onClick={onClose} className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-50 cursor-pointer">
                        <X className="w-5 h-5" />
                    </button>
                )}

                <div className="mb-[10px] border-[#C7C4D8] border shadow-sm w-[44px] h-[44px] rounded-lg flex justify-center items-center text-indigo-600 bg-indigo-50/10">
                    <ShieldAlert className="w-6 h-6" />
                </div>

                <h3 className="text-[#313131] text-[18px] font-semibold mb-4">Edit Director Details</h3>

                <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                    {/* First Name & Last Name */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="text-[14px] text-[#464555] mb-1 block font-semibold">First Name</label>
                            <input {...register("first_name")} type="text" placeholder="First name" className={`border rounded-lg w-full h-[40px] px-3 text-[14px] outline-none transition-all focus:border-indigo-500 ${errors.first_name ? "border-red-300 bg-red-50/10" : "border-[#C7C4D8]"}`} />
                            {errors.first_name && <p className="text-red-400 text-[11px] mt-1">{errors.first_name.message}</p>}
                        </div>
                        <div>
                            <label className="text-[14px] text-[#464555] mb-1 block font-semibold">Last Name</label>
                            <input {...register("last_name")} type="text" placeholder="Last name" className={`border rounded-lg w-full h-[40px] px-3 text-[14px] outline-none transition-all focus:border-indigo-500 ${errors.last_name ? "border-red-300 bg-red-50/10" : "border-[#C7C4D8]"}`} />
                            {errors.last_name && <p className="text-red-400 text-[11px] mt-1">{errors.last_name.message}</p>}
                        </div>
                    </div>

                    {/* Phone & Email */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="text-[14px] text-[#464555] mb-1 block font-semibold">Phone</label>
                            <div className="relative flex items-center">
                                <div className="absolute left-3 flex items-center gap-1.5 select-none pointer-events-none">
                                    <span className="text-base leading-none">🇺🇿</span><span className="text-sm font-semibold text-[#191C1D]">+998</span>
                                </div>
                                <input type="tel" value={phoneDisplay} onChange={handlePhoneChange} placeholder="90-123-45-67" className={`border rounded-lg w-full h-[40px] pl-[90px] pr-[10px] text-[14px] outline-none transition-all focus:border-indigo-500 ${errors.phone ? "border-red-300 bg-red-50/10" : "border-[#C7C4D8]"}`} />
                            </div>
                            {errors.phone && <p className="text-red-400 text-[11px] mt-1 ml-2">{errors.phone.message}</p>}
                        </div>
                        <div>
                            <label className="text-[14px] text-[#464555] mb-1 block font-semibold">Email Address</label>
                            <input {...register("email")} type="email" placeholder="email@example.com" className={`border rounded-lg w-full h-[40px] px-3 text-[14px] outline-none transition-all focus:border-indigo-500 ${errors.email ? "border-red-300 bg-red-50/10" : "border-[#C7C4D8]"}`} />
                            {errors.email && <p className="text-red-400 text-[11px] mt-1">{errors.email.message}</p>}
                        </div>
                    </div>

                    {/* Password */}
                    <div>
                        <label className="text-[14px] text-[#464555] mb-1 block font-semibold">New Password (Required)</label>
                        <div className="relative flex items-center">
                            <input {...register("password")} type={showPassword ? "text" : "password"} placeholder="Enter new password to save updates" className={`border rounded-lg w-full h-[40px] pl-3 pr-10 text-[14px] outline-none transition-all focus:border-indigo-500 ${errors.password ? "border-red-300 bg-red-50/10" : "border-[#C7C4D8]"}`} />
                            <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 text-slate-400 hover:text-slate-600 focus:outline-none cursor-pointer">
                                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                            </button>
                        </div>
                        {errors.password && <p className="text-red-400 text-[11px] mt-1">{errors.password.message}</p>}
                    </div>

                    {/* Submit Button */}
                    <button type="submit" disabled={isPending} className="w-full h-[40px] mt-2 bg-[#4F46E5] hover:bg-[#4338CA] disabled:bg-indigo-300 text-white rounded-lg text-[14px] font-bold transition-colors cursor-pointer flex items-center justify-center">
                        {isPending ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                        {isPending ? "Saving Updates..." : "Save Updates"}
                    </button>
                </form>
            </div>
        </div>
    );
}