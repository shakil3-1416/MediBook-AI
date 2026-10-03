"use client";

import {
  Activity,
  Bot,
  CalendarDays,
  CalendarRange,
  ClipboardList,
  LayoutDashboard,
  Link2,
  Menu,
  RefreshCw,
  Settings,
  Stethoscope,
  Users,
  X,
} from "lucide-react";

import Link from "next/link";

import {
  usePathname,
} from "next/navigation";

import {
  ReactNode,
  useState,
} from "react";

import {
  HospitalWorkspaceProvider,
  useHospitalWorkspace,
} from "./hospital-workspace-context";


const navigation = [
  {
    href:
      "/hospital-dashboard",
    label:
      "Overview",
    icon:
      LayoutDashboard,
    exact:
      true,
  },
  {
    href:
      "/hospital-dashboard/appointments",
    label:
      "Appointments",
    icon:
      CalendarDays,
  },
  {
    href:
      "/hospital-dashboard/doctors",
    label:
      "Doctors",
    icon:
      Stethoscope,
  },
  {
    href:
      "/hospital-dashboard/schedules",
    label:
      "Schedules",
    icon:
      CalendarRange,
  },
  {
    href:
      "/hospital-dashboard/integrations",
    label:
      "Integrations",
    icon:
      Link2,
  },
  {
    href:
      "/hospital-dashboard/ai",
    label:
      "AI Copilot",
    icon:
      Bot,
  },
  {
    href:
      "/hospital-dashboard/staff",
    label:
      "Staff",
    icon:
      Users,
  },
  {
    href:
      "/hospital-dashboard/audit",
    label:
      "Audit Log",
    icon:
      ClipboardList,
  },
  {
    href:
      "/hospital-dashboard/settings",
    label:
      "Settings",
    icon:
      Settings,
  },
];


function SidebarContent({
  onNavigate,
}: {
  onNavigate?: () => void;
}) {
  const pathname =
    usePathname();

  const {
    workspaces,
    activeWorkspace,
    switching,
    selectWorkspace,
  } =
    useHospitalWorkspace();

  if (!activeWorkspace) {
    return null;
  }

  return (
    <>
      <div className="border-b border-slate-100 px-5 py-5">
        <div className="text-xs font-semibold uppercase tracking-[0.16em] text-brand-600">
          MediBook
        </div>

        <div className="mt-1 text-lg font-semibold tracking-tight text-slate-950">
          Hospital Operations
        </div>

        <div className="mt-5">
          <label className="text-xs font-medium text-slate-500">
            Hospital workspace
          </label>

          <select
            value={
              activeWorkspace.slug
            }
            disabled={
              switching
            }
            onChange={
              (event) => {
                void selectWorkspace(
                  event.target.value,
                );
              }
            }
            className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 outline-none transition focus:border-brand-400 focus:ring-2 focus:ring-brand-100 disabled:opacity-60"
          >
            {workspaces.map(
              (
                workspace,
              ) => (
                <option
                  key={
                    workspace.id
                  }
                  value={
                    workspace.slug
                  }
                >
                  {
                    workspace.name
                  }
                </option>
              ),
            )}
          </select>

          <div className="mt-2 flex items-center justify-between gap-2">
            <span className="text-xs text-slate-500">
              {
                activeWorkspace.role
              }
            </span>

            {switching ? (
              <span className="flex items-center gap-1 text-xs text-brand-600">
                <RefreshCw
                  size={12}
                  className="animate-spin"
                />
                Switching
              </span>
            ) : null}
          </div>
        </div>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto p-4">
        {navigation.map(
          ({
            href,
            label,
            icon: Icon,
            exact,
          }) => {
            const active =
              exact
                ? pathname ===
                  href
                : pathname.startsWith(
                    href,
                  );

            return (
              <Link
                key={
                  href
                }
                href={
                  href
                }
                onClick={
                  onNavigate
                }
                className={[
                  "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition",
                  active
                    ? "bg-brand-50 text-brand-800"
                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-950",
                ].join(
                  " ",
                )}
              >
                <Icon
                  size={
                    18
                  }
                />

                {
                  label
                }
              </Link>
            );
          },
        )}
      </nav>

      <div className="border-t border-slate-100 p-4">
        <div className="rounded-xl bg-slate-50 p-3">
          <div className="flex items-center gap-2">
            <Activity
              size={14}
              className="text-brand-600"
            />

            <span className="truncate text-xs font-semibold text-slate-700">
              {
                activeWorkspace.name
              }
            </span>
          </div>

          <div className="mt-2 flex items-center justify-between gap-2">
            <span className="text-xs text-slate-500">
              {
                activeWorkspace.timezone
              }
            </span>

            <span className="rounded-full bg-brand-50 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-brand-700">
              {
                activeWorkspace.status
              }
            </span>
          </div>
        </div>
      </div>
    </>
  );
}


