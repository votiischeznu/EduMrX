"use client";

import { useState, useEffect, useRef } from "react";
import { useForm } from "react-hook-form";
import { yupResolver } from "@hookform/resolvers/yup";
import * as yup from "yup";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { API } from "@/services/api";
import { User, Eye, EyeOff, MapPin, Notebook, X, Loader2 } from "lucide-react";
import { toast } from "react-toastify";
import { YMaps, Map, Placemark } from "@pbe/react-yandex-maps";

import { ChevronDown, Search } from "lucide-react";
import { useQuery } from "@tanstack/react-query";

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
        .required("Telefon raqam majburiy")
        .test("phone-complete", "Raqamni to'liq kiriting", (val) => {
            const digits = val?.replace(/\D/g, "") ?? "";
            return digits.length === 12;
        }),
    email: yup.string().email("Xato email formati").required("Email kiritilishi shart"),
    password: yup
        .string()
        .required("Parol kiritilishi shart")
        .min(6, "Parol kamida 6 ta belgidan iborat bo'lishi kerak"),
    center: yup.string().uuid("O'quv markazi UUID formatida bo'lishi shart").required("Markazni tanlash shart"),
    date_of_birth: yup.string().required("Tug'ilgan sana kiritilishi shart"),
    address: yup.string().required("Manzil kiritilishi shart"),
    latitude: yup.string().required("Kenglik (Lat) shart"),
    longitude: yup.string().required("Uzunlik (Lang) shart"),
    notes: yup.string().optional(),
    status: yup.string().oneOf(["active", "frozen", "inactive"]).required("Status shart"),
}).required();

type FormData = yup.InferType<typeof schema>;

interface AddStudentModalProps {
    onClose: () => void;
}

