"use client";

import clsx from "clsx";
import { useEffect, useId, useMemo, useState, useSyncExternalStore, type FormEvent } from "react";

import { AnimatedNumber, BarList, Donut } from "@/components/control/charts";
import { ADD_HOSPITAL_EVENT, OPEN_HOSPITAL_EVENT, OPEN_HOSPITAL_KEY } from "@/components/control/command-palette";
import { ControlShell } from "@/components/control/control-shell";
import { Icon, type IconName } from "@/components/control/icons";
import { Dialog, Drawer } from "@/components/ui/overlay";
import { Alert, Badge, Button, Card, CheckboxField, EmptyState, InputField, SelectField, SkeletonBlock, TextareaField, type Tone } from "@/components/ui/primitives";
import { useToast } from "@/components/ui/toast";
import { readErrorMessage } from "@/lib/error-message";

type Overview = {
  hospitals_total: number; hospitals_active: number; hospitals_suspended: number; appointments_total: number;
  doctors_total: number; staff_total: number; integrations_total: number; unhealthy_integrations: number;
  copilot_proposals_total: number; copilot_failed_executions: number;
};
type Hospital = {
  id: string; slug: string; name: string; timezone?: string | null; status: string; data_mode?: string | null;
  doctors: number; appointments: number; staff: number; integrations: number; schedule_rules: number; schedule_exceptions: number;
  integration_health: Record<string, unknown>; security: Record<string, unknown>; usage: Record<string, unknown>;
};
type HospitalDetail = Hospital & {
  recent_integrations: Record<string, unknown>[]; recent_appointments: Record<string, unknown>[]; recent_platform_events: Record<string, unknown>[];
};

const API = "/api/dashboard/platform-control-v2";
const TIMEZONES = ["Asia/Dhaka", "Asia/Kolkata", "Asia/Singapore", "Asia/Dubai", "Europe/London", "UTC"];
const AVATARS = ["bg-brand-100 text-brand-800", "bg-teal-100 text-teal-800", "bg-lime-100 text-lime-900", "bg-amber-100 text-amber-900", "bg-slate-200 text-slate-800", "bg-brand-200 text-brand-900"];
const numberFormat = new Intl.NumberFormat("en");

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, { cache: "no-store", ...init });
  if (response.ok === false) throw new Error(await readErrorMessage(response, `Request failed (${response.status}).`));
  return (await response.json()) as T;
}

const count = (value: unknown) => (typeof value === "number" ? value : 0);
const humanize = (key: string) => {
  const text = key.replace(/[_.]/g, " ").trim();
  return text.charAt(0).toUpperCase() + text.slice(1);
};
const isTestHospital = (hospital: Pick<Hospital, "slug" | "name">) => /isolation-test|e2e|(^|-)test(-|$)/.test(hospital.slug) || /isolation test/i.test(hospital.name);
const statusTone = (status: string): Tone => (status === "active" ? "green" : status === "suspended" ? "red" : "neutral");
const initials = (name: string) => name.split(/\s+/).filter(Boolean).slice(0, 2).map((word) => word[0]?.toUpperCase() ?? "").join("");
const avatarClass = (slug: string) => AVATARS[[...slug].reduce((sum, char) => sum + char.charCodeAt(0), 0) % AVATARS.length];
const slugify = (name: string) => name.toLowerCase().normalize("NFKD").replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 120);

const subscribeNever = () => () => undefined;
function subscribeTicker(callback: () => void) {
  const id = window.setInterval(callback, 10000);
  return () => window.clearInterval(id);
}

function displayValue(value: unknown) {
  if (value === null || value === undefined || value === "") return "None";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "number") return numberFormat.format(value);
  return String(value);
}

function eventTitle(item: Record<string, unknown>) {
  for (const key of ["action", "event", "status", "kind", "provider", "name", "confirmation_code"]) {
    const value = item[key];
    if (typeof value === "string" && value) return humanize(value);
  }
  return "Activity";
}

function eventTime(item: Record<string, unknown>) {
  for (const key of ["created_at", "updated_at", "occurred_at", "scheduled_for", "slot_date"]) {
    const value = item[key];
    if (typeof value === "string" && value) {
      const date = new Date(value);
      return Number.isNaN(date.getTime()) ? value : date.toLocaleString("en-GB", { dateStyle: "medium", timeStyle: "short" });
    }
  }
  return null;
}

