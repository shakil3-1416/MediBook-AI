"use client";

import {
  Save,
  Settings,
} from "lucide-react";

import {
  useEffect,
  useState,
} from "react";

import {
  hospitalOpsRequest,
} from "@/lib/hospital-ops";

import {
  useHospitalWorkspace,
} from "@/components/hospital/hospital-workspace-context";


const backendCanUpdate =
  true;


export default function HospitalSettingsPage() {
  const {
    activeWorkspace,
  } =
    useHospitalWorkspace();

  const roleCanUpdate =
    activeWorkspace?.role ===
      "hospital_admin";

  const canUpdate =
    backendCanUpdate &&
    roleCanUpdate;

  const [
    settings,
    setSettings,
  ] =
    useState<
      Record<
        string,
        unknown
      >
    >({});

  const [
    draft,
    setDraft,
  ] =
    useState("");

  const [
    loading,
    setLoading,
  ] =
    useState(true);

  const [
    saving,
    setSaving,
  ] =
    useState(false);

  const [
    error,
    setError,
  ] =
    useState<
      string | null
    >(null);

  const [
    success,
    setSuccess,
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
          Record<
            string,
            unknown
          >
        >(
          "/api/dashboard/hospital-admin?resource=settings",
        );

      setSettings(
        response,
      );

      setDraft(
        JSON.stringify(
          response,
          null,
          2,
        ),
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not load settings.",
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


  async function save() {
    if (!canUpdate) {
      return;
    }

    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      const payload =
        JSON.parse(
          draft,
        ) as Record<
          string,
          unknown
        >;

      const response =
        await hospitalOpsRequest<
          Record<
            string,
            unknown
          >
        >(
          "/api/dashboard/hospital-admin?resource=settings",
          {
            method:
              "PATCH",
            body:
              JSON.stringify(
                payload,
              ),
          },
        );

      setSettings(
        response,
      );

      setDraft(
        JSON.stringify(
          response,
          null,
          2,
        ),
      );

      setSuccess(
        "Hospital settings updated.",
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not save settings.",
      );
    } finally {
      setSaving(false);
    }
  }


  return (
    <main className="p-5 md:p-8">
      <div className="mx-auto max-w-5xl">
        <div className="flex items-center gap-2 text-sm font-semibold text-brand-600">
          <Settings size={16} />
          Configuration
        </div>

        <h1 className="mt-2 text-3xl font-semibold tracking-tight">
          Settings
        </h1>

        <p className="mt-2 text-sm text-slate-500">
          Hospital-level configuration for the active workspace.
        </p>

        {error ? (
          <div className="mt-6 rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
            {error}
          </div>
        ) : null}

        {success ? (
          <div className="mt-6 rounded-2xl border border-brand-200 bg-brand-50 p-4 text-sm text-brand-700">
            {success}
          </div>
        ) : null}

        <div className="mt-6 rounded-2xl border border-slate-200 bg-white p-6">
          {loading ? (
            <div className="text-sm text-slate-500">
              Loading settings...
            </div>
          ) : (
            <>
              <div className="mb-3 text-sm font-medium text-slate-700">
                Configuration
              </div>

              <textarea
                value={draft}
                onChange={
                  (event) =>
                    setDraft(
                      event.target.value,
                    )
                }
                spellCheck={false}
                className="min-h-[420px] w-full rounded-xl border border-slate-200 bg-slate-950 p-4 font-mono text-xs leading-6 text-slate-100 outline-none focus:border-brand-400"
              />

              <div className="mt-4 flex items-center justify-between gap-4">
                <div className="text-xs text-slate-500">
                  {
                    canUpdate
                      ? "Changes are validated by the backend before persistence."
                      : "The current backend exposes settings as read-only."
                  }
                </div>

                <button
                  type="button"
                  disabled={
                    saving ||
                    !canUpdate
                  }
                  onClick={
                    () =>
                      void save()
                  }
                  className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-40"
                >
                  <Save size={16} />

                  {
                    saving
                      ? "Saving..."
                      : "Save settings"
                  }
                </button>
              </div>
            </>
          )}
        </div>

        <div className="mt-6 hidden">
          {
            JSON.stringify(
              settings,
            )
          }
        </div>
      </div>
    </main>
  );
}
