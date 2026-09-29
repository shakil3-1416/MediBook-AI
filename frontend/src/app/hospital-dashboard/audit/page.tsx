"use client";

import {
  ClipboardList,
  RefreshCw,
  Search,
} from "lucide-react";

import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  displayValue,
  hospitalOpsRequest,
  normalizeCollection,
} from "@/lib/hospital-ops";


export default function HospitalAuditPage() {
  const [
    entries,
    setEntries,
  ] =
    useState<
      Record<
        string,
        unknown
      >[]
    >([]);

  const [
    search,
    setSearch,
  ] =
    useState("");

  const [
    loading,
    setLoading,
  ] =
    useState(true);

  const [
    error,
    setError,
  ] =
    useState<
      string | null
    >(null);


  async function load() {
    setLoading(true);
    setError(null);

    try {
      const response =
        await hospitalOpsRequest<
          unknown
        >(
          "/api/dashboard/hospital-admin?resource=audit",
        );

      setEntries(
        normalizeCollection(
          response,
        ),
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not load audit log.",
      );
    } finally {
      setLoading(false);
    }
  }


  useEffect(
    () => {
      queueMicrotask(
        () => {
          void load();
        },
      );
    },
    [],
  );


  const filtered =
    useMemo(
      () => {
        const needle =
          search
            .trim()
            .toLowerCase();

        if (!needle) {
          return entries;
        }

        return entries.filter(
          (entry) =>
            JSON.stringify(
              entry,
            )
              .toLowerCase()
              .includes(
                needle,
              ),
        );
      },
      [
        entries,
        search,
      ],
    );


  return (
    <main className="p-5 md:p-8">
      <div className="mx-auto max-w-7xl">
        <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
          <div>
            <div className="flex items-center gap-2 text-sm font-semibold text-purple-600">
              <ClipboardList size={16} />
              Governance
            </div>

            <h1 className="mt-2 text-3xl font-semibold tracking-tight">
              Audit Log
            </h1>

            <p className="mt-2 text-sm text-slate-500">
              Search operational actions recorded for this hospital.
            </p>
          </div>

          <button
            type="button"
            onClick={() => void load()}
            className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium"
          >
            <RefreshCw size={16} />
            Refresh
          </button>
        </div>

        <div className="mt-6 rounded-2xl border border-slate-200 bg-white p-4">
          <div className="relative">
            <Search
              size={17}
              className="absolute left-3 top-3 text-slate-400"
            />

            <input
              value={search}
              onChange={
                (event) =>
                  setSearch(
                    event.target.value,
                  )
              }
              placeholder="Search action, actor, entity, ID or date"
              className="w-full rounded-xl border border-slate-200 py-2.5 pl-10 pr-4 text-sm outline-none focus:border-purple-400"
            />
          </div>
        </div>

        {error ? (
          <div className="mt-6 rounded-2xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-700">
            {error}
          </div>
        ) : null}

        <div className="mt-6 overflow-hidden rounded-2xl border border-slate-200 bg-white">
          {loading ? (
            <div className="p-8 text-sm text-slate-500">
              Loading audit log...
            </div>
          ) : filtered.length === 0 ? (
            <div className="p-8 text-sm text-slate-500">
              No audit entries found.
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {filtered.map(
                (
                  entry,
                  index,
                ) => (
                  <div
                    key={
                      String(
                        entry.id ??
                        entry.audit_id ??
                        index,
                      )
                    }
                    className="grid gap-4 p-5 md:grid-cols-[1fr_1fr_1fr_1.2fr]"
                  >
                    <div>
                      <div className="text-xs uppercase tracking-wide text-slate-400">
                        Action
                      </div>
                      <div className="mt-1 text-sm font-medium">
                        {displayValue(
                          entry.action ??
                          entry.event,
                        )}
                      </div>
                    </div>

                    <div>
                      <div className="text-xs uppercase tracking-wide text-slate-400">
                        Actor
                      </div>
                      <div className="mt-1 text-sm">
                        {displayValue(
                          entry.actor ??
                          entry.actor_email ??
                          entry.user_id,
                        )}
                      </div>
                    </div>

                    <div>
                      <div className="text-xs uppercase tracking-wide text-slate-400">
                        Entity
                      </div>
                      <div className="mt-1 text-sm">
                        {displayValue(
                          entry.entity ??
                          entry.entity_type ??
                          entry.resource,
                        )}
                      </div>
                    </div>

                    <div>
                      <div className="text-xs uppercase tracking-wide text-slate-400">
                        Time
                      </div>
                      <div className="mt-1 text-sm">
                        {displayValue(
                          entry.created_at ??
                          entry.timestamp ??
                          entry.occurred_at,
                        )}
                      </div>
                    </div>
                  </div>
                ),
              )}
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