export default function AddStudentModal({ onClose }: AddStudentModalProps) {
    const queryClient = useQueryClient();
    const [isMounted, setIsMounted] = useState(false);
    const [phoneDisplay, setPhoneDisplay] = useState("");
    const [showPassword, setShowPassword] = useState(false);

    const mapRef = useRef<any>(null);
    const [mapCoords, setMapCoords] = useState<[number, number]>([41.311081, 69.240562]);

    const [isCenterOpen, setIsCenterOpen] = useState(false);
    const [centerSearch, setCenterSearch] = useState("");
    const [selectedCenter, setSelectedCenter] = useState<{ id: string, name: string } | null>(null);

    useEffect(() => {
        setIsMounted(true);
    }, []);

    const {
        register,
        handleSubmit,
        setValue,
        reset,
        formState: { errors },
    } = useForm({
        resolver: yupResolver(schema),
        defaultValues: {
            status: "active",
            center: "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            latitude: "41.311081",
            longitude: "69.240562",
            date_of_birth: new Date().toISOString().split('T')[0],
            address: ""
        }
    });


    const { data: centersData, isLoading: isCentersLoading } = useQuery({
        queryKey: ["centers-list"],
        queryFn: async () => {
            const res = await API.get("/api/v1/super-admin/centers/");
            return res.data.results; // Backenddan keladigan formatga qarab o'zgartiring
        }
    });

    const filteredCenters = centersData?.filter((c: any) =>
        c.name.toLowerCase().includes(centerSearch.toLowerCase())
    );

    const handleMapClick = async (e: any) => {
        const coords = e.get("coords") as [number, number];
        setMapCoords(coords);

        const latStr = coords[0].toFixed(6);
        const lngStr = coords[1].toFixed(6);

        setValue("latitude", latStr, { shouldValidate: true });
        setValue("longitude", lngStr, { shouldValidate: true });

        if (mapRef.current) {
            mapRef.current.panTo(coords, {
                flying: true,
                duration: 600
            });
        }

        try {
            const response = await fetch(
                `https://nominatim.openstreetmap.org/reverse?format=json&lat=${coords[0]}&lon=${coords[1]}&accept-language=uz,ru,en`
            );
            const data = await response.json();

            if (data && data.display_name) {
                // Juda uzun manzil bo'lib ketmasligi uchun chiroyli qilib kesib olamiz
                setValue("address", data.display_name, { shouldValidate: true });
            }
        } catch (error) {
            console.error("Manzilni aniqlashda xatolik:", error);
        }
    };

    const { mutate: addStudent, isPending } = useMutation({
        mutationFn: async (body: FormData) => {
            const res = await API.post("/api/v1/super-admin/students/", body, {
                headers: {
                    "Content-Type": "application/json",
                },
            });

            return res.data;
        },
        onSuccess: (data) => {
            toast.success(data?.message || "Talaba muvaffaqiyatli qo'shildi!");
            reset();
            setPhoneDisplay("");
            setShowPassword(false);
            setMapCoords([41.311081, 69.240562]);

            queryClient.invalidateQueries({
                queryKey: ["students-list"],
            });
            onClose();
        },
        onError: (err: any) => {
            toast.error(err?.response?.data?.detail || "Xatolik yuz berdi!");
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
        addStudent(data);
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div
                className={`fixed inset-0 bg-slate-900/40 backdrop-blur-sm transition-opacity duration-500 ${isMounted ? "opacity-100" : "opacity-0"}`}
                onClick={onClose}
            />

            <div className={`bg-white p-6 rounded-xl max-w-xl w-full max-h-[90vh] overflow-y-auto relative z-10 shadow-2xl border border-slate-100 transform transition-all duration-500 ease-out ${isMounted ? "opacity-100 translate-y-0 scale-100" : "opacity-0 -translate-y-12 scale-95"}`}>

                <button type="button" onClick={onClose} className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-50 cursor-pointer border-none bg-transparent">
                    <X className="w-5 h-5" />
                </button>

                <div className="mb-[10px] border-[#C7C4D8] border shadow-sm w-[44px] h-[44px] rounded-lg flex justify-center items-center text-indigo-600 bg-indigo-50/10">
                    <User className="w-6 h-6" />
                </div>

                <h3 className="text-[#313131] text-[18px] font-semibold mb-4">Add New Student</h3>

                <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="text-[14px] text-[#464555] mb-1 block font-semibold">First Name</label>
                            <input
                                {...register("first_name")}
                                type="text"
                                placeholder="John"
                                className={`border rounded-lg w-full h-[40px] px-3 text-[14px] outline-none transition-all ${errors.first_name ? "border-red-300 bg-red-50/10" : "border-[#C7C4D8] focus:border-indigo-500"}`}
                            />
                            {errors.first_name && <p className="text-red-400 text-[11px] mt-1">{errors.first_name.message}</p>}
                        </div>
                        <div>
                            <label className="text-[14px] text-[#464555] mb-1 block font-semibold">Last Name</label>
                            <input
                                {...register("last_name")}
                                type="text"
                                placeholder="Doe"
                                className={`border rounded-lg w-full h-[40px] px-3 text-[14px] outline-none transition-all ${errors.last_name ? "border-red-300 bg-red-50/10" : "border-[#C7C4D8] focus:border-indigo-500"}`}
                            />
                            {errors.last_name && <p className="text-red-400 text-[11px] mt-1">{errors.last_name.message}</p>}
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="text-[14px] text-[#464555] mb-1 block font-semibold">Phone Number</label>
                            <div className="relative flex items-center">
                                <div className="absolute left-3 flex items-center gap-1.5 select-none pointer-events-none">
                                    <span className="text-base leading-none">🇺🇿</span>
                                    <span className="text-sm font-semibold text-[#191C1D]">+998</span>
                                </div>
                                <input
                                    type="tel"
                                    value={phoneDisplay}
                                    onChange={handlePhoneChange}
                                    placeholder="90-123-45-67"
                                    className={`border rounded-lg w-full h-[40px] pl-[90px] pr-[10px] text-[14px] outline-none transition-all ${errors.phone ? "border-red-300 bg-red-50/10" : "border-[#C7C4D8] focus:border-indigo-500"}`}
                                />
                            </div>
                            {errors.phone && <p className="text-red-400 text-[11px] mt-1 ml-1">{errors.phone.message}</p>}
                        </div>

                        <div>
                            <label className="text-[14px] text-[#464555] mb-1 block font-semibold">Password</label>
                            <div className="relative flex items-center">
                                <input
                                    {...register("password")}
                                    type={showPassword ? "text" : "password"}
                                    placeholder="••••••••"
                                    className={`border rounded-lg w-full h-[40px] pl-3 pr-[40px] text-[14px] outline-none transition-all ${errors.password ? "border-red-300 bg-red-50/10" : "border-[#C7C4D8] focus:border-indigo-500"}`}
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-3 text-slate-400 hover:text-slate-600 cursor-pointer p-0.5 rounded-sm focus:outline-none border-none bg-transparent flex items-center"
                                >
                                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                </button>
                            </div>
                            {errors.password && <p className="text-red-400 text-[11px] mt-1">{errors.password.message}</p>}
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="text-[14px] text-[#464555] mb-1 block font-semibold">Email Address</label>
                            <input
                                {...register("email")}
                                type="email"
                                placeholder="student@example.com"
                                className={`border rounded-lg w-full h-[40px] px-3 text-[14px] outline-none transition-all ${errors.email ? "border-red-300 bg-red-50/10" : "border-[#C7C4D8] focus:border-indigo-500"}`}
                            />
                            {errors.email && <p className="text-red-400 text-[11px] mt-1">{errors.email.message}</p>}
                        </div>
                        <div>
                            <label className="text-[14px] text-[#464555] mb-1 block font-semibold">Date of Birth</label>
                            <input
                                {...register("date_of_birth")}
                                type="date"
                                className={`border rounded-lg w-full h-[40px] px-3 text-[14px] outline-none transition-all ${errors.date_of_birth ? "border-red-300" : "border-[#C7C4D8] focus:border-indigo-500"}`}
                            />
                            {errors.date_of_birth && <p className="text-red-400 text-[11px] mt-1">{errors.date_of_birth.message}</p>}
                        </div>
                    </div>

                    <div>
                        <label className="text-[14px] text-[#464555] mb-1 block font-semibold">Address</label>
                        <div className="relative flex items-center">
                            <MapPin className="absolute left-3 w-4 h-4 text-slate-400 select-none pointer-events-none" />
                            <input
                                {...register("address")}
                                type="text"
                                placeholder="Xaritadan tanlang yoki manzilni kiriting"
                                className={`border rounded-lg w-full h-[40px] pl-10 pr-3 text-[14px] outline-none transition-all ${errors.address ? "border-red-300 bg-red-50/10" : "border-[#C7C4D8] focus:border-indigo-500"}`}
                            />
                        </div>
                        {errors.address && <p className="text-red-400 text-[11px] mt-1">{errors.address.message}</p>}
                    </div>

                    <div>
                        <label className="text-[14px] text-[#464555] mb-1.5 block font-semibold">Select Location on Yandex Map</label>
                        <div className="w-full h-[200px] rounded-xl overflow-hidden border border-[#C7C4D8] relative z-0">
                            {isMounted && (
                                <YMaps query={{ lang: "ru_RU" }}>
                                    <Map
                                        instanceRef={(ref) => {
                                            mapRef.current = ref;
                                        }}
                                        state={{ center: mapCoords, zoom: 12, controls: [] }}
                                        onClick={handleMapClick}
                                        style={{ width: "100%", height: "100%" }}
                                    >
                                        <Placemark geometry={mapCoords} />
                                    </Map>
                                </YMaps>
                            )}
                        </div>
                        <p className="text-[11px] text-slate-400 mt-1">Xarita ustiga bosing — marker silliq siljiydi va manzil aniqlanadi.</p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-slate-50 p-3 rounded-xl border border-dashed border-slate-200">
                        <div>
                            <label className="text-[12px] text-slate-500 mb-1 block font-semibold">Map Latitude (Lat)</label>
                            <input
                                {...register("latitude")}
                                type="text"
                                placeholder="41.123456"
                                className={`bg-white border rounded-lg w-full h-[36px] px-3 text-[13px] outline-none focus:border-indigo-500 ${errors.latitude ? "border-red-300" : "border-[#C7C4D8]"}`}
                            />
                            {errors.latitude && <p className="text-red-400 text-[11px] mt-1">{errors.latitude.message}</p>}
                        </div>
                        <div>
                            <label className="text-[12px] text-slate-500 mb-1 block font-semibold">Map Longitude (Lang)</label>
                            <input
                                {...register("longitude")}
                                type="text"
                                placeholder="69.123456"
                                className={`bg-white border rounded-lg w-full h-[36px] px-3 text-[13px] outline-none focus:border-indigo-500 ${errors.longitude ? "border-red-300" : "border-[#C7C4D8]"}`}
                            />
                            {errors.longitude && <p className="text-red-400 text-[11px] mt-1">{errors.longitude.message}</p>}
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="text-[14px] text-[#464555] mb-1 block font-semibold">Status</label>
                            <select
                                {...register("status")}
                                className="border border-[#C7C4D8] rounded-lg w-full h-[40px] px-3 text-[14px] outline-none bg-white text-[#191C1D] focus:border-indigo-500"
                            >
                                <option value="active">Active</option>
                                <option value="frozen">Frozen</option>
                                <option value="inactive">Inactive</option>
                            </select>
                        </div>
                        <div className="relative">
                            <label className="text-[14px] text-[#464555] mb-1 block font-semibold">Learning Center</label>
                            <div
                                className="border border-[#C7C4D8] rounded-lg w-full h-[40px] px-3 flex items-center justify-between cursor-pointer hover:border-indigo-500 transition-all"
                                onClick={() => setIsCenterOpen(!isCenterOpen)}
                            >
                                <span className={selectedCenter ? "text-slate-900" : "text-slate-400"}>
                                    {selectedCenter ? selectedCenter.name : "Markazni tanlang..."}
                                </span>
                                <ChevronDown className="w-4 h-4 text-slate-400" />
                            </div>

                            {isCenterOpen && (
                                <div className="absolute w-full mt-1 bg-white border border-[#C7C4D8] rounded-lg shadow-xl z-50 p-2">
                                    <div className="flex items-center gap-2 border-b pb-2 mb-2">
                                        <Search className="w-4 h-4 text-slate-400" />
                                        <input
                                            autoFocus
                                            placeholder="Qidirish..."
                                            className="w-full outline-none text-[14px]"
                                            onChange={(e) => setCenterSearch(e.target.value)}
                                        />
                                    </div>
                                    <div className="max-h-[150px] overflow-y-auto">
                                        {isCentersLoading ? (
                                            <p className="text-center py-2 text-sm">Yuklanmoqda...</p>
                                        ) : filteredCenters?.length > 0 ? (
                                            filteredCenters.map((c: any) => (
                                                <div
                                                    key={c.id}
                                                    className="px-3 py-2 hover:bg-indigo-50 cursor-pointer rounded-md text-[14px]"
                                                    onClick={() => {
                                                        setSelectedCenter({ id: c.id, name: c.name });
                                                        setValue("center", c.id, { shouldValidate: true });
                                                        setIsCenterOpen(false);
                                                    }}
                                                >
                                                    {c.name}
                                                </div>
                                            ))
                                        ) : (
                                            <p className="text-center py-2 text-sm text-slate-400">Topilmadi</p>
                                        )}
                                    </div>
                                </div>
                            )}
                            {errors.center && <p className="text-red-400 text-[11px] mt-1">{errors.center.message}</p>}
                        </div>
                    </div>

                    <div>
                        <label className="text-[14px] text-[#464555] mb-1 block font-semibold">Notes (Optional)</label>
                        <div className="relative flex items-start">
                            <Notebook className="absolute left-3 top-3 w-4 h-4 text-slate-400 select-none pointer-events-none" />
                            <textarea
                                {...register("notes")}
                                placeholder="Additional notes about the student..."
                                rows={2}
                                className="border border-[#C7C4D8] rounded-lg w-full pl-10 pr-3 py-2 text-[14px] outline-none resize-none min-h-[60px] focus:border-indigo-500"
                            />
                        </div>
                    </div>

                    <button
                        type="submit"
                        disabled={isPending}
                        className="w-full h-[40px] mt-2 bg-[#4F46E5] hover:bg-[#4338CA] disabled:bg-indigo-300 text-white rounded-lg text-[14px] font-bold transition-colors cursor-pointer flex items-center justify-center border-none select-none"
                    >
                        {isPending ? (
                            <span className="flex items-center gap-2">
                                <Loader2 className="w-4 h-4 animate-spin" /> Adding Student...
                            </span>
                        ) : (
                            "Add Student"
                        )}
                    </button>
                </form>
            </div>
        </div>
    );
}