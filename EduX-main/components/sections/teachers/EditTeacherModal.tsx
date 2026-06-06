"use client";

import { useState, useEffect, useRef } from "react";
import { useForm } from "react-hook-form";
import { yupResolver } from "@hookform/resolvers/yup";
import * as yup from "yup";
import { useMutation, useQueryClient, useQuery } from "@tanstack/react-query";
import { API } from "@/services/api";
import { Edit3, X, Search, ChevronDown } from "lucide-react";
import { toast } from "react-toastify";

function formatUzPhone(raw: string): string {
    const d = raw.replace(/\D/g, "").replace(/^998/, "");
    const slice = d.slice(0, 9);
    if (slice.length <= 2) return slice;
    if (slice.length <= 5) return `${slice.slice(0, 2)}-${slice.slice(2, 5)}`;
    if (slice.length <= 7) return `${slice.slice(0, 2)}-${slice.slice(2, 5)}-${slice.slice(5, 7)}`;
    return `${slice.slice(0, 2)}-${slice.slice(2, 5)}-${slice.slice(5, 7)}-${slice.slice(7)}`;
}

// Password maydoni olib tashlangan validatsiya sxemasi
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
    centers: yup.string().uuid("Invalid Center UUID").required("Center selection is required"),
    specialization: yup.string().required("Specialization is required"),
    experience: yup
        .number()
        .typeError("Experience must be a number")
        .min(0, "Can't be negative")
        .required("Experience is required"),
    salary: yup
        .string()
        .required("Salary is required")
        .matches(/^\d+$/, "Salary must contain only digits"),
    bio: yup.string().min(10, "Bio must be at least 10 characters").required("Biography is required"),
    date_of_birth: yup.string().required("Date of birth is required"),
}).required();

type FormData = yup.InferType<typeof schema>;

interface EditTeacherModalProps {
    teacher: any;
    onClose: () => void;
}

