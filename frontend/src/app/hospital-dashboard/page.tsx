"use client";

import { useRouter } from "next/navigation";

import Link from "next/link";


import {
  useEffect,
  useMemo,
  useState,
} from "react";


type DashboardData = {
  hospital: {
    id: string;
    slug: string;
    name: string;
    active: boolean;
    timezone: string;
  };

  metrics: {
    doctors: number;
    specialties: number;
    appointments_today: number;
    appointments_upcoming: number;
    appointments_confirmed: number;
    appointments_cancelled: number;
    appointments_rescheduled: number;
    available_slots: number;
    unavailable_slots: number;
  };

  recent_appointments: Array<{
    appointment_id: string;
    confirmation_code: string;
    status: string;
    doctor_name: string;
    date: string | null;
    time: string | null;
    booked_at: string | null;
  }>;

  integrations: Array<{
    type: string;
    status: string;
    updated_at: string | null;
  }>;

  generated_at: string;
};


function MetricCard({
  label,
  value,
  description,
}: {
  label: string;
  value: number;
  description: string;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="text-sm font-medium text-slate-500">
        {label}
      </div>

      <div className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">
        {value}
      </div>

      <div className="mt-2 text-xs leading-5 text-slate-500">
        {description}
      </div>
    </div>
  );
}


