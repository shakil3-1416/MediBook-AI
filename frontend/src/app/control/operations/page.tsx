"use client";

import { readErrorMessage } from "@/lib/error-message";

import Link from "next/link";
import {
  useEffect,
  useState,
} from "react";


type Summary = {
  metrics: {
    hospitals: number;
    active_hospitals: number;
    integrations: number;
    degraded_integrations: number;
  };

  hospitals: Array<{
    id: string;
    slug: string;
    name: string;
    status: string;
    is_active: boolean;
    timezone: string;
    doctors: number;
    integrations: {
      total: number;
      connected: number;
      degraded: number;
      error: number;
    };
  }>;
};


export default function ControlOperationsPage() {
  const [
    data,
    setData,
  ] = useState<Summary | null>(
    null,
  );

  const [
    error,
    setError,
  ] = useState<string | null>(
    null,
  );


  useEffect(
    () => {
      void fetch(
        "/api/dashboard/platform-control",
        {
          cache:
            "no-store",
        },
      )
        .then(
          async (response) => {
            if (!response.ok) {
              throw new Error(
                await readErrorMessage(
                  response,
                  "Could not load platform operations.",
                ),
              );
            }

            return response.json();
          },
        )
        .then(setData)
        .catch(
          (value) =>
            setError(
              value instanceof Error
                ? value.message
                : String(value),
            ),
        );
    },
    [],
  );


  return (
    <main className="min-h-screen bg-slate-50 px-6 py-8">
      <div className="mx-auto max-w-7xl">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm font-semibold text-purple-600">
              MediBook Control Center
            </div>

            <h1 className="mt-1 text-3xl font-semibold">
              Platform operations
            </h1>
          </div>

          <Link
            href="/control"
            className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm"
          >
            Control home
          </Link>
        </div>

        {error && (
          <div className="mt-6 rounded-xl border border-rose-200 bg-rose-50 p-4 text-rose-700">
            {error}
          </div>
        )}

        {data && (
          <>
            <div className="mt-8 grid gap-4 md:grid-cols-4">
              {[
                [
                  "Hospitals",
                  data.metrics.hospitals,
                ],
                [
                  "Active",
                  data.metrics.active_hospitals,
                ],
                [
                  "Integrations",
                  data.metrics.integrations,
                ],
                [
                  "Needs attention",
                  data.metrics.degraded_integrations,
                ],
              ].map(
                ([label, value]) => (
                  <div
                    key={String(label)}
                    className="rounded-2xl border border-slate-200 bg-white p-5"
                  >
                    <div className="text-sm text-slate-500">
                      {label}
                    </div>

                    <div className="mt-2 text-3xl font-semibold">
                      {value}
                    </div>
                  </div>
                ),
              )}
            </div>

            <div className="mt-8 overflow-hidden rounded-2xl border border-slate-200 bg-white">
              {data.hospitals.map(
                (hospital) => (
                  <div
                    key={hospital.id}
                    className="grid gap-4 border-b border-slate-100 p-5 md:grid-cols-5"
                  >
                    <div className="md:col-span-2">
                      <div className="font-semibold">
                        {hospital.name}
                      </div>

                      <div className="text-sm text-slate-500">
                        {hospital.slug}
                      </div>
                    </div>

                    <div>
                      <div className="text-xs text-slate-500">
                        Doctors
                      </div>

                      <div className="font-semibold">
                        {hospital.doctors}
                      </div>
                    </div>

                    <div>
                      <div className="text-xs text-slate-500">
                        Integrations
                      </div>

                      <div className="font-semibold">
                        {hospital.integrations.total}
                      </div>
                    </div>

                    <div>
                      <div className="text-xs text-slate-500">
                        Health
                      </div>

                      <div className="font-semibold">
                        {hospital.integrations.degraded +
                          hospital.integrations.error ===
                        0
                          ? "Healthy"
                          : "Attention"}
                      </div>
                    </div>
                  </div>
                ),
              )}
            </div>
          </>
        )}
      </div>
    </main>
  );
}
