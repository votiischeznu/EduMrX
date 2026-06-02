"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { API } from "@/services/api";
import { X, AlertTriangle, Loader2 } from "lucide-react";
import { toast } from "react-toastify";

interface DeleteModalProps {
  centerId: string;
  centerName: string;
  onClose: () => void;
}

export default function DeleteLearningCenterModal({ centerId, centerName, onClose }: DeleteModalProps) {
  const queryClient = useQueryClient();

  const { mutate: deleteCenter, isPending } = useMutation({
    mutationFn: async () => {
      await API.delete(`/api/v1/super-admin/centers/${centerId}/`);
    },
    onSuccess: () => {
      toast.success("O'quv markazi tizimdan butkul o'chirildi");
      queryClient.invalidateQueries({ queryKey: ["learning-centers"] });
      onClose();
    },
    onError: (err: any) => {
      toast.error(err?.message || "O'chirishda xatolik yuz berdi");
    }
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs animate-fade-in">
      <div className="absolute inset-0" onClick={onClose} />

      <div className="relative bg-white w-full max-w-md rounded-xl shadow-xl border border-slate-100 overflow-hidden z-10">
        <div className="p-5 flex flex-col items-center text-center">
          <div className="w-12 h-12 rounded-full bg-red-50 border border-red-100 flex items-center justify-center text-red-500 mb-4">
            <AlertTriangle className="w-6 h-6" />
          </div>

          <h3 className="text-base font-bold text-slate-900">O'quv markazini o'chirish</h3>
          <p className="text-sm text-slate-500 mt-2">
            Rostdan ham <span className="font-semibold text-slate-800">"{centerName}"</span> o'quv markazini o'chirmoqchimisiz? Bu amalni ortga qaytarib bo'lmaydi.
          </p>

          <div className="flex items-center gap-3 w-full mt-6">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 h-10 border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 text-sm font-semibold rounded-lg cursor-pointer"
            >
              Yo'q, bekor qilish
            </button>
            <button
              type="button"
              onClick={() => deleteCenter()}
              disabled={isPending}
              className="flex-1 inline-flex items-center justify-center gap-2 h-10 bg-red-600 hover:bg-red-700 text-white text-sm font-semibold rounded-lg disabled:bg-red-400 cursor-pointer"
            >
              {isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : "Ha, o'chirilsin"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}