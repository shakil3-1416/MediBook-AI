"use client";

import clsx from "clsx";
import { createContext, useCallback, useContext, useRef, useState, type ReactNode } from "react";

type ToastTone = "success" | "error" | "info";
type ToastItem = { id: number; message: string; tone: ToastTone };

const ToastContext = createContext<(message: string, tone?: ToastTone) => void>(() => undefined);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const nextId = useRef(1);
  const notify = useCallback((message: string, tone: ToastTone = "success") => {
    const id = nextId.current;
    nextId.current += 1;
    setToasts((list) => [...list, { id, message, tone }]);
    window.setTimeout(() => setToasts((list) => list.filter((toast) => toast.id !== id)), 4500);
  }, []);
  return (
    <ToastContext.Provider value={notify}>
      {children}
      <div aria-live="polite" className="pointer-events-none fixed bottom-4 right-4 z-[60] flex w-[min(92vw,380px)] flex-col gap-2">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            role="status"
            className="pointer-events-auto flex items-start gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm shadow-lg motion-safe:animate-[mb-toast_220ms_ease-out]"
          >
            <span
              aria-hidden="true"
              className={clsx(
                "mt-1.5 size-2 shrink-0 rounded-full",
                toast.tone === "success" ? "bg-brand-600" : toast.tone === "error" ? "bg-red-600" : "bg-sky-600",
              )}
            />
            <p className="text-slate-800">{toast.message}</p>
          </div>
        ))}
      </div>
      <style>{"@keyframes mb-toast{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}"}</style>
    </ToastContext.Provider>
  );
}

export function useToast() {
  return useContext(ToastContext);
}
