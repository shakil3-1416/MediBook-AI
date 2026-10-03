"use client";

import {
  CalendarDays,
  LayoutDashboard,
  MessageCircle,
  Stethoscope,
} from "lucide-react";

import Link from "next/link";

import {
  usePathname,
} from "next/navigation";

import {
  ReactNode,
} from "react";


const navigation = [
  {
    href: "/",
    label: "Overview",
    icon: LayoutDashboard,
  },

  {
    href: "/assistant",
    label: "AI Assistant",
    icon: MessageCircle,
  },

  {
    href: "/doctors",
    label: "Doctors",
    icon: Stethoscope,
  },

  {
    href: "/appointments",
    label: "Appointments",
    icon: CalendarDays,
  },
];


export function AppShell({
  children,
}: {
  children: ReactNode;
}) {
  const pathname =
    usePathname();

  return (
    <div className="min-h-screen bg-slate-50 text-slate-950">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-slate-200 bg-white lg:flex lg:flex-col">
        <div className="border-b border-slate-100 px-6 py-6">
          <Link
            href="/"
            className="flex items-center gap-3"
          >
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-600 text-white">
              <Stethoscope
                size={20}
              />
            </div>

            <div>
              <div className="text-lg font-bold">
                MediBook
              </div>

              <div className="text-xs text-slate-500">
                Patient Portal
              </div>
            </div>
          </Link>
        </div>

        <nav className="flex-1 space-y-1 p-4">
          {navigation.map(
            ({
              href,
              label,
              icon: Icon,
            }) => {
              const active =
                href === "/"
                  ? pathname === "/"
                  : pathname.startsWith(
                      href
                    );

              return (
                <Link
                  key={href}
                  href={href}
                  className={[
                    "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition",
                    active
                      ? "bg-brand-50 text-brand-800"
                      : "text-slate-600 hover:bg-slate-50 hover:text-slate-950",
                  ].join(" ")}
                >
                  <Icon
                    size={18}
                  />

                  {label}
                </Link>
              );
            }
          )}
        </nav>

        <div className="border-t border-slate-100 p-4">
          <div className="rounded-xl bg-slate-50 p-4">
            <div className="text-xs font-semibold text-slate-700">
              MediBook Engine
            </div>

            <div className="mt-2 flex items-center gap-2 text-xs text-slate-500">
              <span className="h-2 w-2 rounded-full bg-brand-500" />
              Backend connected
            </div>
          </div>
        </div>
      </aside>

      <div className="lg:pl-64">
        <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/90 backdrop-blur">
          <div className="flex h-16 items-center justify-between px-5 md:px-8">
            <Link
              href="/"
              className="font-bold lg:hidden"
            >
              MediBook
            </Link>

            <div className="hidden text-sm text-slate-500 lg:block">
              Healthcare appointments,
              simplified.
            </div>

            <div className="rounded-full bg-brand-50 px-3 py-1.5 text-xs font-semibold text-brand-700">
              System online
            </div>
          </div>
        </header>

        <main className="mx-auto max-w-7xl p-5 md:p-8">
          {children}
        </main>
      </div>

      <nav className="fixed inset-x-0 bottom-0 z-40 flex border-t border-slate-200 bg-white lg:hidden">
        {navigation.map(
          ({
            href,
            label,
            icon: Icon,
          }) => (
            <Link
              key={href}
              href={href}
              className="flex flex-1 flex-col items-center gap-1 py-3 text-[11px] text-slate-600"
            >
              <Icon
                size={18}
              />

              {label}
            </Link>
          )
        )}
      </nav>
    </div>
  );
}
