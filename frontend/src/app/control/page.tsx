"use client";

import {
  Activity,
  Building2,
  Plus,
  RefreshCw,
  Search,
  ShieldCheck,
} from "lucide-react";

import {
  FormEvent,
  useEffect,
  useMemo,
  useState,
} from "react";


type Overview = {
  hospitals_total: number;
  hospitals_active: number;
  hospitals_suspended: number;
  appointments_total: number;
  doctors_total: number;
  staff_total: number;
  integrations_total: number;
  unhealthy_integrations: number;
  copilot_proposals_total: number;
  copilot_failed_executions: number;
};


type Hospital = {
  id: string;
  slug: string;
  name: string;
  timezone?: string | null;
  status: string;
  data_mode?: string | null;
  doctors: number;
  appointments: number;
  staff: number;
  integrations: number;
  schedule_rules: number;
  schedule_exceptions: number;
  integration_health:
    Record<
      string,
      unknown
    >;
  security:
    Record<
      string,
      unknown
    >;
  usage:
    Record<
      string,
      unknown
    >;
};


type HospitalDetail =
  Hospital & {
    recent_integrations:
      Record<
        string,
        unknown
      >[];

    recent_appointments:
      Record<
        string,
        unknown
      >[];

    recent_platform_events:
      Record<
        string,
        unknown
      >[];
  };


async function api<T>(
  url: string,
  options?: RequestInit,
): Promise<T> {
  const response =
    await fetch(
      url,
      {
        cache:
          "no-store",
        ...options,
      },
    );

  const raw =
    await response.text();

  if (!response.ok) {
    try {
      const parsed =
        JSON.parse(
          raw,
        ) as {
          detail?: unknown;
        };

      if (
        typeof parsed.detail ===
        "string"
      ) {
        throw new Error(
          parsed.detail,
        );
      }
    } catch (
      error
    ) {
      if (
        error instanceof Error &&
        error.message !==
          raw
      ) {
        throw error;
      }
    }

    throw new Error(
      raw ||
      `Request failed (${response.status}).`,
    );
  }

  return JSON.parse(
    raw,
  ) as T;
}


