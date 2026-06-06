"use client";

import { useState, useEffect, useRef } from "react";
import { useForm } from "react-hook-form";
import { yupResolver } from "@hookform/resolvers/yup";
import * as yup from "yup";
import { useMutation, useQueryClient, useQuery } from "@tanstack/react-query";
import { API } from "@/services/api";
import { GraduationCap, X, Search, ChevronDown, Eye, EyeOff } from "lucide-react";
import { toast } from "react-toastify";

// Telefon raqamni vizual formatlash (90-123-45-67)
function formatUzPhone(raw: string): string {
    const d = raw.slice(0, 9);
    if (d.length <= 2) return d;
    if (d.length <= 5) return `${d.slice(0, 2)}-${d.slice(2, 5)}`;
    if (d.length <= 7) return `${d.slice(0, 2)}-${d.slice(2, 5)}-${d.slice(5, 7)}`;
    return `${d.slice(0, 2)}-${d.slice(2, 5)}-${d.slice(5, 7)}-${d.slice(7)}`;
}

// Barcha maydonlar uchun qat'iy Yup sxemasi (Required)
const schema = yup.object({
    first_name: yup.string().required("First name is required"),
    last_name: yup.string().required("Last name is required"),
    phone: yup
        .string()
        .required("Phone number is required")
        .test("phone-complete", "Please enter a valid phone number", (val) => {
            const digits = val?.replace(/\D/g, "") ?? "";
            return digits.length === 12;
        }),
    email: yup.string().email("Invalid email format").required("Email is required"),
    password: yup.string().min(6, "Password must be at least 6 characters").required("Password is required"),
    centers: yup.string().uuid("Invalid Center UUID").required("Center selection is required"),
    specialization: yup.string().required("Specialization is required"),
    experience: yup
        .number()
        .typeError("Experience must be a number")
        .min(0, "Can't be negative")
        .max(50, "Too high")
        .required("Experience is required"),
    salary: yup
        .string()
        .required("Salary is required")
        .matches(/^\d+$/, "Salary must contain only digits"),
    bio: yup.string().min(10, "Bio must be at least 10 characters").required("Biography is required"),
    date_of_birth: yup.string().required("Date of birth is required"),
}).required();

type FormData = yup.InferType<typeof schema>;

