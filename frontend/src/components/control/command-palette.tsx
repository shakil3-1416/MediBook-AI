"use client";

import clsx from "clsx";
import { useRouter } from "next/navigation";
import { useEffect, useId, useMemo, useRef, useState } from "react";

import { Icon, type IconName } from "@/components/control/icons";

type Hospital = { slug: string; name: string; status: string };
type Command = { id: string; label: string; hint: string; icon: IconName; run: () => void };

export const OPEN_HOSPITAL_KEY = "mb-open-hospital";
export const OPEN_HOSPITAL_EVENT = "mb:open-hospital";
export const ADD_HOSPITAL_EVENT = "mb:add-hospital";

/* Ctrl+K / Cmd+K: jump to any hospital or action from anywhere in the control center. */
export function CommandPalette({ open, onClose }: { open: boolean; onClose: () => void }) {
  const router = useRouter();
  const inputId = useId();
  const listId = useId();
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const [hospitals, setHospitals] = useState<Hospital[]>([]);
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (open === false) return;
    let cancelled = false;
    fetch("/api/dashboard/platform-control-v2?action=hospitals", { cache: "no-store" })
      .then((response) => (response.ok ? response.json() : []))
      .then((list: unknown) => {
        if (cancelled === false && Array.isArray(list)) setHospitals(list as Hospital[]);
      })
      .catch(() => undefined);
    const previous = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    panelRef.current?.querySelector<HTMLInputElement>("input")?.focus();
    return () => {
      cancelled = true;
      previous?.focus();
    };
  }, [open]);

  const commands = useMemo<Command[]>(() => {
    const go = (href: string) => () => {
      onClose();
      router.push(href);
    };
    const openHospital = (slug: string) => () => {
      onClose();
      if (window.location.pathname === "/control") {
        window.dispatchEvent(new CustomEvent(OPEN_HOSPITAL_EVENT, { detail: slug }));
      } else {
        window.sessionStorage.setItem(OPEN_HOSPITAL_KEY, slug);
        router.push("/control");
      }
    };
    const actions: Command[] = [
      {
        id: "add",
        label: "Add a hospital",
        hint: "Action",
        icon: "plus",
        run: () => {
          onClose();
          if (window.location.pathname === "/control") {
            window.dispatchEvent(new Event(ADD_HOSPITAL_EVENT));
          } else {
            window.sessionStorage.setItem(OPEN_HOSPITAL_KEY, "__add__");
            router.push("/control");
          }
        },
      },
      { id: "overview", label: "Go to overview", hint: "Page", icon: "grid", run: go("/control") },
      { id: "operations", label: "Go to operations", hint: "Page", icon: "pulse", run: go("/control/operations") },
    ];
    const places: Command[] = hospitals.map((hospital) => ({
      id: `h-${hospital.slug}`,
      label: hospital.name,
      hint: hospital.slug,
      icon: "building",
      run: openHospital(hospital.slug),
    }));
    const needle = query.trim().toLowerCase();
    return [...actions, ...places].filter(
      (command) => needle === "" || command.label.toLowerCase().includes(needle) || command.hint.toLowerCase().includes(needle),
    );
  }, [hospitals, query, onClose, router]);

  if (open === false) return null;
  const current = Math.min(active, Math.max(commands.length - 1, 0));

  return (
    <div className="fixed inset-0 z-[70] flex items-start justify-center px-4 pt-[12vh]">
      <div aria-hidden="true" className="absolute inset-0 bg-slate-950/40 backdrop-blur-[2px]" onMouseDown={onClose} />
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-label="Search the control center"
        className="relative w-full max-w-xl overflow-hidden rounded-2xl bg-white shadow-2xl ring-1 ring-slate-900/5"
        onKeyDown={(event) => {
          if (event.key === "Escape") onClose();
          if (event.key === "ArrowDown") {
            event.preventDefault();
            setActive((value) => Math.min(value + 1, commands.length - 1));
          }
          if (event.key === "ArrowUp") {
            event.preventDefault();
            setActive((value) => Math.max(value - 1, 0));
          }
          if (event.key === "Enter" && commands[current]) {
            event.preventDefault();
            commands[current].run();
          }
        }}
      >
        <div className="flex items-center gap-3 border-b border-slate-200 px-4">
          <Icon name="search" className="size-5 text-slate-500" />
          <label htmlFor={inputId} className="sr-only">Search hospitals and actions</label>
          <input
            id={inputId}
            role="combobox"
            aria-expanded="true"
            aria-controls={listId}
            aria-activedescendant={commands[current] ? `${listId}-${commands[current].id}` : undefined}
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              setActive(0);
            }}
            placeholder="Search hospitals and actions"
            className="h-14 w-full bg-transparent text-base text-slate-900 placeholder:text-slate-500 focus:outline-none"
          />
          <kbd className="hidden rounded-md border border-slate-200 px-1.5 py-0.5 text-xs text-slate-600 sm:block">Esc</kbd>
        </div>
        <ul id={listId} role="listbox" aria-label="Results" className="max-h-80 overflow-y-auto p-2">
          {commands.length === 0 ? (
            <li className="px-3 py-8 text-center text-sm text-slate-600">Nothing matches “{query}”.</li>
          ) : (
            commands.map((command, index) => (
              <li
                key={command.id}
                id={`${listId}-${command.id}`}
                role="option"
                aria-selected={index === current}
                onMouseEnter={() => setActive(index)}
                onMouseDown={(event) => {
                  event.preventDefault();
                  command.run();
                }}
                className={clsx(
                  "flex cursor-pointer items-center gap-3 rounded-xl px-3 py-2.5 text-sm",
                  index === current ? "bg-brand-50 text-brand-900" : "text-slate-800",
                )}
              >
                <span className={clsx("flex size-8 items-center justify-center rounded-lg", index === current ? "bg-white text-brand-700" : "bg-slate-100 text-slate-600")}>
                  <Icon name={command.icon} />
                </span>
                <span className="min-w-0 flex-1 truncate font-medium">{command.label}</span>
                <span className="shrink-0 text-xs text-slate-600">{command.hint}</span>
              </li>
            ))
          )}
        </ul>
      </div>
    </div>
  );
}
