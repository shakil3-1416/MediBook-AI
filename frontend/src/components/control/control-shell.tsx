"use client";

import clsx from "clsx";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";

import { CommandPalette } from "@/components/control/command-palette";
import { Icon, type IconName } from "@/components/control/icons";

const NAV: { href: string; label: string; icon: IconName }[] = [
  { href: "/control", label: "Overview", icon: "grid" },
  { href: "/control/operations", label: "Operations", icon: "pulse" },
];

const focusRing = "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-700";

function Brand() {
  return (
    <Link href="/control" className={clsx("flex items-center gap-3 rounded-lg", focusRing)}>
      <span aria-hidden="true" className="flex size-9 items-center justify-center rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 text-sm font-bold text-white shadow-sm shadow-brand-900/20">
        M
      </span>
      <span className="leading-tight">
        <span className="block text-[15px] font-semibold tracking-tight text-slate-900">MediBook</span>
        <span className="block text-xs text-slate-600">Platform console</span>
      </span>
    </Link>
  );
}

export function ControlShell({ title, eyebrow, description, actions, children }: {
  title: ReactNode; eyebrow?: ReactNode; description?: ReactNode; actions?: ReactNode; children: ReactNode;
}) {
  const pathname = usePathname();
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [signingOut, setSigningOut] = useState(false);

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setPaletteOpen((value) => value === false);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  async function signOut() {
    setSigningOut(true);
    await Promise.allSettled([
      fetch("/api/auth/logout", { method: "POST" }),
      fetch("/api/auth/hospital-logout", { method: "POST" }),
    ]);
    window.location.assign("/login");
  }

  const nav = (
    <nav aria-label="Control center" className="flex gap-1 lg:flex-col">
      {NAV.map((item) => {
        const active = item.href === "/control" ? pathname === "/control" : pathname.startsWith(item.href);
        return (
          <Link
            key={item.href}
            href={item.href}
            aria-current={active ? "page" : undefined}
            className={clsx(
              "group relative flex items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium transition-colors",
              focusRing,
              active ? "bg-brand-50 text-brand-800" : "text-slate-700 hover:bg-slate-100 hover:text-slate-900",
            )}
          >
            {active ? <span aria-hidden="true" className="absolute inset-y-2 left-0 hidden w-1 rounded-full bg-brand-600 lg:block" /> : null}
            <Icon name={item.icon} className={clsx("size-[18px]", active ? "text-brand-700" : "text-slate-500 group-hover:text-slate-700")} />
            {item.label}
          </Link>
        );
      })}
    </nav>
  );

  const quiet = clsx(
    "flex w-full items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-100 hover:text-slate-900 disabled:opacity-60",
    focusRing,
  );

  return (
    <div className="min-h-screen bg-[var(--mb-bg)] text-slate-900">
        <div className="flex min-h-screen">
          <aside className="sticky top-0 hidden h-screen w-64 shrink-0 flex-col border-r border-slate-200/80 bg-white/80 px-4 py-6 backdrop-blur lg:flex">
            <Brand />
            <p className="mt-8 px-3 text-xs font-semibold uppercase tracking-wider text-slate-600">Platform</p>
            <div className="mt-2">{nav}</div>
            <div className="mt-auto space-y-1 border-t border-slate-200 pt-4">
              <Link href="/" className={quiet}>
                <Icon name="back" className="size-[18px] text-slate-500" />
                Back to site
              </Link>
              <button type="button" onClick={signOut} disabled={signingOut} className={quiet}>
                <Icon name="logout" className="size-[18px] text-slate-500" />
                {signingOut ? "Signing out…" : "Sign out"}
              </button>
            </div>
          </aside>
          <div className="flex min-w-0 flex-1 flex-col">
            <header className="sticky top-0 z-30 border-b border-slate-200/80 bg-white/80 backdrop-blur">
              <div className="flex h-16 items-center gap-3 px-4 sm:px-6 lg:px-10">
                <div className="lg:hidden">
                  <Brand />
                </div>
                <button
                  type="button"
                  onClick={() => setPaletteOpen(true)}
                  className={clsx(
                    "ml-auto flex h-10 w-full max-w-sm items-center gap-3 rounded-xl border border-slate-200 bg-white px-3 text-sm text-slate-600 shadow-sm transition-colors hover:border-slate-300 lg:ml-0",
                    focusRing,
                  )}
                >
                  <Icon name="search" className="text-slate-500" />
                  <span className="flex-1 text-left">Search hospitals and actions</span>
                  <kbd className="hidden rounded-md border border-slate-200 px-1.5 py-0.5 text-xs text-slate-600 sm:block">Ctrl K</kbd>
                </button>
                <div className="hidden items-center gap-3 lg:ml-auto lg:flex">
                  <span className="flex size-9 items-center justify-center rounded-full bg-brand-100 text-xs font-semibold text-brand-800" aria-hidden="true">PA</span>
                  <span className="text-sm leading-tight">
                    <span className="block font-medium text-slate-900">Platform admin</span>
                    <span className="block text-xs text-slate-600">Full access</span>
                  </span>
                </div>
                <button type="button" onClick={signOut} disabled={signingOut} aria-label="Sign out" className={clsx("rounded-lg p-2 text-slate-600 hover:bg-slate-100 lg:hidden", focusRing)}>
                  <Icon name="logout" className="size-5" />
                </button>
              </div>
              <div className="overflow-x-auto border-t border-slate-200/80 px-4 py-2 lg:hidden">{nav}</div>
            </header>
            <main className="flex-1 px-4 py-8 sm:px-6 lg:px-10">
              <div className="mx-auto max-w-7xl">
                <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
                  <div>
                    {eyebrow ? <div className="text-sm font-medium text-brand-700">{eyebrow}</div> : null}
                    <h1 className="mt-1 text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">{title}</h1>
                    {description ? <div className="mt-1.5 max-w-2xl text-sm text-slate-600">{description}</div> : null}
                  </div>
                  {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
                </div>
                {children}
              </div>
            </main>
          </div>
        </div>
        <CommandPalette open={paletteOpen} onClose={() => setPaletteOpen(false)} />
    </div>
  );
}
