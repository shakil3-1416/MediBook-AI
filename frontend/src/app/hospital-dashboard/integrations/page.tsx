"use client";

import {
  useEffect,
  useState,
} from "react";


type Integration = {
  id: string;
  provider: string;
  integration_type: string;
  source_mode: string;
  status: string;
  sync_status: string;
  ownership: Record<string, string>;
  has_secrets: boolean;
  last_checked_at: string | null;
  last_error: string | null;
};


const HOSPITAL =
  "";


export default function IntegrationsPage() {
  const [
    integrations,
    setIntegrations,
  ] = useState<Integration[]>([]);

  const [
    provider,
    setProvider,
  ] = useState("");

  const [
    mode,
    setMode,
  ] = useState("managed");

  const [
    error,
    setError,
  ] = useState<string | null>(
    null,
  );


  async function load() {
    const response =
      await fetch(
        `/api/dashboard/hospital-integrations?hospital=${HOSPITAL}`,
        {
          cache:
            "no-store",
        },
      );

    if (!response.ok) {
      throw new Error(
        await response.text(),
      );
    }

    const data =
      await response.json();

    setIntegrations(
      data.integrations ?? [],
    );
  }


  useEffect(
    () => {
      queueMicrotask(() => {
        void load().catch(
          (value) =>
            setError(
              String(value),
            ),
        );
      });
    },
    [],
  );


  async function create() {
    setError(null);

    const ownership =
      mode === "hybrid"
        ? {
            doctors: "connected",
            schedules: "connected",
            appointments: "managed",
          }
        : {};

    const response =
      await fetch(
        `/api/dashboard/hospital-integrations?hospital=${HOSPITAL}`,
        {
          method:
            "POST",
          headers: {
            "Content-Type":
              "application/json",
          },
          body:
            JSON.stringify({
              provider,
              integration_type:
                "hms",
              source_mode:
                mode,
              ownership,
              config: {},
            }),
        },
      );

    if (!response.ok) {
      setError(
        await response.text(),
      );

      return;
    }

    setProvider("");

    await load();
  }


  async function health(
    id: string,
  ) {
    const response =
      await fetch(
        `/api/dashboard/hospital-integrations?hospital=${HOSPITAL}&id=${encodeURIComponent(id)}&health=1`,
        {
          method:
            "POST",
        },
      );

    if (!response.ok) {
      setError(
        await response.text(),
      );

      return;
    }

    await load();
  }


  return (
    <main className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
          <div>
            <div className="text-sm font-semibold text-brand-600">
              MediBook Hospital Operations
            </div>

            <h1 className="mt-1 text-2xl font-semibold">
              Integration Center
            </h1>

            <p className="mt-1 text-sm text-slate-500">
              Data ownership, connector health and integration status
            </p>
          </div>

        </div>
      </header>

      <div className="mx-auto max-w-7xl space-y-6 px-6 py-8">
        {error && (
          <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
            {error}
          </div>
        )}

        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="font-semibold">
            Add integration
          </h2>

          <div className="mt-4 grid gap-3 md:grid-cols-3">
            <input
              value={provider}
              onChange={
                (event) =>
                  setProvider(
                    event.target.value,
                  )
              }
              placeholder="Provider name"
              className="rounded-xl border border-slate-300 px-3 py-2"
            />

            <select
              value={mode}
              onChange={
                (event) =>
                  setMode(
                    event.target.value,
                  )
              }
              className="rounded-xl border border-slate-300 px-3 py-2"
            >
              <option value="managed">
                Managed
              </option>
              <option value="connected">
                Connected
              </option>
              <option value="hybrid">
                Hybrid
              </option>
            </select>

            <button
              type="button"
              disabled={!provider.trim()}
              onClick={
                () => void create()
              }
              className="rounded-xl bg-brand-600 px-4 py-2 font-medium text-white disabled:opacity-40"
            >
              Add integration
            </button>
          </div>
        </section>

        <section className="grid gap-4 lg:grid-cols-2">
          {integrations.map(
            (item) => (
              <article
                key={item.id}
                className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h2 className="font-semibold text-slate-950">
                      {item.provider}
                    </h2>

                    <p className="mt-1 text-sm text-slate-500">
                      {item.source_mode}
                      {" · "}
                      {item.integration_type}
                    </p>
                  </div>

                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium">
                    {item.status}
                  </span>
                </div>

                <div className="mt-5 space-y-2 text-sm">
                  {Object.entries(
                    item.ownership,
                  ).map(
                    ([domain, owner]) => (
                      <div
                        key={domain}
                        className="flex justify-between"
                      >
                        <span className="capitalize text-slate-500">
                          {domain}
                        </span>
                        <span className="font-medium">
                          {owner}
                        </span>
                      </div>
                    ),
                  )}
                </div>

                {item.last_error && (
                  <div className="mt-4 rounded-xl bg-amber-50 p-3 text-sm text-amber-800">
                    {item.last_error}
                  </div>
                )}

                <button
                  type="button"
                  onClick={
                    () =>
                      void health(
                        item.id,
                      )
                  }
                  className="mt-5 rounded-xl border border-brand-200 bg-brand-50 px-4 py-2 text-sm font-medium text-brand-700"
                >
                  Check health
                </button>
              </article>
            ),
          )}
        </section>
      </div>
    </main>
  );
}