function Avatar({ hospital, size = "md" }: { hospital: Pick<Hospital, "slug" | "name">; size?: "md" | "lg" }) {
  return (
    <span aria-hidden="true" className={clsx("flex shrink-0 items-center justify-center rounded-xl font-semibold", avatarClass(hospital.slug), size === "lg" ? "size-12 text-base" : "size-9 text-xs")}>
      {initials(hospital.name)}
    </span>
  );
}

function KpiCard({ icon, label, value, footnote, tone = "neutral" }: { icon: IconName; label: string; value: number; footnote: string; tone?: "neutral" | "warning" }) {
  return (
    <div className="group relative overflow-hidden rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_1px_2px_rgba(16,40,28,0.04),0_12px_32px_-16px_rgba(16,40,28,0.14)] transition-shadow hover:shadow-[0_1px_2px_rgba(16,40,28,0.04),0_18px_40px_-16px_rgba(16,40,28,0.22)]">
      <div aria-hidden="true" className="pointer-events-none absolute -right-10 -top-10 size-32 rounded-full bg-brand-100/60 blur-2xl transition-opacity group-hover:opacity-80" />
      <div className="relative flex items-center justify-between">
        <p className="text-sm font-medium text-slate-600">{label}</p>
        <span className="flex size-9 items-center justify-center rounded-xl bg-brand-50 text-brand-700 ring-1 ring-brand-100"><Icon name={icon} className="size-[18px]" /></span>
      </div>
      <AnimatedNumber value={value} className="relative mt-3 block text-3xl font-semibold tracking-tight text-slate-900 tabular-nums" />
      <p className={clsx("relative mt-1 flex items-center gap-1.5 text-xs", tone === "warning" ? "font-medium text-amber-800" : "text-slate-600")}>
        <span aria-hidden="true" className={clsx("size-1.5 rounded-full", tone === "warning" ? "bg-amber-500" : "bg-brand-500")} />
        {footnote}
      </p>
    </div>
  );
}

