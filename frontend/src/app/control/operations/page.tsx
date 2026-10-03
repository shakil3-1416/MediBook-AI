"use client";

import clsx from "clsx";
import { useEffect, useState } from "react";

import { AnimatedNumber } from "@/components/control/charts";
import { ControlShell } from "@/components/control/control-shell";
import { Icon, type IconName } from "@/components/control/icons";
import { Alert, Badge, Card, EmptyState, SkeletonBlock } from "@/components/ui/primitives";
import { readErrorMessage } from "@/lib/error-message";

type Summary = {
  metrics: { hospitals: number; active_hospitals: number; integrations: number; degraded_integrations: number };
  hospitals: Array<{
    id: string; slug: string; name: string; status: string; is_active: boolean; timezone: string; doctors: number;
    integrations: { total: number; connected: number; degraded: number; error: number };
  }>;
};

const numberFormat = new Intl.NumberFormat("en");
const count = (value: unknown) => (typeof value === "number" ? value : 0);

function Metric({ icon, label, value, footnote, warn = false }: { icon: IconName; label: string; value: number; footnote: string; warn?: boolean }) {
  return (
    <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_1px_2px_rgba(16,40,28,0.04),0_12px_32px_-16px_rgba(16,40,28,0.14)]">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-slate-600">{label}</p>
        <span className={clsx("flex size-9 items-center justify-center rounded-xl ring-1", warn ? "bg-amber-50 text-amber-800 ring-amber-100" : "bg-brand-50 text-brand-700 ring-brand-100")}>
          <Icon name={icon} className="size-[18px]" />
        </span>
      </div>
      <AnimatedNumber value={value} className="mt-3 block text-3xl font-semibold tracking-tight text-slate-900 tabular-nums" />
      <p className={clsx("mt-1 text-xs", warn ? "font-medium text-amber-800" : "text-slate-600")}>{footnote}</p>
    </div>
  );
}

function HealthBar({ connected, degraded, failing, total }: { connected: number; degraded: number; failing: number; total: number }) {
  if (total === 0) return <span className="text-xs text-slate-600">No integrations</span>;
  const part = (value: number) => `${(value / total) * 100}%`;
  return (
    <div className="w-40">
      <div className="flex h-2 overflow-hidden rounded-full bg-slate-100" aria-hidden="true">
        <span className="bg-brand-600" style={{ width: part(connected) }} />
        <span className="bg-amber-500" style={{ width: part(degraded) }} />
        <span className="bg-red-600" style={{ width: part(failing) }} />
      </div>
      <p className="mt-1 text-xs text-slate-600">{connected} connected, {degraded} degraded, {failing} failing</p>
    </div>
  );
}

export default function ControlOperationsPage() {
  const [data, setData] = useState<Summary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetch("/api/dashboard/platform-control", { cache: "no-store" })
      .then(async (response) => {
        if (response.ok === false) throw new Error(await readErrorMessage(response, "Could not load platform operations."));
        return (await response.json()) as Summary;
      })
      .then((value) => {
        if (cancelled === false) setData(value);
      })
      .catch((err: unknown) => {
        if (cancelled === false) setError(err instanceof Error ? err.message : "Could not load platform operations.");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const hospitals = data?.hospitals ?? [];
  const degraded = count(data?.metrics?.degraded_integrations);
  const failingHospitals = hospitals.filter((hospital) => count(hospital.integrations?.error) > 0).length;
  const healthy = degraded === 0 && failingHospitals === 0;

  return (
    <ControlShell
      eyebrow="Platform"
      title="Operations"
      description="Integration health and sync status for every hospital, refreshed each time you open this page."
    >
      {error ? <div className="mb-6"><Alert title="Something went wrong">{error}</Alert></div> : null}

      {data === null && error === null ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{[0, 1, 2, 3].map((index) => <SkeletonBlock key={index} className="h-[132px] rounded-2xl" />)}</div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <Metric icon="building" label="Hospitals" value={count(data?.metrics?.hospitals)} footnote={`${count(data?.metrics?.active_hospitals)} active`} />
          <Metric icon="plug" label="Integrations" value={count(data?.metrics?.integrations)} footnote="Configured across all hospitals" />
          <Metric icon="alert" label="Degraded" value={degraded} footnote={degraded > 0 ? "Check the hospitals below" : "Nothing degraded"} warn={degraded > 0} />
          <Metric icon="pulse" label="Hospitals with failed syncs" value={failingHospitals} footnote={failingHospitals > 0 ? "A sync failed recently" : "No failed syncs"} warn={failingHospitals > 0} />
        </div>
      )}

      {data ? (
        <div className={clsx("mt-6 flex items-center gap-3 rounded-2xl border px-5 py-4 text-sm", healthy ? "border-brand-200 bg-brand-50/70 text-brand-900" : "border-amber-200 bg-amber-50 text-amber-900")}>
          <Icon name={healthy ? "check" : "alert"} className="size-5" />
          {healthy ? "Every integration is healthy." : "Some integrations need attention. The hospitals affected are highlighted below."}
        </div>
      ) : null}

      <Card className="mt-6 overflow-hidden">
        <div className="border-b border-slate-200 px-6 py-5">
          <h2 className="text-base font-semibold text-slate-900">Integration status by hospital</h2>
          <p className="mt-0.5 text-sm text-slate-600">Connected, degraded and failing connections to hospital systems.</p>
        </div>
        {data === null ? (
          <div className="space-y-3 px-6 py-6">{[0, 1, 2].map((index) => <SkeletonBlock key={index} className="h-14 rounded-xl" />)}</div>
        ) : hospitals.length === 0 ? (
          <EmptyState title="No hospitals yet" description="Hospitals appear here once they are added." />
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <caption className="sr-only">Integration status by hospital</caption>
              <thead className="bg-slate-50/80 text-xs font-semibold uppercase tracking-wide text-slate-600">
                <tr>
                  <th scope="col" className="px-6 py-3">Hospital</th>
                  <th scope="col" className="px-3 py-3">Status</th>
                  <th scope="col" className="hidden px-3 py-3 text-right sm:table-cell">Doctors</th>
                  <th scope="col" className="px-3 py-3 text-right">Integrations</th>
                  <th scope="col" className="px-6 py-3">Health</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {hospitals.map((hospital) => {
                  const failing = count(hospital.integrations?.error);
                  const slow = count(hospital.integrations?.degraded);
                  return (
                    <tr key={hospital.id} className={clsx(failing > 0 ? "bg-red-50/40" : slow > 0 ? "bg-amber-50/40" : "hover:bg-slate-50")}>
                      <td className="px-6 py-3.5">
                        <p className="font-medium text-slate-900">{hospital.name}</p>
                        <p className="text-xs text-slate-600">{hospital.slug}{hospital.timezone ? ` · ${hospital.timezone}` : ""}</p>
                      </td>
                      <td className="px-3 py-3.5">
                        <Badge tone={hospital.status === "active" ? "green" : hospital.status === "suspended" ? "red" : "neutral"}>
                          {hospital.status.charAt(0).toUpperCase() + hospital.status.slice(1)}
                        </Badge>
                      </td>
                      <td className="hidden px-3 py-3.5 text-right tabular-nums text-slate-800 sm:table-cell">{numberFormat.format(count(hospital.doctors))}</td>
                      <td className="px-3 py-3.5 text-right tabular-nums text-slate-800">{numberFormat.format(count(hospital.integrations?.total))}</td>
                      <td className="px-6 py-3.5">
                        <HealthBar connected={count(hospital.integrations?.connected)} degraded={slow} failing={failing} total={count(hospital.integrations?.total)} />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </ControlShell>
  );
}