function HospitalOperationsShellInner({
  children,
}: {
  children: ReactNode;
}) {
  const [
    mobileOpen,
    setMobileOpen,
  ] =
    useState(false);

  const {
    activeWorkspace,
    loading,
    error,
    reload,
  } =
    useHospitalWorkspace();


  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <div className="rounded-2xl border border-slate-200 bg-white px-6 py-5 shadow-sm">
          <div className="flex items-center gap-3 text-sm font-medium text-slate-700">
            <RefreshCw
              size={18}
              className="animate-spin text-brand-600"
            />
            Loading hospital workspace...
          </div>
        </div>
      </div>
    );
  }


  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 p-6">
        <div className="w-full max-w-lg rounded-2xl border border-rose-200 bg-white p-8 shadow-sm">
          <h1 className="text-xl font-semibold text-slate-950">
            Hospital workspace unavailable
          </h1>

          <p className="mt-3 whitespace-pre-wrap text-sm text-rose-700">
            {error}
          </p>

          <button
            type="button"
            onClick={
              () => {
                void reload();
              }
            }
            className="mt-5 rounded-xl bg-brand-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-brand-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }


  if (!activeWorkspace) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 p-6">
        <div className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
          <h1 className="text-xl font-semibold text-slate-950">
            No active hospital workspace
          </h1>

          <p className="mt-3 text-sm leading-6 text-slate-600">
            This account does not currently have access to an active hospital.
          </p>
        </div>
      </div>
    );
  }


  return (
    <div className="min-h-screen bg-slate-50 text-slate-950">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 border-r border-slate-200 bg-white lg:flex lg:flex-col">
        <SidebarContent />
      </aside>

      {mobileOpen ? (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button
            type="button"
            aria-label="Close navigation"
            className="absolute inset-0 bg-slate-950/40"
            onClick={
              () =>
                setMobileOpen(
                  false,
                )
            }
          />

          <aside className="relative flex h-full w-72 flex-col bg-white shadow-2xl">
            <div className="absolute right-3 top-3 z-10">
              <button
                type="button"
                aria-label="Close navigation"
                onClick={
                  () =>
                    setMobileOpen(
                      false,
                    )
                }
                className="rounded-lg p-2 text-slate-500 hover:bg-slate-100"
              >
                <X
                  size={18}
                />
              </button>
            </div>

            <SidebarContent
              onNavigate={
                () =>
                  setMobileOpen(
                    false,
                  )
              }
            />
          </aside>
        </div>
      ) : null}

      <div className="lg:pl-64">
        <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/95 backdrop-blur">
          <div className="flex min-h-16 items-center justify-between gap-4 px-4 md:px-8">
            <div className="flex min-w-0 items-center gap-3">
              <button
                type="button"
                aria-label="Open navigation"
                className="rounded-lg border border-slate-200 p-2 text-slate-600 lg:hidden"
                onClick={
                  () =>
                    setMobileOpen(
                      true,
                    )
                }
              >
                <Menu
                  size={18}
                />
              </button>

              <div className="min-w-0">
                <div className="truncate text-sm font-semibold text-slate-950">
                  {
                    activeWorkspace.name
                  }
                </div>

                <div className="text-xs text-slate-500">
                  Hospital Operations
                </div>
              </div>
            </div>

            <div className="rounded-full bg-brand-50 px-3 py-1.5 text-xs font-semibold capitalize text-brand-700">
              {
                activeWorkspace.status
              }
            </div>
          </div>
        </header>

        <div className="min-h-[calc(100vh-4rem)]">
          {
            children
          }
        </div>
      </div>
    </div>
  );
}


export function HospitalOperationsShell({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <HospitalWorkspaceProvider>
      <HospitalOperationsShellInner>
        {
          children
        }
      </HospitalOperationsShellInner>
    </HospitalWorkspaceProvider>
  );
}