export default function AddTeacherModal({ onClose }: { onClose?: () => void }) {
    const queryClient = useQueryClient();
    const [isMounted, setIsMounted] = useState(false);
    const [phoneDisplay, setPhoneDisplay] = useState("");
    const [isOpen, setIsOpen] = useState(false);
    const [showPassword, setShowPassword] = useState(false);
    const [searchTerm, setSearchTerm] = useState("");
    const [selectedCenterName, setSelectedCenterName] = useState("");
    const dropdownRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        setIsMounted(true);
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    // O'quv markazlari ro'yxatini yuklash
    const { data: learningCenters, isLoading: isCentersLoading } = useQuery({
        queryKey: ["learning-centers-list"],
        queryFn: async () => {
            const res = await API.get("/api/v1/super-admin/centers/");
            return res?.data?.results || res?.data || [];
        }
    });

    const { register, handleSubmit, setValue, reset, formState: { errors } } = useForm<FormData>({
        resolver: yupResolver(schema),
        defaultValues: { experience: 0, salary: "" }
    });

    // Teacher qo'shish mutatsiyasi
    const { mutate: addTeacher, isPending } = useMutation({
        mutationFn: async (body: FormData) => {
            const res = await API.post("/api/v1/super-admin/teachers/", body);
            return res.data;
        },
        onSuccess: (data) => {
            toast.success(data?.message || "Teacher added successfully!");
            reset();
            setPhoneDisplay("");
            setSelectedCenterName("");
            queryClient.invalidateQueries({ queryKey: ["teachers"] });
            onClose?.();
        },
        onError: (error: any) => {
            toast.error(error?.response?.data?.message || "Something went wrong!");
        }
    });

    const handlePhoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const raw = e.target.value.replace(/\D/g, "");
        const withPrefix = raw.startsWith("998") ? raw : "998" + raw.replace(/^998/, "");
        const local = withPrefix.slice(3, 12);
        setPhoneDisplay(formatUzPhone(local));
        setValue("phone", "998" + local, { shouldValidate: true });
    };

    const filteredCenters = Array.isArray(learningCenters)
        ? learningCenters.filter((c: any) => c.name.toLowerCase().includes(searchTerm.toLowerCase()))
        : [];

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 overflow-y-auto">
            {/* Backdrop */}
            <div className={`fixed inset-0 bg-slate-900/40 backdrop-blur-sm transition-opacity duration-500 ${isMounted ? "opacity-100" : "opacity-0"}`} onClick={onClose} />

            {/* Modal Box */}
            <div className={`bg-white p-6 rounded-xl max-w-2xl w-full max-h-[92vh] overflow-y-auto relative z-10 shadow-2xl border border-slate-100 transform transition-all duration-500 ease-out ${isMounted ? "opacity-100 translate-y-0 scale-100" : "opacity-0 -translate-y-12 scale-95"}`}>

                {onClose && (
                    <button type="button" onClick={onClose} className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-50 cursor-pointer transition-colors">
                        <X className="w-5 h-5" />
                    </button>
                )}

                <div className="mb-[10px] border-[#C7C4D8] border shadow-sm w-[44px] h-[44px] rounded-lg flex justify-center items-center text-indigo-600 bg-indigo-50/10">
                    <GraduationCap className="w-6 h-6" />
                </div>
                <h3 className="text-[#313131] text-[18px] font-semibold mb-4">Add New Teacher</h3>

                <form onSubmit={handleSubmit((data) => addTeacher(data))} className="space-y-4">

                    {/* First Name & Last Name */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div>
                            <label className="text-[14px] text-[#464555] mb-1 block font-semibold">First Name</label>
                            <input {...register("first_name")} type="text" placeholder="E.g., Botir" className={`border rounded-lg w-full h-[40px] px-3 text-[14px] outline-none transition-all focus:border-indigo-500 ${errors.first_name ? "border-red-300 bg-red-50/10" : "border-[#C7C4D8]"}`} />
                            {errors.first_name && <p className="text-red-400 text-[11px] mt-1">{errors.first_name.message}</p>}
                        </div>
                        <div>
                            <label className="text-[14px] text-[#464555] mb-1 block font-semibold">Last Name</label>
                            <input {...register("last_name")} type="text" placeholder="E.g., Abbosov" className={`border rounded-lg w-full h-[40px] px-3 text-[14px] outline-none transition-all focus:border-indigo-500 ${errors.last_name ? "border-red-300 bg-red-50/10" : "border-[#C7C4D8]"}`} />
                            {errors.last_name && <p className="text-red-400 text-[11px] mt-1">{errors.last_name.message}</p>}
                        </div>
                    </div>

                    {/* Center Selection (Dropdown with Search) */}
                    <div ref={dropdownRef} className="relative">
                        <label className="text-[14px] text-[#464555] mb-1 block font-semibold">Learning Center</label>
                        <div onClick={() => !isCentersLoading && setIsOpen(!isOpen)} className={`border rounded-lg w-full h-[40px] px-3 text-[14px] flex items-center justify-between cursor-pointer bg-white transition-all ${errors.centers ? "border-red-300 bg-red-50/10" : "border-[#C7C4D8]"} ${isCentersLoading ? "opacity-60 bg-slate-50" : ""}`}>
                            <span className={selectedCenterName ? "text-[#191C1D]" : "text-slate-400"}>{isCentersLoading ? "Loading centers..." : selectedCenterName || "Select Center..."}</span>
                            <ChevronDown className={`w-4 h-4 text-slate-400 transition-transform duration-200 ${isOpen ? "rotate-180" : ""}`} />
                        </div>
                        {isOpen && (
                            <div className="absolute left-0 right-0 mt-1 bg-white border border-[#C7C4D8] rounded-lg shadow-xl z-50 max-h-[220px] overflow-hidden flex flex-col">
                                <div className="p-2 border-b border-slate-100 flex items-center gap-2 bg-slate-50 sticky top-0">
                                    <Search className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                                    <input type="text" value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} placeholder="Search center..." className="w-full bg-transparent text-xs outline-none h-6 text-[#191C1D]" autoFocus />
                                </div>
                                <div className="overflow-y-auto flex-1 max-h-[160px]">
                                    {filteredCenters.map((c: any) => (
                                        <div key={c.id} onClick={() => { setSelectedCenterName(c.name); setValue("centers", c.id, { shouldValidate: true }); setIsOpen(false); }} className="px-3 py-2 text-[13px] text-[#191C1D] hover:bg-indigo-50 hover:text-indigo-600 cursor-pointer">
                                            {c.name}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                        {errors.centers && <p className="text-red-400 text-[11px] mt-1">{errors.centers.message}</p>}
                    </div>

                    {/* Phone & Email */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div>
                            <label className="text-[14px] text-[#464555] mb-1 block font-semibold">Phone</label>
                            <div className="relative flex items-center">
                                <div className="absolute left-3 flex items-center gap-1.5 select-none pointer-events-none">
                                    <span className="text-sm font-semibold text-[#191C1D]">+998</span>
                                </div>
                                <input type="tel" value={phoneDisplay} onChange={handlePhoneChange} placeholder="90-123-45-67" className={`border rounded-lg w-full h-[40px] pl-[55px] pr-[10px] text-[14px] outline-none transition-all focus:border-indigo-500 ${errors.phone ? "border-red-300 bg-red-50/10" : "border-[#C7C4D8]"}`} />
                            </div>
                            {errors.phone && <p className="text-red-400 text-[11px] mt-1">{errors.phone.message}</p>}
                        </div>
                        <div>
                            <label className="text-[14px] text-[#464555] mb-1 block font-semibold">Email Address</label>
                            <input {...register("email")} type="email" placeholder="teacher@example.com" className={`border rounded-lg w-full h-[40px] px-3 text-[14px] outline-none transition-all focus:border-indigo-500 ${errors.email ? "border-red-300 bg-red-50/10" : "border-[#C7C4D8]"}`} />
                            {errors.email && <p className="text-red-400 text-[11px] mt-1">{errors.email.message}</p>}
                        </div>
                    </div>

                    {/* Password & Date of Birth */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div>
                            <label className="text-[14px] text-[#464555] mb-1 block font-semibold">Password</label>
                            <div className="relative flex items-center">
                                <input {...register("password")} type={showPassword ? "text" : "password"} placeholder="••••••" className={`border rounded-lg w-full h-[40px] pl-3 pr-10 text-[14px] outline-none transition-all focus:border-indigo-500 ${errors.password ? "border-red-300 bg-red-50/10" : "border-[#C7C4D8]"}`} />
                                <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 text-slate-400 hover:text-slate-600 cursor-pointer">
                                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                </button>
                            </div>
                            {errors.password && <p className="text-red-400 text-[11px] mt-1">{errors.password.message}</p>}
                        </div>
                        <div>
                            <label className="text-[14px] text-[#464555] mb-1 block font-semibold">Date of Birth</label>
                            <input {...register("date_of_birth")} type="date" className={`border rounded-lg w-full h-[40px] px-3 text-[14px] outline-none transition-all focus:border-indigo-500 ${errors.date_of_birth ? "border-red-300 bg-red-50/10" : "border-[#C7C4D8]"}`} />
                            {errors.date_of_birth && <p className="text-red-400 text-[11px] mt-1">{errors.date_of_birth.message}</p>}
                        </div>
                    </div>

                    {/* Specialization & Experience */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div>
                            <label className="text-[14px] text-[#464555] mb-1 block font-semibold">Specialization</label>
                            <input {...register("specialization")} type="text" placeholder="E.g., Senior Python Developer" className={`border rounded-lg w-full h-[40px] px-3 text-[14px] outline-none transition-all focus:border-indigo-500 ${errors.specialization ? "border-red-300 bg-red-50/10" : "border-[#C7C4D8]"}`} />
                            {errors.specialization && <p className="text-red-400 text-[11px] mt-1">{errors.specialization.message}</p>}
                        </div>
                        <div>
                            <label className="text-[14px] text-[#464555] mb-1 block font-semibold">Experience (Years)</label>
                            <input {...register("experience")} type="number" className={`border rounded-lg w-full h-[40px] px-3 text-[14px] outline-none transition-all focus:border-indigo-500 ${errors.experience ? "border-red-300 bg-red-50/10" : "border-[#C7C4D8]"}`} />
                            {errors.experience && <p className="text-red-400 text-[11px] mt-1">{errors.experience.message}</p>}
                        </div>
                    </div>

                    {/* Salary */}
                    <div>
                        <label className="text-[14px] text-[#464555] mb-1 block font-semibold">Salary</label>
                        <div className="relative flex items-center">
                            <input {...register("salary")} type="number" placeholder="E.g., 12000000" className={`border rounded-lg w-full h-[40px] pl-3 pr-16 text-[14px] outline-none transition-all focus:border-indigo-500 ${errors.salary ? "border-red-300 bg-red-50/10" : "border-[#C7C4D8]"}`} />
                            <div className="absolute right-3 text-sm font-semibold text-slate-400 pointer-events-none select-none">so'm</div>
                        </div>
                        {errors.salary && <p className="text-red-400 text-[11px] mt-1">{errors.salary.message}</p>}
                    </div>

                    {/* Biography (Bio) */}
                    <div>
                        <label className="text-[14px] text-[#464555] mb-1 block font-semibold">Biography (Bio)</label>
                        <textarea {...register("bio")} rows={3} placeholder="Tell us about teacher's core background, achievements..." className={`border rounded-lg w-full p-3 text-[14px] outline-none transition-all focus:border-indigo-500 resize-none ${errors.bio ? "border-red-300 bg-red-50/10" : "border-[#C7C4D8]"}`} />
                        {errors.bio && <p className="text-red-400 text-[11px] mt-1">{errors.bio.message}</p>}
                    </div>

                    {/* Submit Button */}
                    <button type="submit" disabled={isPending} className="w-full h-[40px] bg-[#4F46E5] hover:bg-[#4338CA] disabled:bg-indigo-300 text-white rounded-lg text-[14px] font-bold transition-colors cursor-pointer flex items-center justify-center">
                        {isPending ? "Adding..." : "Create Teacher Profile"}
                    </button>
                </form>
            </div>
        </div>
    );
}