export default function ControlCenterPage() {
  const [
    overview,
    setOverview,
  ] =
    useState<
      Overview | null
    >(null);

  const [
    hospitals,
    setHospitals,
  ] =
    useState<
      Hospital[]
    >([]);

  const [
    selected,
    setSelected,
  ] =
    useState<
      HospitalDetail | null
    >(null);

  const [
    search,
    setSearch,
  ] =
    useState("");

  const [
    error,
    setError,
  ] =
    useState<
      string | null
    >(null);

  const [
    loading,
    setLoading,
  ] =
    useState(true);

  const [
    provisionOpen,
    setProvisionOpen,
  ] =
    useState(false);

  const [
    busy,
    setBusy,
  ] =
    useState(false);


  async function load() {
    setLoading(true);
    setError(null);

    try {
      const [
        summary,
        hospitalList,
      ] =
        await Promise.all([
          api<Overview>(
            "/api/dashboard/platform-control-v2",
          ),

          api<Hospital[]>(
            "/api/dashboard/platform-control-v2?action=hospitals",
          ),
        ]);

      setOverview(
        summary
      );

      setHospitals(
        hospitalList
      );

    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : (
              "Could not load Control Center."
            ),
      );

    } finally {
      setLoading(false);
    }
  }


  useEffect(
    () => {
      const timer =
        window.setTimeout(
          () => {
            void load();
          },
          0,
        );

      return () => {
        window.clearTimeout(
          timer
        );
      };
    },
    [],
  );


  async function openHospital(
    hospital: Hospital,
  ) {
    setError(null);

    try {
      const detail =
        await api<
          HospitalDetail
        >(
          `/api/dashboard/platform-control-v2?action=detail&hospital=${encodeURIComponent(
            hospital.slug,
          )}`,
        );

      setSelected(
        detail
      );

    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : (
              "Could not load hospital."
            ),
      );
    }
  }


  async function changeStatus(
    hospital:
      HospitalDetail,
  ) {
    const suspended =
      hospital.status ===
      "suspended";

    const status =
      suspended
        ? "active"
        : "suspended";

    const reason =
      window.prompt(
        suspended
          ? "Reason for activating this hospital"
          : "Reason for suspending this hospital",
      );

    if (!reason) {
      return;
    }

    setBusy(true);
    setError(null);

    try {
      const detail =
        await api<
          HospitalDetail
        >(
          `/api/dashboard/platform-control-v2?action=status&hospital=${encodeURIComponent(
            hospital.slug,
          )}`,
          {
            method:
              "PATCH",

            headers: {
              "Content-Type":
                "application/json",
            },

            body:
              JSON.stringify(
                {
                  status,
                  reason,
                },
              ),
          },
        );

      setSelected(
        detail
      );

      await load();

    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : (
              "Status update failed."
            ),
      );

    } finally {
      setBusy(false);
    }
  }


  const filtered =
    useMemo(
      () => {
        const needle =
          search
            .trim()
            .toLowerCase();

        if (!needle) {
          return hospitals;
        }

        return hospitals.filter(
          (
            hospital,
          ) =>
            (
              hospital.name
              .toLowerCase()
              .includes(
                needle
              )
              ||
              hospital.slug
              .toLowerCase()
              .includes(
                needle
              )
            ),
        );
      },
      [
        hospitals,
        search,
      ],
    );


  const cards = [
    [
      "Hospitals",
      overview?.hospitals_total ??
        0,
    ],

    [
      "Active",
      overview?.hospitals_active ??
        0,
    ],

    [
      "Appointments",
      overview?.appointments_total ??
        0,
    ],

    [
      "Doctors",
      overview?.doctors_total ??
        0,
    ],

    [
      "Integrations",
      overview?.integrations_total ??
        0,
    ],

    [
      "Integration alerts",
      overview?.unhealthy_integrations ??
        0,
    ],

    [
      "Copilot proposals",
      overview?.copilot_proposals_total ??
        0,
    ],

    [
      "Copilot failures",
      overview?.copilot_failed_executions ??
        0,
    ],
  ] as const;


  return (
    <main className="min-h-screen bg-slate-50 text-slate-950">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-[1600px] items-center justify-between gap-4 px-5 py-5 md:px-8">
          <div>
            <div className="flex items-center gap-2 text-sm font-semibold text-brand-600">
              <ShieldCheck
                size={17}
              />

              MediBook Platform
            </div>

            <h1 className="mt-1 text-2xl font-semibold tracking-tight">
              Control Center
            </h1>

            <p className="mt-1 text-sm text-slate-500">
              Hospital provisioning, operations health, usage and security.
            </p>
          </div>

          <div className="flex gap-2">
            <button
              type="button"
              onClick={
                () =>
                  void load()
              }
              className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium"
            >
              <RefreshCw
                size={15}
              />
              Refresh
            </button>

            <button
              type="button"
              onClick={
                () =>
                  setProvisionOpen(
                    true
                  )
              }
              className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white"
            >
              <Plus
                size={15}
              />
              Provision hospital
            </button>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-[1600px] px-5 py-6 md:px-8">
        {error ? (
          <div className="mb-5 rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
            {
              error
            }
          </div>
        ) : null}

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-8">
          {
            cards.map(
              (
                [
                  label,
                  value,
                ],
              ) => (
                <div
                  key={
                    label
                  }
                  className="rounded-2xl border border-slate-200 bg-white p-4"
                >
                  <div className="text-xs font-medium text-slate-500">
                    {
                      label
                    }
                  </div>

                  <div className="mt-2 text-2xl font-semibold">
                    {
                      value
                    }
                  </div>
                </div>
              ),
            )
          }
        </div>

        <div className="mt-6 grid gap-6 xl:grid-cols-[1.15fr_.85fr]">
          <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
            <div className="border-b border-slate-100 p-4">
              <div className="relative">
                <Search
                  size={16}
                  className="absolute left-3 top-3 text-slate-400"
                />

                <input
                  value={
                    search
                  }
                  onChange={
                    (
                      event,
                    ) =>
                      setSearch(
                        event.target.value
                      )
                  }
                  placeholder="Search hospitals"
                  className="w-full rounded-xl border border-slate-200 py-2.5 pl-9 pr-3 text-sm outline-none focus:border-brand-400"
                />
              </div>
            </div>

            {loading ? (
              <div className="p-8 text-sm text-slate-500">
                Loading hospitals...
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {
                  filtered.map(
                    (
                      hospital,
                    ) => (
                      <button
                        key={
                          hospital.id
                        }
                        type="button"
                        onClick={
                          () =>
                            void openHospital(
                              hospital
                            )
                        }
                        className="grid w-full gap-3 p-5 text-left transition hover:bg-slate-50 md:grid-cols-[1.4fr_.8fr_.8fr_.8fr]"
                      >
                        <div>
                          <div className="flex items-center gap-2 font-semibold">
                            <Building2
                              size={16}
                              className="text-brand-600"
                            />

                            {
                              hospital.name
                            }
                          </div>

                          <div className="mt-1 text-xs text-slate-500">
                            {
                              hospital.slug
                            }
                            {" · "}
                            {
                              hospital.timezone
                            }
                          </div>
                        </div>

                        <div>
                          <div className="text-xs text-slate-400">
                            Status
                          </div>

                          <div className="mt-1 text-sm font-medium">
                            {
                              hospital.status
                            }
                          </div>

                          <div className="mt-1 text-xs text-slate-500">
                            {
                              hospital.data_mode
                            }
                          </div>
                        </div>

                        <div>
                          <div className="text-xs text-slate-400">
                            Operations
                          </div>

                          <div className="mt-1 text-sm">
                            {
                              hospital.doctors
                            } doctors
                          </div>

                          <div className="text-xs text-slate-500">
                            {
                              hospital.appointments
                            } appointments
                          </div>
                        </div>

                        <div>
                          <div className="text-xs text-slate-400">
                            Health
                          </div>

                          <div className="mt-1 flex items-center gap-1 text-sm">
                            <Activity
                              size={14}
                            />

                            {
                              hospital.integrations
                            } integrations
                          </div>

                          <div className="text-xs text-slate-500">
                            {
                              hospital.staff
                            } staff
                          </div>
                        </div>
                      </button>
                    ),
                  )
                }
              </div>
            )}
          </section>

          <section className="rounded-2xl border border-slate-200 bg-white p-5">
            {!selected ? (
              <div className="flex min-h-80 items-center justify-center text-center">
                <div>
                  <Building2
                    size={28}
                    className="mx-auto text-slate-300"
                  />

                  <p className="mt-3 text-sm text-slate-500">
                    Select a hospital for platform-level drilldown.
                  </p>
                </div>
              </div>
            ) : (
              <div>
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h2 className="text-xl font-semibold">
                      {
                        selected.name
                      }
                    </h2>

                    <p className="mt-1 text-xs text-slate-500">
                      {
                        selected.slug
                      }
                      {" · "}
                      {
                        selected.timezone
                      }
                    </p>
                  </div>

                  <button
                    type="button"
                    disabled={
                      busy
                    }
                    onClick={
                      () =>
                        void changeStatus(
                          selected
                        )
                    }
                    className={[
                      "rounded-xl px-3 py-2 text-xs font-semibold",
                      selected.status ===
                      "suspended"
                        ? "bg-brand-600 text-white"
                        : "border border-rose-200 text-rose-700",
                    ].join(
                      " ",
                    )}
                  >
                    {
                      selected.status ===
                      "suspended"
                        ? "Activate"
                        : "Suspend"
                    }
                  </button>
                </div>

                <div className="mt-5 grid grid-cols-2 gap-3">
                  {
                    [
                      [
                        "Doctors",
                        selected.doctors,
                      ],

                      [
                        "Appointments",
                        selected.appointments,
                      ],

                      [
                        "Staff",
                        selected.staff,
                      ],

                      [
                        "Integrations",
                        selected.integrations,
                      ],

                      [
                        "Rules",
                        selected.schedule_rules,
                      ],

                      [
                        "Exceptions",
                        selected.schedule_exceptions,
                      ],
                    ].map(
                      (
                        [
                          label,
                          value,
                        ],
                      ) => (
                        <div
                          key={
                            label
                          }
                          className="rounded-xl bg-slate-50 p-3"
                        >
                          <div className="text-xs text-slate-500">
                            {
                              label
                            }
                          </div>

                          <div className="mt-1 text-lg font-semibold">
                            {
                              value
                            }
                          </div>
                        </div>
                      ),
                    )
                  }
                </div>

                <div className="mt-5">
                  <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Integration health
                  </div>

                  <pre className="mt-2 overflow-x-auto rounded-xl bg-slate-950 p-3 text-xs text-slate-100">
                    {
                      JSON.stringify(
                        selected.integration_health,
                        null,
                        2,
                      )
                    }
                  </pre>
                </div>

                <div className="mt-5">
                  <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Recent platform activity
                  </div>

                  <div className="mt-2 space-y-2">
                    {
                      selected.recent_platform_events.length ===
                      0 ? (
                        <div className="rounded-xl bg-slate-50 p-3 text-xs text-slate-500">
                          No platform-control events yet.
                        </div>
                      ) : (
                        selected.recent_platform_events.map(
                          (
                            item,
                            index,
                          ) => (
                            <div
                              key={
                                String(
                                  item.id ??
                                  index
                                )
                              }
                              className="rounded-xl bg-slate-50 p-3"
                            >
                              <div className="text-xs font-semibold">
                                {
                                  String(
                                    item.event_type ??
                                    "event"
                                  )
                                }
                              </div>

                              <div className="mt-1 text-[11px] text-slate-500">
                                {
                                  String(
                                    item.created_at ??
                                    ""
                                  )
                                }
                              </div>
                            </div>
                          ),
                        )
                      )
                    }
                  </div>
                </div>
              </div>
            )}
          </section>
        </div>
      </div>

      {provisionOpen ? (
        <ProvisionHospital
          busy={
            busy
          }
          onClose={
            () =>
              setProvisionOpen(
                false
              )
          }
          onSubmit={
            async (
              payload,
            ) => {
              setBusy(true);
              setError(null);

              try {
                const created =
                  await api<
                    HospitalDetail
                  >(
                    "/api/dashboard/platform-control-v2?action=provision",
                    {
                      method:
                        "POST",

                      headers: {
                        "Content-Type":
                          "application/json",
                      },

                      body:
                        JSON.stringify(
                          payload
                        ),
                    },
                  );

                setProvisionOpen(
                  false
                );

                setSelected(
                  created
                );

                await load();

              } catch (err) {
                setError(
                  err instanceof Error
                    ? err.message
                    : (
                        "Hospital provisioning failed."
                      ),
                );

              } finally {
                setBusy(false);
              }
            }
          }
        />
      ) : null}
    </main>
  );
}


