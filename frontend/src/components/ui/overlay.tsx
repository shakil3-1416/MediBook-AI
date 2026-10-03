"use client";

import { useEffect, useId, useRef, type ReactNode, type RefObject } from "react";

const FOCUSABLE = "a[href], button:not([disabled]), input:not([disabled]), select, textarea, [tabindex]:not([tabindex='-1'])";
const POP_IN: Keyframe[] = [
  { opacity: 0, transform: "translateY(8px) scale(0.98)" },
  { opacity: 1, transform: "translateY(0) scale(1)" },
];
const SLIDE_IN: Keyframe[] = [
  { opacity: 0.6, transform: "translateX(40px)" },
  { opacity: 1, transform: "translateX(0)" },
];

/* Focus trap, Escape to close, scroll lock, entrance motion (skipped for reduced motion) and focus return. */
function useOverlay(open: boolean, onClose: () => void, panelRef: RefObject<HTMLDivElement | null>, motion: Keyframe[]) {
  const closeRef = useRef(onClose);
  useEffect(() => {
    closeRef.current = onClose;
  });
  useEffect(() => {
    if (open === false) return;
    const panel = panelRef.current;
    const previous = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    if (panel && window.matchMedia("(prefers-reduced-motion: reduce)").matches === false) {
      panel.animate(motion, { duration: 220, easing: "cubic-bezier(0.2, 0.8, 0.2, 1)" });
    }
    panel?.querySelector<HTMLElement>("[data-autofocus]")?.focus();
    if (panel && panel.contains(document.activeElement) === false) {
      panel.querySelector<HTMLElement>(FOCUSABLE)?.focus();
    }
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") {
        closeRef.current();
        return;
      }
      if (event.key !== "Tab" || panel === null) return;
      const items = Array.from(panel.querySelectorAll<HTMLElement>(FOCUSABLE));
      if (items.length === 0) return;
      const first = items[0];
      const last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (event.shiftKey === false && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }
    document.addEventListener("keydown", onKey);
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = overflow;
      previous?.focus();
    };
  }, [open, panelRef, motion]);
  return closeRef;
}

export function Dialog({ open, title, description, onClose, children, size = "md" }: {
  open: boolean; title: string; description?: string; onClose: () => void; children: ReactNode; size?: "md" | "lg";
}) {
  const titleId = useId();
  const descriptionId = useId();
  const panelRef = useRef<HTMLDivElement>(null);
  const closeRef = useOverlay(open, onClose, panelRef, POP_IN);
  if (open === false) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center p-4 sm:items-center">
      <div aria-hidden="true" className="absolute inset-0 bg-slate-950/40 backdrop-blur-[2px]" onMouseDown={() => closeRef.current()} />
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={description ? descriptionId : undefined}
        className={`relative w-full ${size === "lg" ? "max-w-2xl" : "max-w-lg"} rounded-2xl bg-white shadow-2xl ring-1 ring-slate-900/5`}
      >
        <div className="border-b border-slate-200 px-6 py-5">
          <h2 id={titleId} className="text-lg font-semibold tracking-tight text-slate-900">{title}</h2>
          {description ? <p id={descriptionId} className="mt-1 text-sm text-slate-600">{description}</p> : null}
        </div>
        <div className="max-h-[75vh] overflow-y-auto px-6 py-5">{children}</div>
      </div>
    </div>
  );
}

export function Drawer({ open, onClose, labelledBy, children }: {
  open: boolean; onClose: () => void; labelledBy: string; children: ReactNode;
}) {
  const panelRef = useRef<HTMLDivElement>(null);
  const closeRef = useOverlay(open, onClose, panelRef, SLIDE_IN);
  if (open === false) return null;
  return (
    <div className="fixed inset-0 z-50">
      <div aria-hidden="true" className="absolute inset-0 bg-slate-950/30 backdrop-blur-[2px]" onMouseDown={() => closeRef.current()} />
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={labelledBy}
        className="absolute inset-y-0 right-0 flex w-full max-w-xl flex-col bg-white shadow-2xl ring-1 ring-slate-900/5"
      >
        {children}
      </div>
    </div>
  );
}
