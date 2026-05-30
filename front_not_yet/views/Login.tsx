"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { yupResolver } from "@hookform/resolvers/yup";
import * as yup from "yup";
import { Eye, EyeOff, Lock } from "lucide-react";
import Text from "@/components/ui/Text";
import Title from "@/components/ui/Title";
import { useMutation } from "@tanstack/react-query";
import { AuthAPI } from "@/services/api";
import { toast } from "react-toastify";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/authStore";

const schema = yup.object({
    phone: yup
        .string()
        .required("Phone number is mandatory")
        .test("phone-complete", "Enter a full number", (val) => {
            const digits = val?.replace(/\D/g, "") ?? "";
            return digits.length === 12;
        }),
    password: yup
        .string()
        .min(1, "At least 8 characters")
        .required("Password is required"),
});

type FormData = yup.InferType<typeof schema>;

function formatUzPhone(raw: string): string {
    const d = raw.slice(0, 9);
    if (d.length <= 2) return d;
    if (d.length <= 5) return `${d.slice(0, 2)}-${d.slice(2, 5)}`;
    if (d.length <= 7) return `${d.slice(0, 2)}-${d.slice(2, 5)}-${d.slice(5, 7)}`;
    return `${d.slice(0, 2)}-${d.slice(2, 5)}-${d.slice(5, 7)}-${d.slice(7)}`;
}

export default function LoginView() {
    const [showPassword, setShowPassword] = useState(false);
    const [phoneDisplay, setPhoneDisplay] = useState("");
    const [phoneFull, setPhoneFull] = useState("998");

    const router = useRouter();
    const { login } = useAuthStore();

    const {
        register,
        handleSubmit,
        setValue,
        formState: { errors },
    } = useForm<FormData>({
        resolver: yupResolver(schema),
    });

    const { mutate: loginToProfile, isPending } = useMutation({
        mutationFn: async (body: FormData) => {
            const res = await AuthAPI.post("/api/v1/login/", body);
            return res?.data;
        },
        onSuccess: (data) => {
            login(data.user, {
                access_token: data.access_token,
                refresh_token: data.refresh_token,
            });

            toast.success(data?.message || "Login successfully");

            console.log(data);

            router.push("/");
        },
        onError: (err: any) => {
            toast.error(
                err?.response?.data?.message ||
                err.message ||
                "Login amalga oshmadi"
            );

            console.log(err);

        },
    });

    const handlePhoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const raw = e.target.value.replace(/\D/g, "");
        const withPrefix = raw.startsWith("998") ? raw : "998" + raw.replace(/^998/, "");
        const local = withPrefix.slice(3, 12);
        const formatted = formatUzPhone(local);
        setPhoneDisplay(formatted);

        const full = "998" + local;
        setPhoneFull(full);
        setValue("phone", full, { shouldValidate: true });
    };

    const isPhoneComplete = phoneFull.replace(/\D/g, "").length === 12;

    // Backendga yuborishdan oldin telefon raqamiga "+" belgisi qo'shildi
    const onSubmit = (data: FormData) => {
        const formattedData = {
            ...data,
            phone: `+${data.phone}`
        };
        loginToProfile(formattedData);
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-[#EEF2FF] via-[#F8F9FF] to-[#E0E7FF] flex items-center justify-center p-4">
            <div className="w-full max-w-[448px]">
                <div className="bg-white rounded-2xl shadow-xl shadow-indigo-100/60 border border-indigo-50 p-8">

                    {/* Logo */}
                    <div className="mb-8 text-center">
                        <Title text="EDU X" />
                        <Text text="Education Center ADMIN" />
                    </div>

                    <div className="mb-6">
                        <h2 className="text-[20px] font-semibold text-[#191C1D]">Welcome back</h2>
                        <p className="text-[14px] text-[#464555]">Please enter your details to sign in.</p>
                    </div>

                    <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">

                        {/* Phone */}
                        <div>
                            <label className="text-[16px] text-[#464555] mb-[10px] block font-semibold">
                                Phone
                            </label>
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
                                    className={`border rounded-lg w-full h-[40px] pl-[90px] pr-[36px] text-[14px] outline-none
                                        placeholder:text-[#6B7280] text-[#191C1D]
                                        ${errors.phone
                                            ? "border-red-300"
                                            : isPhoneComplete
                                                ? "border-emerald-300"
                                                : "border-[#C7C4D8]"
                                        }`}
                                />
                                {isPhoneComplete && (
                                    <div className="absolute right-3 w-5 h-5 rounded-full bg-emerald-500 flex items-center justify-center">
                                        <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                                            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                                        </svg>
                                    </div>
                                )}
                            </div>
                            {errors.phone && (
                                <p className="text-red-400 text-[11px] mt-1 ml-2">{errors.phone.message}</p>
                            )}
                        </div>

                        {/* Password */}
                        <div>
                            <label className="text-[16px] text-[#464555] mb-[10px] block font-semibold">
                                Password
                            </label>
                            <div className="relative">
                                <div className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none">
                                    <Lock className="w-[16px] h-[16px] text-[#C7C4D8]" />
                                </div>
                                <input
                                    {...register("password")}
                                    type={showPassword ? "text" : "password"}
                                    placeholder="Enter Password"
                                    className={`border rounded-lg w-full h-[40px] pl-[40px] pr-[40px] text-[14px] outline-none
                                        placeholder:text-[#6B7280] text-[#191C1D]
                                        ${errors.password ? "border-red-300" : "border-[#C7C4D8]"}`}
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword((p) => !p)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-[#C7C4D8] hover:text-[#4338CA] transition-colors"
                                >
                                    {showPassword ? <EyeOff className="w-[16px] h-[16px]" /> : <Eye className="w-[16px] h-[16px]" />}
                                </button>
                            </div>
                            {errors.password && (
                                <p className="text-red-400 text-[11px] mt-1 ml-2">{errors.password.message}</p>
                            )}
                        </div>

                        {/* Submit Button */}
                        <button
                            type="submit"
                            disabled={isPending}
                            className="w-full h-[40px] mt-2 bg-[#4F46E5] hover:bg-[#4338CA] disabled:bg-indigo-300 text-white rounded-lg text-[14px] font-bold transition-colors"
                        >
                            {isPending ? "Signing in..." : "Sign in"}
                        </button>
                    </form>
                </div>

                <p className="text-center text-xs text-gray-400 mt-4">
                    EduX © {new Date().getFullYear()} — Training Center Management System
                </p>
            </div>
        </div>
    );
}