function ProvisionHospital(
  {
    busy,
    onClose,
    onSubmit,
  }: {
    busy: boolean;

    onClose: () => void;

    onSubmit: (
      payload:
        Record<
          string,
          unknown
        >,
    ) => Promise<void>;
  },
) {
  const [
    name,
    setName,
  ] =
    useState("");

  const [
    slug,
    setSlug,
  ] =
    useState("");

  const [
    timezone,
    setTimezone,
  ] =
    useState(
      "Asia/Dhaka"
    );

  const [
    initialAdminEmail,
    setInitialAdminEmail,
  ] =
    useState("");

  const [
    dataMode,
    setDataMode,
  ] =
    useState(
      "managed"
    );

  const [
    activate,
    setActivate,
  ] =
    useState(false);


  function submit(
    event: FormEvent,
  ) {
    event.preventDefault();

    void onSubmit(
      {
        name,
        slug,
        timezone,

        initial_admin_email:
          initialAdminEmail,

        data_mode:
          dataMode,

        activate,
      },
    );
  }


  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4">
      <form
        onSubmit={
          submit
        }
        className="w-full max-w-xl rounded-3xl bg-white p-6 shadow-2xl"
      >
        <h2 className="text-xl font-semibold">
          Provision hospital
        </h2>

        <p className="mt-1 text-sm text-slate-500">
          The initial administrator must already have a MediBook account.
        </p>

        <div className="mt-5 grid gap-4 md:grid-cols-2">
          <label className="text-sm font-medium">
            Hospital name

            <input
              required
              value={
                name
              }
              onChange={
                (
                  event,
                ) =>
                  setName(
                    event.target.value
                  )
              }
              className="mt-2 w-full rounded-xl border border-slate-200 px-3 py-2.5 font-normal"
            />
          </label>

          <label className="text-sm font-medium">
            Slug

            <input
              required
              value={
                slug
              }
              onChange={
                (
                  event,
                ) =>
                  setSlug(
                    event.target.value
                    .toLowerCase()
                    .replace(
                      /[^a-z0-9-]/g,
                      "-",
                    )
                  )
              }
              className="mt-2 w-full rounded-xl border border-slate-200 px-3 py-2.5 font-normal"
            />
          </label>

          <label className="text-sm font-medium">
            Timezone

            <input
              required
              value={
                timezone
              }
              onChange={
                (
                  event,
                ) =>
                  setTimezone(
                    event.target.value
                  )
              }
              className="mt-2 w-full rounded-xl border border-slate-200 px-3 py-2.5 font-normal"
            />
          </label>

          <label className="text-sm font-medium">
            Initial admin email

            <input
              required
              type="email"
              value={
                initialAdminEmail
              }
              onChange={
                (
                  event,
                ) =>
                  setInitialAdminEmail(
                    event.target.value
                  )
              }
              className="mt-2 w-full rounded-xl border border-slate-200 px-3 py-2.5 font-normal"
            />
          </label>

          <label className="text-sm font-medium">
            Data mode

            <select
              value={
                dataMode
              }
              onChange={
                (
                  event,
                ) =>
                  setDataMode(
                    event.target.value
                  )
              }
              className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 font-normal"
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
          </label>

          <label className="flex items-center gap-3 rounded-xl border border-slate-200 p-3 text-sm">
            <input
              type="checkbox"
              checked={
                activate
              }
              onChange={
                (
                  event,
                ) =>
                  setActivate(
                    event.target.checked
                  )
              }
            />

            Activate immediately
          </label>
        </div>

        <div className="mt-6 flex justify-end gap-2">
          <button
            type="button"
            onClick={
              onClose
            }
            className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium"
          >
            Cancel
          </button>

          <button
            type="submit"
            disabled={
              busy
            }
            className="rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
          >
            {
              busy
                ? "Provisioning..."
                : "Provision hospital"
            }
          </button>
        </div>
      </form>
    </div>
  );
}