export default function EditTeacherModal({ teacher, onClose }: EditTeacherModalProps) {
    const queryClient = useQueryClient();
    const [isMounted, setIsMounted] = useState(false);
    const [phoneDisplay, setPhoneDisplay] = useState("");
    const [isOpen, setIsOpen] = useState(false);
    const [searchTerm, setSearchTerm] = useState("");
    const [selectedCenterName, setSelectedCenterName] = useState("");
    const dropdownRef = useRef<HTMLDivElement>(null);

    // O'quv markazlarini yuklash
    const { data: learningCenters, isLoading: isCentersLoading } = useQuery({
        queryKey: ["learning-centers-list"],
        queryFn: async () => {
            const res = await API.get("/api/v1/super-admin/centers/");
            return res?.data?.results || res?.data || [];
        }
    });

    const nameParts = teacher?.full_name ? teacher.full_name.trim().split(/\s+/) : [];

    const currentCenterId = teacher?.center_id || teacher?.center || teacher?.centers || "";

    const { register, handleSubmit, setValue, formState: { errors } } = useForm<FormData>({
        resolver: yupResolver(schema),
        defaultValues: {
            first_name: teacher?.first_name,
            last_name: teacher?.last_name,
            phone: teacher?.phone || "998",
            email: teacher?.email || "",
            specialization: teacher?.specialization || "",
            experience: teacher?.experience || 0,
            salary: teacher?.salary ? String(Math.abs(parseInt(teacher.salary))).replace(/\D/g, "") : "",
            bio: teacher?.bio || "",
            date_of_birth: teacher?.date_of_birth ? teacher.date_of_birth.slice(0, 10) : "2000-01-01",
            centers: currentCenterId
        }
    });

    useEffect(() => {
        setIsMounted(true);

        if (teacher?.phone) {
            const cleanLocal = teacher.phone.replace(/\D/g, "").replace(/^998/, "");
            setPhoneDisplay(formatUzPhone(cleanLocal));
        }

        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, [teacher]);

    useEffect(() => {
        if (Array.isArray(learningCenters) && currentCenterId) {
            const activeCenter = learningCenters.find((c: any) => c.id === currentCenterId);
            if (activeCenter) {
                setSelectedCenterName(activeCenter.name);
            } else if (teacher?.center_name) {
                setSelectedCenterName(teacher.center_name);
            }
        } else if (teacher?.center_name) {
            setSelectedCenterName(teacher.center_name);
        }
    }, [learningCenters, currentCenterId, teacher]);

    const { mutate: updateTeacher, isPending } = useMutation({
        mutationFn: async (body: FormData) => {
            const res = await API.put(`/api/v1/super-admin/teachers/${teacher.id}/`, body);
            return res.data;
        },
        onSuccess: (data) => {
            toast.success(data?.message || "Teacher profile updated successfully!");
            queryClient.invalidateQueries({ queryKey: ["teachers"] });
            onClose();
        },
        onError: (error: any) => {
            toast.error(error?.response?.data?.message || "Failed to update profile!");
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
        ? learningCenters.filter((c: any) => c?.name?.toLowerCase().includes(searchTerm.toLowerCase()))
        : [];

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 overflow-y-auto">
            <div className={`fixed inset-0 bg-slate-900/40 backdrop-blur-sm transition-opacity duration-500 ${isMounted ? "opacity-100" : "opacity-0"}`} onClick={onClose} />

            <div className={`bg-white p-6 rounded-xl max-w-2xl w-full max-h-[92vh] overflow-y-auto relative z-10 shadow-2xl border border-slate-100 transform transition-all duration-500 ease-out ${isMounted ? "opacity-100 translate-y-0 scale-100" : "opacity-0 -translate-y-12 scale-95"}`}>

                <button type="button" onClick={onClose} className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-50 cursor-pointer transition-colors">
                    <X className="w-5 h-5" />
                </button>

                <div className="mb-[10px] border-[#C7C4D8] border shadow-sm w-[44px] h-[44px] rounded-lg flex justify-center items-center text-indigo-600 bg-indigo-50/10">
                    <Edit3 className="w-5 h-5" />
                </div>
                <h3 className="text-[#313131] text-[18px] font-semibold mb-4">Edit Teacher Profile</h3>

                <form onSubmit={handleSubmit((data) => updateTeacher(data))} className="space-y-4">

                    {/* First Name & Last Name */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div>
                            <label className="text-[14px] text-[#464555] mb-1 block font-semibold">First Name</label>
                            <input {...register("first_name")} type="text" className={`border rounded-lg w-full h-[40px] px-3 text-[14px] outline-none transition-all focus:border-indigo-500 ${errors.first_name ? "border-red-300 bg-red-50/10" : "border-[#C7C4D8]"}`} />
                            {errors.first_name && <p className="text-red-400 text-[11px] mt-1">{errors.first_name.message}</p>}
                        </div>
                        <div>
                            <label className="text-[14px] text-[#464555] mb-1 block font-semibold">Last Name</label>
                            <input {...register("last_name")} type="text" className={`border rounded-lg w-full h-[40px] px-3 text-[14px] outline-none transition-all focus:border-indigo-500 ${errors.last_name ? "border-red-300 bg-red-50/10" : "border-[#C7C4D8]"}`} />
                            {errors.last_name && <p className="text-red-400 text-[11px] mt-1">{errors.last_name.message}</p>}
                        </div>
                    </div>

                    {/* Learning Center Selection */}
                    <div ref={dropdownRef} className="relative">
                        <label className="text-[14px] text-[#464555] mb-1 block font-semibold">Learning Center</label>
                        <div onClick={() => !isCentersLoading && setIsOpen(!isOpen)} className={`border rounded-lg w-full h-[40px] px-3 text-[14px] flex items-center justify-between cursor-pointer bg-white transition-all ${errors.centers ? "border-red-300 bg-red-50/10" : "border-[#C7C4D8]"}`}>
                            <span className={selectedCenterName ? "text-[#191C1D]" : "text-slate-400"}>
                                {isCentersLoading ? "Loading centers..." : selectedCenterName || "Select Center..."}
                            </span>
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
                                        <div
                                            key={c.id}
                                            onClick={() => {
                                                setSelectedCenterName(c.name);
                                                setValue("centers", c.id, { shouldValidate: true });
                                                setIsOpen(false);
                                            }}
                                            className="px-3 py-2 text-[13px] text-[#191C1D] hover:bg-indigo-50 hover:text-indigo-600 cursor-pointer flex items-center gap-2"
                                        >
                                            {c.logo && <img src={c.logo} alt={c.name} className="w-5 h-5 rounded object-cover" />}
                                            <span>{c.name}</span>
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
                                <input type="tel" value={phoneDisplay} onChange={handlePhoneChange} className={`border rounded-lg w-full h-[40px] pl-[55px] pr-[10px] text-[14px] outline-none transition-all focus:border-indigo-500 ${errors.phone ? "border-red-300 bg-red-50/10" : "border-[#C7C4D8]"}`} />
                            </div>
                            {errors.phone && <p className="text-red-400 text-[11px] mt-1">{errors.phone.message}</p>}
                        </div>
                        <div>
                            <label className="text-[14px] text-[#464555] mb-1 block font-semibold">Email Address</label>
                            <input {...register("email")} type="email" className={`border rounded-lg w-full h-[40px] px-3 text-[14px] outline-none transition-all focus:border-indigo-500 ${errors.email ? "border-red-300 bg-red-50/10" : "border-[#C7C4D8]"}`} />
                            {errors.email && <p className="text-red-400 text-[11px] mt-1">{errors.email.message}</p>}
                        </div>
                    </div>

                    {/* Date of Birth (Faqat Date qoldi) */}
                    <div>
                        <label className="text-[14px] text-[#464555] mb-1 block font-semibold">Date of Birth</label>
                        <input {...register("date_of_birth")} type="date" className={`border rounded-lg w-full h-[40px] px-3 text-[14px] outline-none transition-all focus:border-indigo-500 ${errors.date_of_birth ? "border-red-300 bg-red-50/10" : "border-[#C7C4D8]"}`} />
                        {errors.date_of_birth && <p className="text-red-400 text-[11px] mt-1">{errors.date_of_birth.message}</p>}
                    </div>

                    {/* Specialization & Experience */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div>
                            <label className="text-[14px] text-[#464555] mb-1 block font-semibold">Specialization</label>
                            <input {...register("specialization")} type="text" className={`border rounded-lg w-full h-[40px] px-3 text-[14px] outline-none transition-all focus:border-indigo-500 ${errors.specialization ? "border-red-300 bg-red-50/10" : "border-[#C7C4D8]"}`} />
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
                            <input {...register("salary")} type="text" className={`border rounded-lg w-full h-[40px] pl-3 pr-16 text-[14px] outline-none transition-all focus:border-indigo-500 ${errors.salary ? "border-red-300 bg-red-50/10" : "border-[#C7C4D8]"}`} />
                            <div className="absolute right-3 text-sm font-semibold text-slate-400 pointer-events-none select-none">so'm</div>
                        </div>
                        {errors.salary && <p className="text-red-400 text-[11px] mt-1">{errors.salary.message}</p>}
                    </div>

                    {/* Biography (Bio) */}
                    <div>
                        <label className="text-[14px] text-[#464555] mb-1 block font-semibold">Biography (Bio)</label>
                        <textarea {...register("bio")} rows={3} className={`border rounded-lg w-full p-3 text-[14px] outline-none transition-all focus:border-indigo-500 resize-none ${errors.bio ? "border-red-300 bg-red-50/10" : "border-[#C7C4D8]"}`} />
                        {errors.bio && <p className="text-red-400 text-[11px] mt-1">{errors.bio.message}</p>}
                    </div>

                    <button type="submit" disabled={isPending} className="w-full h-[40px] bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300 text-white rounded-lg text-[14px] font-bold transition-all flex items-center justify-center cursor-pointer">
                        {isPending ? "Saving Changes..." : "Save Changes"}
                    </button>
                </form>
            </div>
        </div>
    );
}