export default function ControlCenterPage() {
  const notify = useToast();
  const [overview, setOverview] = useState<Overview | null>(null);
  const [hospitals, setHospitals] = useState<Hospital[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updatedAt, setUpdatedAt] = useState<number | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [showTest, setShowTest] = useState(false);
  const [selectedSlug, setSelectedSlug] = useState<string | null>(null);
  const [provisionOpen, setProvisionOpen] = useState(false);
  const hour = useSyncExternalStore(subscribeNever, () => new Date().getHours(), () => -1);
  const tick = useSyncExternalStore(subscribeTicker, () => Math.floor(Date.now() / 10000), () => 0);

  useEffect(() => {
    let cancelled = false;
    Promise.all([request<Overview>(API), request<Hospital[]>(`${API}?action=hospitals`)])
      .then(([summary, list]) => {
        if (cancelled) return;
        setOverview(summary);
        setHospitals(Array.isArray(list) ? list : []);
        setError(null);
        setUpdatedAt(Date.now());
        const pending = window.sessionStorage.getItem(OPEN_HOSPITAL_KEY);
        if (pending) {
          window.sessionStorage.removeItem(OPEN_HOSPITAL_KEY);
          if (pending === "__add__") setProvisionOpen(true);
          else setSelectedSlug(pending);
        }
      })
      .catch((err: unknown) => {
        if (cancelled === false) setError(err instanceof Error ? err.message : "Could not load the control center.");
      })
      .finally(() => {
        if (cancelled === false) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [reloadKey]);

  useEffect(() => {
    const refresh = window.setInterval(() => setReloadKey((value) => value + 1), 60000);
    const openHospital = (event: Event) => setSelectedSlug(String((event as CustomEvent<string>).detail));
    const addHospital = () => setProvisionOpen(true);
    window.addEventListener(OPEN_HOSPITAL_EVENT, openHospital);
    window.addEventListener(ADD_HOSPITAL_EVENT, addHospital);
    return () => {
      window.clearInterval(refresh);
      window.removeEventListener(OPEN_HOSPITAL_EVENT, openHospital);
      window.removeEventListener(ADD_HOSPITAL_EVENT, addHospital);
    };
  }, []);

  const real = useMemo(() => hospitals.filter((hospital) => isTestHospital(hospital) === false), [hospitals]);
  const testCount = hospitals.length - real.length;
  const visible = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return (showTest ? hospitals : real).filter(
      (hospital) =>
        (statusFilter === "all" || hospital.status === statusFilter) &&
        (needle === "" || hospital.name.toLowerCase().includes(needle) || hospital.slug.includes(needle)),
    );
  }, [hospitals, real, showTest, query, statusFilter]);

  const greeting = hour < 0 ? "Welcome back" : hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";
  const alerts = count(overview?.unhealthy_integrations) + count(overview?.copilot_failed_executions) + count(overview?.hospitals_suspended);
  const seconds = updatedAt && tick > 0 ? Math.max(0, Math.round((tick * 10000 - updatedAt) / 1000)) : null;
  const freshness = seconds === null ? "Loading" : seconds < 30 ? "Updated just now" : `Updated ${Math.max(1, Math.round(seconds / 60))} min ago`;
  const scope = showTest ? hospitals : real;
  const byAppointments = [...scope].sort((a, b) => count(b.appointments) - count(a.appointments)).slice(0, 5).map((h) => ({ label: h.name, value: count(h.appointments) }));
  const byDoctors = [...scope].sort((a, b) => count(b.doctors) - count(a.doctors)).slice(0, 5).map((h) => ({ label: h.name, value: count(h.doctors) }));

  return (
    <ControlShell
      eyebrow={greeting}
      title="Platform overview"
      description={
        <span className="inline-flex flex-wrap items-center gap-x-3 gap-y-1">
          <span className={clsx("inline-flex items-center gap-1.5 font-medium", alerts > 0 ? "text-amber-800" : "text-brand-800")}>
            <span aria-hidden="true" className="relative flex size-2">
              <span className={clsx("absolute inline-flex size-full rounded-full opacity-60 motion-safe:animate-ping", alerts > 0 ? "bg-amber-400" : "bg-brand-400")} />
              <span className={clsx("relative inline-flex size-2 rounded-full", alerts > 0 ? "bg-amber-500" : "bg-brand-600")} />
            </span>
            {loading && overview === null ? "Checking the network" : alerts > 0 ? `${alerts} ${alerts === 1 ? "item needs" : "items need"} attention` : "All systems normal"}
          </span>
          <span>{freshness}</span>
        </span>
      }
      actions={
        <>
          <Button variant="secondary" onClick={() => setReloadKey((value) => value + 1)}>
            <Icon name="refresh" /> Refresh
          </Button>
          <Button onClick={() => setProvisionOpen(true)}>
            <Icon name="plus" /> Add hospital
          </Button>
        </>
      }
    >
      {error ? <div className="mb-6"><Alert title="Something went wrong">{error}</Alert></div> : null}

      {loading && overview === null ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {[0, 1, 2, 3].map((index) => <SkeletonBlock key={index} className="h-[132px] rounded-2xl" />)}
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <KpiCard icon="building" label="Hospitals" value={count(overview?.hospitals_total)} footnote={`${count(overview?.hospitals_active)} active, ${count(overview?.hospitals_suspended)} suspended`} tone={count(overview?.hospitals_suspended) > 0 ? "warning" : "neutral"} />
          <KpiCard icon="doctor" label="Doctors" value={count(overview?.doctors_total)} footnote={`${numberFormat.format(count(overview?.staff_total))} staff accounts`} />
          <KpiCard icon="calendar" label="Appointments" value={count(overview?.appointments_total)} footnote="Booked across all hospitals" />
          <KpiCard icon="plug" label="Integrations" value={count(overview?.integrations_total)} footnote={count(overview?.unhealthy_integrations) > 0 ? `${count(overview?.unhealthy_integrations)} need attention` : "None need attention"} tone={count(overview?.unhealthy_integrations) > 0 ? "warning" : "neutral"} />
        </div>
      )}

      <div className="mt-6 grid gap-6 lg:grid-cols-3">
        <Card className="p-6">
          <h2 className="text-base font-semibold text-slate-900">Appointments by hospital</h2>
          <p className="mt-0.5 text-sm text-slate-600">Busiest hospitals first.</p>
          <div className="mt-5">{loading && overview === null ? <SkeletonBlock className="h-40" /> : <BarList items={byAppointments} unit="booked" empty="No appointments booked yet." />}</div>
        </Card>
        <Card className="p-6">
          <h2 className="text-base font-semibold text-slate-900">Doctors by hospital</h2>
          <p className="mt-0.5 text-sm text-slate-600">Where patients have the most choice.</p>
          <div className="mt-5">{loading && overview === null ? <SkeletonBlock className="h-40" /> : <BarList items={byDoctors} unit="doctors" empty="No doctors listed yet." />}</div>
        </Card>
        <Card className="p-6">
          <h2 className="text-base font-semibold text-slate-900">Network status</h2>
          <p className="mt-0.5 text-sm text-slate-600">Hospitals by status.</p>
          <div className="mt-5">
            <Donut
              centerLabel="hospitals"
              centerValue={hospitals.length}
              segments={[
                { label: "Active", value: real.filter((h) => h.status === "active").length, color: "#3D7A5A", swatch: "bg-brand-600" },
                { label: "Suspended", value: real.filter((h) => h.status === "suspended").length, color: "#B42318", swatch: "bg-red-700" },
                { label: "Test", value: testCount, color: "#A9BDB1", swatch: "bg-slate-300" },
              ]}
            />
            <div className="mt-5 flex items-center gap-3 rounded-xl bg-brand-50/70 px-4 py-3 text-sm">
              <Icon name="sparkles" className="size-5 text-brand-700" />
              <span className="text-slate-700">
                AI copilot: <strong className="font-semibold text-slate-900">{numberFormat.format(count(overview?.copilot_proposals_total))}</strong> proposals,{" "}
                <strong className={clsx("font-semibold", count(overview?.copilot_failed_executions) > 0 ? "text-amber-800" : "text-slate-900")}>{numberFormat.format(count(overview?.copilot_failed_executions))}</strong> failed
              </span>
            </div>
          </div>
        </Card>
      </div>

      <Card className="mt-6 overflow-hidden">
        <div className="flex flex-col gap-4 border-b border-slate-200 px-6 py-5 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h2 className="text-base font-semibold text-slate-900">Hospitals</h2>
            <p className="mt-0.5 text-sm text-slate-600">{loading ? "Loading hospitals…" : `${visible.length} shown`}</p>
          </div>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <div className="relative">
              <label htmlFor="hospital-search" className="sr-only">Search hospitals</label>
              <Icon name="search" className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-500" />
              <input id="hospital-search" type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search by name or address" className="h-10 w-full rounded-xl border border-[#869489] bg-white pl-9 pr-3 text-sm text-slate-900 placeholder:text-slate-500 focus:border-brand-600 focus:outline-2 focus:outline-brand-600/30 sm:w-64" />
            </div>
            <div role="group" aria-label="Filter by status" className="flex rounded-xl bg-slate-100 p-1">
              {[["all", "All"], ["active", "Active"], ["suspended", "Suspended"]].map(([value, label]) => (
                <button key={value} type="button" aria-pressed={statusFilter === value} onClick={() => setStatusFilter(value)} className={clsx("rounded-lg px-3 py-1.5 text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-brand-700", statusFilter === value ? "bg-white text-slate-900 shadow-sm" : "text-slate-600 hover:text-slate-900")}>
                  {label}
                </button>
              ))}
            </div>
            {testCount > 0 ? (
              <button type="button" role="switch" aria-checked={showTest} onClick={() => setShowTest((value) => value === false)} className="flex items-center gap-2 rounded-lg text-sm text-slate-700 focus-visible:outline-2 focus-visible:outline-brand-700">
                <span className={clsx("relative h-5 w-9 rounded-full transition-colors", showTest ? "bg-brand-600" : "bg-slate-300")}>
                  <span className={clsx("absolute top-0.5 size-4 rounded-full bg-white shadow transition-transform", showTest ? "translate-x-4" : "translate-x-0.5")} />
                </span>
                Test hospitals ({testCount})
              </button>
            ) : null}
          </div>
        </div>
        <HospitalTable loading={loading} hospitals={visible} total={hospitals.length} onOpen={setSelectedSlug} onAdd={() => setProvisionOpen(true)} />
      </Card>

      {selectedSlug ? (
        <HospitalDrawer
          key={selectedSlug}
          slug={selectedSlug}
          onClose={() => setSelectedSlug(null)}
          onChanged={(message) => {
            notify(message);
            setReloadKey((value) => value + 1);
          }}
        />
      ) : null}

      <ProvisionDialog
        open={provisionOpen}
        onClose={() => setProvisionOpen(false)}
        onCreated={(slug, name) => {
          setProvisionOpen(false);
          notify(`${name} is ready. Its dashboard and chat assistant are live.`);
          setSelectedSlug(slug);
          setReloadKey((value) => value + 1);
        }}
      />
    </ControlShell>
  );
}

function HospitalTable({ loading, hospitals, total, onOpen, onAdd }: {
  loading: boolean; hospitals: Hospital[]; total: number; onOpen: (slug: string) => void; onAdd: () => void;
}) {
  if (loading && total === 0) {
    return <div className="space-y-3 px-6 py-6">{[0, 1, 2].map((index) => <SkeletonBlock key={index} className="h-14 rounded-xl" />)}</div>;
  }
  if (total === 0) {
    return <EmptyState title="No hospitals yet" description="Add the first hospital to give it a dashboard and a chat assistant." action={<Button onClick={onAdd}><Icon name="plus" /> Add hospital</Button>} />;
  }
  if (hospitals.length === 0) {
    return <EmptyState title="No hospitals match" description="Try another name, or change the status filter." />;
  }
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-left text-sm">
        <caption className="sr-only">Hospitals on MediBook</caption>
        <thead className="bg-slate-50/80 text-xs font-semibold uppercase tracking-wide text-slate-600">
          <tr>
            <th scope="col" className="px-6 py-3">Hospital</th>
            <th scope="col" className="px-3 py-3">Status</th>
            <th scope="col" className="hidden px-3 py-3 text-right sm:table-cell">Doctors</th>
            <th scope="col" className="hidden px-3 py-3 text-right sm:table-cell">Appointments</th>
            <th scope="col" className="hidden px-3 py-3 text-right md:table-cell">Staff</th>
            <th scope="col" className="hidden px-3 py-3 text-right lg:table-cell">Integrations</th>
            <th scope="col" className="px-6 py-3"><span className="sr-only">Open</span></th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {hospitals.map((hospital) => (
            <tr key={hospital.id} onClick={() => onOpen(hospital.slug)} className="group cursor-pointer transition-colors hover:bg-brand-50/50">
              <td className="px-6 py-3.5">
                <div className="flex items-center gap-3">
                  <Avatar hospital={hospital} />
                  <div className="min-w-0">
                    <p className="flex items-center gap-2 truncate font-medium text-slate-900">
                      {hospital.name}
                      {isTestHospital(hospital) ? <Badge>Test</Badge> : null}
                    </p>
                    <p className="truncate text-xs text-slate-600">{hospital.slug}{hospital.timezone ? ` · ${hospital.timezone}` : ""}</p>
                  </div>
                </div>
              </td>
              <td className="px-3 py-3.5">
                <Badge tone={statusTone(hospital.status)}>
                  <span aria-hidden="true" className={clsx("size-1.5 rounded-full", hospital.status === "active" ? "bg-brand-600" : hospital.status === "suspended" ? "bg-red-600" : "bg-slate-500")} />
                  {humanize(hospital.status)}
                </Badge>
              </td>
              <td className="hidden px-3 py-3.5 text-right tabular-nums text-slate-800 sm:table-cell">{numberFormat.format(count(hospital.doctors))}</td>
              <td className="hidden px-3 py-3.5 text-right tabular-nums text-slate-800 sm:table-cell">{numberFormat.format(count(hospital.appointments))}</td>
              <td className="hidden px-3 py-3.5 text-right tabular-nums text-slate-800 md:table-cell">{numberFormat.format(count(hospital.staff))}</td>
              <td className="hidden px-3 py-3.5 text-right tabular-nums text-slate-800 lg:table-cell">{numberFormat.format(count(hospital.integrations))}</td>
              <td className="px-6 py-3.5 text-right">
                <button
                  type="button"
                  onClick={(event) => {
                    event.stopPropagation();
                    onOpen(hospital.slug);
                  }}
                  aria-label={`Open ${hospital.name}`}
                  className="inline-flex items-center gap-1 rounded-lg px-2 py-1 text-sm font-medium text-brand-700 hover:bg-brand-50 focus-visible:outline-2 focus-visible:outline-brand-700"
                >
                  Open <Icon name="chevron" className="size-4 transition-transform group-hover:translate-x-0.5" />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function KeyValues({ title, values }: { title: string; values: Record<string, unknown> | null | undefined }) {
  const entries = Object.entries(values ?? {}).filter(([, value]) => value === null || ["string", "number", "boolean"].includes(typeof value));
  if (entries.length === 0) return null;
  return (
    <section>
      <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
      <dl className="mt-2 divide-y divide-slate-100 rounded-xl border border-slate-200">
        {entries.slice(0, 8).map(([key, value]) => (
          <div key={key} className="flex items-center justify-between gap-3 px-4 py-2.5 text-sm">
            <dt className="text-slate-600">{humanize(key)}</dt>
            <dd className="text-right font-medium text-slate-900">{displayValue(value)}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

function Timeline({ title, items, empty }: { title: string; items: Record<string, unknown>[] | undefined; empty: string }) {
  const list = Array.isArray(items) ? items.slice(0, 6) : [];
  return (
    <section>
      <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
      {list.length === 0 ? (
        <p className="mt-2 rounded-xl border border-dashed border-slate-300 px-4 py-6 text-center text-sm text-slate-600">{empty}</p>
      ) : (
        <ol className="mt-3 space-y-4 border-l border-slate-200 pl-5">
          {list.map((item, index) => {
            const when = eventTime(item);
            return (
              <li key={typeof item.id === "string" ? item.id : index} className="relative">
                <span aria-hidden="true" className="absolute -left-[25px] top-1.5 size-2.5 rounded-full border-2 border-white bg-brand-500 ring-1 ring-brand-200" />
                <p className="text-sm font-medium text-slate-900">{eventTitle(item)}</p>
                {when ? <p className="text-xs text-slate-600">{when}</p> : null}
              </li>
            );
          })}
        </ol>
      )}
    </section>
  );
}

function HospitalDrawer({ slug, onClose, onChanged }: { slug: string; onClose: () => void; onChanged: (message: string) => void }) {
  const notify = useToast();
  const titleId = useId();
  const [detail, setDetail] = useState<HospitalDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<"overview" | "activity" | "manage">("overview");
  const [reason, setReason] = useState("");
  const [saving, setSaving] = useState(false);
  const [version, setVersion] = useState(0);

  useEffect(() => {
    let cancelled = false;
    request<HospitalDetail>(`${API}?action=detail&hospital=${encodeURIComponent(slug)}`)
      .then((value) => {
        if (cancelled) return;
        setDetail(value);
        setError(null);
      })
      .catch((err: unknown) => {
        if (cancelled === false) setError(err instanceof Error ? err.message : "Could not load this hospital.");
      });
    return () => {
      cancelled = true;
    };
  }, [slug, version]);

  const nextStatus = detail?.status === "active" ? "suspended" : "active";
  const widgetPath = `/widget/${slug}`;

  async function changeStatus(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (detail === null) return;
    if (reason.trim().length < 2) {
      setError("Add a short reason. It is saved in the audit log.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await request<HospitalDetail>(`${API}?action=status&hospital=${encodeURIComponent(slug)}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: nextStatus, reason: reason.trim() }),
      });
      setReason("");
      setVersion((value) => value + 1);
      onChanged(nextStatus === "active" ? `${detail.name} is active again.` : `${detail.name} is suspended.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not change the status.");
    } finally {
      setSaving(false);
    }
  }

  async function copyLink() {
    try {
      await navigator.clipboard.writeText(`${window.location.origin}${widgetPath}`);
      notify("Chat link copied.");
    } catch {
      notify("Could not copy the link. Select it and copy it manually.", "error");
    }
  }

  const tabs: { id: "overview" | "activity" | "manage"; label: string }[] = [
    { id: "overview", label: "Overview" },
    { id: "activity", label: "Activity" },
    { id: "manage", label: "Manage" },
  ];
  const stats: [string, number][] = detail
    ? [["Doctors", count(detail.doctors)], ["Appointments", count(detail.appointments)], ["Staff", count(detail.staff)], ["Integrations", count(detail.integrations)], ["Schedule rules", count(detail.schedule_rules)], ["Exceptions", count(detail.schedule_exceptions)]]
    : [];

  return (
    <Drawer open onClose={onClose} labelledBy={titleId}>
      <div className="border-b border-slate-200 bg-gradient-to-b from-brand-50/80 to-white px-6 pb-4 pt-5">
        <div className="flex items-start gap-4">
          <Avatar hospital={{ slug, name: detail?.name ?? slug }} size="lg" />
          <div className="min-w-0 flex-1">
            <h2 id={titleId} className="truncate text-lg font-semibold tracking-tight text-slate-900">{detail?.name ?? "Loading…"}</h2>
            <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-slate-600">
              {detail ? <Badge tone={statusTone(detail.status)}>{humanize(detail.status)}</Badge> : null}
              <span>{slug}</span>
              {detail?.timezone ? <span>· {detail.timezone}</span> : null}
            </div>
          </div>
          <button type="button" onClick={onClose} aria-label="Close" className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 focus-visible:outline-2 focus-visible:outline-brand-700">
            <Icon name="close" className="size-5" />
          </button>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          <a href={widgetPath} target="_blank" rel="noreferrer" className="inline-flex h-9 items-center gap-2 rounded-lg bg-brand-600 px-3 text-sm font-semibold text-white hover:bg-brand-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-700">
            <Icon name="external" /> Open chat assistant
          </a>
          <Button size="sm" variant="secondary" className="h-9" onClick={copyLink}>
            <Icon name="copy" /> Copy link
          </Button>
        </div>
        <div role="tablist" aria-label="Hospital details" className="mt-5 flex gap-1">
          {tabs.map((item) => (
            <button
              key={item.id}
              id={`${titleId}-tab-${item.id}`}
              type="button"
              role="tab"
              aria-selected={tab === item.id}
              aria-controls={`${titleId}-panel`}
              onClick={() => setTab(item.id)}
              className={clsx("rounded-lg px-3 py-1.5 text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-brand-700", tab === item.id ? "bg-white text-slate-900 shadow-sm ring-1 ring-slate-200" : "text-slate-600 hover:text-slate-900")}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>
      <div id={`${titleId}-panel`} role="tabpanel" aria-labelledby={`${titleId}-tab-${tab}`} className="flex-1 space-y-6 overflow-y-auto px-6 py-6">
        {error ? <Alert>{error}</Alert> : null}
        {detail === null && error === null ? (
          <div className="space-y-3"><SkeletonBlock className="h-24 rounded-xl" /><SkeletonBlock className="h-40 rounded-xl" /></div>
        ) : null}
        {detail && tab === "overview" ? (
          <>
            <dl className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              {stats.map(([label, value]) => (
                <div key={label} className="rounded-xl border border-slate-200 bg-white px-4 py-3">
                  <dt className="text-xs font-medium text-slate-600">{label}</dt>
                  <dd className="mt-1 text-xl font-semibold tabular-nums text-slate-900">{numberFormat.format(value)}</dd>
                </div>
              ))}
            </dl>
            <div className="flex flex-wrap gap-2">
              <Badge tone="blue">{humanize(detail.data_mode ?? "managed")} doctor data</Badge>
              {isTestHospital(detail) ? <Badge>Test hospital</Badge> : null}
            </div>
            <KeyValues title="Usage" values={detail.usage} />
            <KeyValues title="Integration health" values={detail.integration_health} />
            <KeyValues title="Security" values={detail.security} />
          </>
        ) : null}
        {detail && tab === "activity" ? (
          <>
            <Timeline title="Recent appointments" items={detail.recent_appointments} empty="No appointments yet." />
            <Timeline title="Platform events" items={detail.recent_platform_events} empty="No platform events yet." />
            <Timeline title="Integrations" items={detail.recent_integrations} empty="No integrations connected yet." />
          </>
        ) : null}
        {detail && tab === "manage" ? (
          <form onSubmit={changeStatus} className={clsx("space-y-4 rounded-2xl border p-5", nextStatus === "suspended" ? "border-red-200 bg-red-50/40" : "border-brand-200 bg-brand-50/40")}>
            <div className="flex items-start gap-3">
              <Icon name={nextStatus === "suspended" ? "alert" : "check"} className={clsx("mt-0.5 size-5", nextStatus === "suspended" ? "text-red-700" : "text-brand-700")} />
              <div>
                <p className="text-sm font-semibold text-slate-900">{nextStatus === "suspended" ? "Suspend this hospital" : "Reactivate this hospital"}</p>
                <p className="mt-1 text-sm text-slate-600">
                  {nextStatus === "suspended" ? "The hospital stays suspended across MediBook until you reactivate it." : "The hospital becomes active across MediBook again."}
                </p>
              </div>
            </div>
            <TextareaField label="Reason" hint="Saved in the audit log." rows={3} value={reason} onChange={(event) => setReason(event.target.value)} />
            <Button type="submit" variant={nextStatus === "suspended" ? "danger" : "primary"} loading={saving}>
              {nextStatus === "suspended" ? "Suspend hospital" : "Reactivate hospital"}
            </Button>
          </form>
        ) : null}
      </div>
    </Drawer>
  );
}

function ProvisionDialog({ open, onClose, onCreated }: { open: boolean; onClose: () => void; onCreated: (slug: string, name: string) => void }) {
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [slugEdited, setSlugEdited] = useState(false);
  const [timezone, setTimezone] = useState("Asia/Dhaka");
  const [email, setEmail] = useState("");
  const [dataMode, setDataMode] = useState("managed");
  const [activate, setActivate] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const effectiveSlug = slugEdited ? slug : slugify(name);
  const slugValid = effectiveSlug.length >= 2 && /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(effectiveSlug);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (name.trim().length < 2) return setError("Enter the hospital’s name.");
    if (slugValid === false) return setError("The web address can use lowercase letters, numbers and single dashes.");
    if (email.includes("@") === false) return setError("Enter the administrator’s email address.");
    setSaving(true);
    setError(null);
    try {
      const created = await request<Partial<HospitalDetail>>(`${API}?action=provision`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: name.trim(), slug: effectiveSlug, timezone, initial_admin_email: email.trim(), data_mode: dataMode, activate }),
      });
      setName("");
      setSlug("");
      setSlugEdited(false);
      setEmail("");
      onCreated(created.slug || effectiveSlug, created.name || name.trim());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not add the hospital.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Dialog open={open} onClose={onClose} title="Add a hospital" description="It gets its own dashboard and chat assistant straight away. The administrator needs a MediBook account already.">
      <form onSubmit={submit} className="space-y-4">
        {error ? <Alert>{error}</Alert> : null}
        <InputField label="Hospital name" placeholder="Dhaka General Hospital" autoComplete="organization" value={name} onChange={(event) => setName(event.target.value)} data-autofocus />
        <InputField
          label="Web address"
          hint={`Patients will chat at /widget/${effectiveSlug || "your-hospital"}`}
          value={effectiveSlug}
          onChange={(event) => {
            setSlugEdited(true);
            setSlug(event.target.value.toLowerCase());
          }}
        />
        <InputField label="Administrator email" type="email" placeholder="admin@hospital.com" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} />
        <div className="grid gap-4 sm:grid-cols-2">
          <SelectField label="Time zone" value={timezone} onChange={(event) => setTimezone(event.target.value)}>
            {TIMEZONES.map((zone) => <option key={zone} value={zone}>{zone}</option>)}
          </SelectField>
          <SelectField label="Doctor data" value={dataMode} onChange={(event) => setDataMode(event.target.value)}>
            <option value="managed">Managed in MediBook</option>
            <option value="connected">From the hospital’s system</option>
            <option value="hybrid">Both</option>
          </SelectField>
        </div>
        <CheckboxField label="Activate now" hint="Leave this off to set the hospital up before patients can use it." checked={activate} onChange={(event) => setActivate(event.target.checked)} />
        <div className="flex justify-end gap-2 border-t border-slate-200 pt-4">
          <Button variant="secondary" onClick={onClose}>Cancel</Button>
          <Button type="submit" loading={saving}><Icon name="plus" /> Add hospital</Button>
        </div>
      </form>
    </Dialog>
  );
}