function StatusBadge({
  value,
}: {
  value: string;
}) {
  const normalized =
    value.toLowerCase();

  const styles =
    normalized === "confirmed" ||
    normalized === "connected" ||
    normalized === "active"
      ? "bg-emerald-50 text-emerald-700 ring-emerald-600/20"
      : normalized === "cancelled" ||
        normalized === "error" ||
        normalized === "failed"
      ? "bg-rose-50 text-rose-700 ring-rose-600/20"
      : "bg-amber-50 text-amber-700 ring-amber-600/20";

  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset ${styles}`}
    >
      {value}
    </span>
  );
}


export default function HospitalDashboardPage() {
  const router =
    useRouter();


  const [
    data,
    setData,
  ] =
    useState<
      DashboardData | null
    >(null);

  const [
    loading,
    setLoading,
  ] =
    useState(true);

  const [
    error,
    setError,
  ] =
    useState<string | null>(
      null,
    );


  async function loadDashboard() {
    setLoading(true);

    setError(
      null,
    );

    try {
      const response =
        await fetch(
          "/api/dashboard/hospital-summary?hospital=medibook-demo",
          {
            cache:
              "no-store",
          },
        );


      if ((response.status === 401 || response.status === 403)) {
        router.replace(
          "/hospital-login",
        );

        return;
      }


      if (!response.ok) {
        const body =
          await response.text();

        throw new Error(
          body ||
          `HTTP ${response.status}`,
        );
      }


      const payload =
        await response.json();


      setData(
        payload,
      );

    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not load hospital dashboard.",
      );

    } finally {
      setLoading(false);
    }
  }


  useEffect(
    () => {
      queueMicrotask(() => {
        void loadDashboard();
      });
    },
    [],
  );


  const utilization =
    useMemo(
      () => {
        if (!data) {
          return 0;
        }

        const total =
          data.metrics
            .available_slots
          +
          data.metrics
            .unavailable_slots;

        if (!total) {
          return 0;
        }

        return Math.round(
          (
            data.metrics
              .unavailable_slots
            /
            total
          )
          * 100,
        );
      },
      [
        data,
      ],
    );


  if (loading) {
    return (
      <main data-medibook-hospital className="min-h-screen bg-slate-50 p-8">
        <div className="mx-auto max-w-7xl">
          <div className="rounded-2xl border border-slate-200 bg-white p-8 text-slate-600">
            Loading hospital operations...
          </div>
        </div>
      </main>
    );
  }


  if (
    error ||
    !data
  ) {
    return (
      <main className="min-h-screen bg-slate-50 p-8">
        <div className="mx-auto max-w-4xl">
          <div className="rounded-2xl border border-rose-200 bg-white p-8">
            <h1 className="text-xl font-semibold text-slate-950">
              Hospital dashboard unavailable
            </h1>

            <p className="mt-3 whitespace-pre-wrap text-sm text-rose-700">
              {error}
            </p>

            <button
              className="mt-5 rounded-xl bg-purple-600 px-4 py-2 text-sm font-medium text-white"
              onClick={
                () => {
                  void loadDashboard();
                }
              }
            >
              Retry
            </button>
          </div>
        </div>
      </main>
    );
  }


  return (
    <main className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
          <div>
            <div className="text-sm font-semibold text-purple-600">
              MediBook Hospital Operations
            </div>

            <h1 className="mt-1 text-2xl font-semibold tracking-tight text-slate-950">
              {data.hospital.name}
            </h1>

            <p className="mt-1 text-sm text-slate-500">
              Appointment operations, schedules and integration health
            </p>
          </div>


<div className="flex items-center gap-3">
            <Link
              href="/hospital-dashboard/integrations"
              className="rounded-xl border border-purple-200 bg-purple-50 px-4 py-2 text-sm font-medium text-purple-700 hover:bg-purple-100"
            >
              Integrations
            </Link>

            <Link
              href="/hospital-dashboard/schedules"
              className="rounded-xl border border-purple-200 bg-purple-50 px-4 py-2 text-sm font-medium text-purple-700 hover:bg-purple-100"
            >
              Schedules
            </Link>

            <Link
              href="/hospital-dashboard/appointments"
              className="rounded-xl bg-purple-600 px-4 py-2 text-sm font-medium text-white hover:bg-purple-700"
            >
              Appointments
            </Link>

            <StatusBadge
              value={
                data.hospital.active
                  ? "Active"
                  : "Inactive"
              }
            />

            <button
              onClick={
                () => {
                  void loadDashboard();
                }
              }
              className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-50"
            >
              Refresh
            </button>
          </div>
        </div>
      </header>


      <div className="mx-auto max-w-7xl space-y-8 px-6 py-8">
        <section>
          <div className="mb-4">
            <h2 className="text-lg font-semibold text-slate-950">
              Today
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Live operational snapshot from MediBook data
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <MetricCard
              label="Appointments today"
              value={
                data.metrics
                  .appointments_today
              }
              description="Active appointments scheduled for today"
            />

            <MetricCard
              label="Upcoming"
              value={
                data.metrics
                  .appointments_upcoming
              }
              description="Current and future active appointments"
            />

            <MetricCard
              label="Available slots"
              value={
                data.metrics
                  .available_slots
              }
              description="Future appointment capacity"
            />

            <MetricCard
              label="Slot utilization"
              value={
                utilization
              }
              description="Percentage of future slots currently unavailable/booked"
            />
          </div>
        </section>


        <section>
          <div className="mb-4">
            <h2 className="text-lg font-semibold text-slate-950">
              Appointment operations
            </h2>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <MetricCard
              label="Confirmed"
              value={
                data.metrics
                  .appointments_confirmed
              }
              description="Confirmed appointments in hospital scope"
            />

            <MetricCard
              label="Cancelled"
              value={
                data.metrics
                  .appointments_cancelled
              }
              description="Cancelled appointment records"
            />

            <MetricCard
              label="Reschedules"
              value={
                data.metrics
                  .appointments_rescheduled
              }
              description="Recorded reschedule events"
            />

            <MetricCard
              label="Unavailable slots"
              value={
                data.metrics
                  .unavailable_slots
              }
              description="Future slots currently unavailable"
            />
          </div>
        </section>


        <section>
          <div className="mb-4">
            <h2 className="text-lg font-semibold text-slate-950">
              Clinical directory
            </h2>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <MetricCard
              label="Doctors"
              value={
                data.metrics.doctors
              }
              description="Doctors mapped to this hospital"
            />

            <MetricCard
              label="Specialties"
              value={
                data.metrics
                  .specialties
              }
              description="Distinct specialties represented"
            />
          </div>
        </section>


        <section className="grid gap-6 lg:grid-cols-[2fr_1fr]">
          <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
            <div className="border-b border-slate-200 px-5 py-4">
              <h2 className="font-semibold text-slate-950">
                Recent appointments
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                Latest appointment activity for this hospital
              </p>
            </div>

            {data.recent_appointments.length === 0 ? (
              <div className="p-8 text-sm text-slate-500">
                No appointment activity yet.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200">
                  <thead className="bg-slate-50">
                    <tr className="text-left text-xs font-medium uppercase tracking-wide text-slate-500">
                      <th className="px-5 py-3">
                        Doctor
                      </th>

                      <th className="px-5 py-3">
                        Date
                      </th>

                      <th className="px-5 py-3">
                        Time
                      </th>

                      <th className="px-5 py-3">
                        Confirmation
                      </th>

                      <th className="px-5 py-3">
                        Status
                      </th>
                    </tr>
                  </thead>

                  <tbody className="divide-y divide-slate-100">
                    {data.recent_appointments.map(
                      (
                        appointment,
                      ) => (
                        <tr
                          key={
                            appointment.appointment_id
                          }
                          className="text-sm text-slate-700"
                        >
                          <td className="whitespace-nowrap px-5 py-4 font-medium text-slate-950">
                            {
                              appointment.doctor_name
                            }
                          </td>

                          <td className="whitespace-nowrap px-5 py-4">
                            {
                              appointment.date ??
                              "—"
                            }
                          </td>

                          <td className="whitespace-nowrap px-5 py-4">
                            {
                              appointment.time ??
                              "—"
                            }
                          </td>

                          <td className="whitespace-nowrap px-5 py-4 font-mono text-xs">
                            {
                              appointment.confirmation_code
                            }
                          </td>

                          <td className="whitespace-nowrap px-5 py-4">
                            <StatusBadge
                              value={
                                appointment.status
                              }
                            />
                          </td>
                        </tr>
                      ),
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </div>


          <div className="rounded-2xl border border-slate-200 bg-white shadow-sm">
            <div className="border-b border-slate-200 px-5 py-4">
              <h2 className="font-semibold text-slate-950">
                Integration health
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                Connected hospital systems
              </p>
            </div>

            <div className="space-y-4 p-5">
              {data.integrations.length === 0 ? (
                <div className="rounded-xl bg-slate-50 p-4">
                  <div className="text-sm font-medium text-slate-800">
                    Demo data source
                  </div>

                  <p className="mt-1 text-xs leading-5 text-slate-500">
                    No external hospital integration is currently configured.
                  </p>
                </div>
              ) : (
                data.integrations.map(
                  (
                    integration,
                    index,
                  ) => (
                    <div
                      key={
                        `${integration.type}-${index}`
                      }
                      className="flex items-start justify-between gap-3 rounded-xl border border-slate-200 p-4"
                    >
                      <div>
                        <div className="text-sm font-medium text-slate-900">
                          {
                            integration.type
                          }
                        </div>

                        <div className="mt-1 text-xs text-slate-500">
                          {
                            integration.updated_at
                              ? new Date(
                                  integration.updated_at,
                                ).toLocaleString()
                              : "No recent update"
                          }
                        </div>
                      </div>

                      <StatusBadge
                        value={
                          integration.status
                        }
                      />
                    </div>
                  ),
                )
              )}
            </div>
          </div>
        </section>


        <section className="rounded-2xl border border-purple-100 bg-purple-50/60 p-5">
          <div className="text-sm font-semibold text-purple-900">
            Hospital tenant
          </div>

          <div className="mt-2 grid gap-2 text-sm text-purple-800 sm:grid-cols-3">
            <div>
              Slug:{" "}
              <span className="font-medium">
                {data.hospital.slug}
              </span>
            </div>

            <div>
              Timezone:{" "}
              <span className="font-medium">
                {data.hospital.timezone}
              </span>
            </div>

            <div>
              Updated:{" "}
              <span className="font-medium">
                {new Date(
                  data.generated_at,
                ).toLocaleString()}
              </span>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
