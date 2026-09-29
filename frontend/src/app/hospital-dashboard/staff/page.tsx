"use client";

import {
  RefreshCw,
  Search,
  UserPlus,
  Users,
} from "lucide-react";

import {
  FormEvent,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  displayValue,
  hospitalOpsRequest,
  normalizeCollection,
} from "@/lib/hospital-ops";

import {
  useHospitalWorkspace,
} from "@/components/hospital/hospital-workspace-context";


type StaffRecord =
  Record<
    string,
    unknown
  >;


export default function HospitalStaffPage() {
  const {
    activeWorkspace,
  } =
    useHospitalWorkspace();

  const canMutate =
    activeWorkspace?.role ===
      "hospital_admin";

  const [
    staff,
    setStaff,
  ] =
    useState<
      StaffRecord[]
    >([]);

  const [
    search,
    setSearch,
  ] =
    useState("");

  const [
    email,
    setEmail,
  ] =
    useState("");

  const [
    role,
    setRole,
  ] =
    useState(
      "hospital_staff",
    );

  const [
    loading,
    setLoading,
  ] =
    useState(true);

  const [
    busy,
    setBusy,
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
          unknown
        >(
          "/api/dashboard/hospital-admin?resource=staff",
        );

      setStaff(
        normalizeCollection(
          response,
        ),
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not load hospital staff.",
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


  async function addStaff(
    event: FormEvent,
  ) {
    event.preventDefault();

    if (!canMutate) {
      setError(
        "Only hospital administrators can add staff.",
      );

      return;
    }

    setBusy(true);
    setError(null);
    setSuccess(null);

    try {
      await hospitalOpsRequest(
        "/api/dashboard/hospital-admin?resource=staff",
        {
          method: "POST",
          body:
            JSON.stringify(
              {
                email:
                  email.trim(),
                role,
              },
            ),
        },
      );

      setEmail("");

      setSuccess(
        "Staff membership added.",
      );

      await load();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not add staff.",
      );
    } finally {
      setBusy(false);
    }
  }


  async function updateStaff(
    member: StaffRecord,
    patch: Record<
      string,
      unknown
    >,
  ) {
    if (!canMutate) {
      setError(
        "Only hospital administrators can update staff.",
      );

      return;
    }

    const id =
      member.membership_id ??
      member.id;

    if (!id) {
      setError(
        "This staff record does not expose a membership ID.",
      );

      return;
    }

    setBusy(true);
    setError(null);
    setSuccess(null);

    try {
      await hospitalOpsRequest(
        `/api/dashboard/hospital-admin?resource=staff&id=${encodeURIComponent(
          String(id),
        )}`,
        {
          method:
            "PATCH",
          body:
            JSON.stringify(
              patch,
            ),
        },
      );

      setSuccess(
        "Staff membership updated.",
      );

      await load();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not update staff.",
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
          return staff;
        }

        return staff.filter(
          (item) =>
            JSON.stringify(
              item,
            )
              .toLowerCase()
              .includes(
                needle,
              ),
        );
      },
      [
        search,
        staff,
      ],
    );


  return (
    <main className="p-5 md:p-8">
      <div className="mx-auto max-w-7xl">
        <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
          <div>
            <div className="flex items-center gap-2 text-sm font-semibold text-purple-600">
              <Users size={16} />
              Administration
            </div>

            <h1 className="mt-2 text-3xl font-semibold tracking-tight">
              Staff
            </h1>

            <p className="mt-2 text-sm text-slate-500">
              Add existing MediBook users, assign hospital roles and control access.
            </p>
          </div>

          <button
            type="button"
            onClick={
              () =>
                void load()
            }
            className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium"
          >
            <RefreshCw size={16} />
            Refresh
          </button>
        </div>

        {error ? (
          <div className="mt-6 rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
            {error}
          </div>
        ) : null}

        {success ? (
          <div className="mt-6 rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-700">
            {success}
          </div>
        ) : null}

        {canMutate ? (
        <form
          onSubmit={
            addStaff
          }
          className="mt-6 grid gap-3 rounded-2xl border border-slate-200 bg-white p-5 md:grid-cols-[1fr_220px_auto]"
        >
          <div>
            <label className="text-xs font-medium text-slate-500">
              Existing user email
            </label>

            <input
              type="email"
              required
              value={email}
              onChange={
                (event) =>
                  setEmail(
                    event.target.value,
                  )
              }
              placeholder="staff@example.com"
              className="mt-2 w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm outline-none focus:border-purple-400"
            />
          </div>

          <div>
            <label className="text-xs font-medium text-slate-500">
              Role
            </label>

            <select
              value={role}
              onChange={
                (event) =>
                  setRole(
                    event.target.value,
                  )
              }
              className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm"
            >
              <option value="hospital_staff">
                Hospital staff
              </option>

              <option value="hospital_admin">
                Hospital admin
              </option>

              <option value="doctor">
                Doctor
              </option>
            </select>
          </div>

          <button
            type="submit"
            disabled={
              busy
            }
            className="mt-auto inline-flex items-center justify-center gap-2 rounded-xl bg-purple-600 px-4 py-2.5 text-sm font-medium text-white disabled:opacity-50"
          >
            <UserPlus size={16} />
            Add staff
          </button>
        </form>
        ) : (
          <div className="mt-6 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
            Your hospital role has read-only access to staff administration.
          </div>
        )}

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
              placeholder="Search staff"
              className="w-full rounded-xl border border-slate-200 py-2.5 pl-10 pr-4 text-sm outline-none focus:border-purple-400"
            />
          </div>
        </div>

        <div className="mt-6 overflow-hidden rounded-2xl border border-slate-200 bg-white">
          {loading ? (
            <div className="p-8 text-sm text-slate-500">
              Loading staff...
            </div>
          ) : filtered.length === 0 ? (
            <div className="p-8 text-sm text-slate-500">
              No staff members found.
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {filtered.map(
                (
                  member,
                  index,
                ) => {
                  const id =
                    member.membership_id ??
                    member.id ??
                    index;

                  const active =
                    member.is_active !==
                    false;

                  return (
                    <div
                      key={
                        String(id)
                      }
                      className="grid gap-4 p-5 lg:grid-cols-[1.2fr_1.2fr_220px_160px]"
                    >
                      <div>
                        <div className="text-xs uppercase tracking-wide text-slate-400">
                          Identity
                        </div>

                        <div className="mt-1 font-medium">
                          {displayValue(
                            member.name ??
                            member.full_name ??
                            member.email,
                          )}
                        </div>

                        <div className="mt-1 text-xs text-slate-500">
                          {displayValue(
                            member.email,
                          )}
                        </div>
                      </div>

                      <div>
                        <div className="text-xs uppercase tracking-wide text-slate-400">
                          Role
                        </div>

                        <select
                          disabled={
                            busy ||
                            !canMutate
                          }
                          value={
                            String(
                              member.role ??
                              "hospital_staff",
                            )
                          }
                          onChange={
                            (event) =>
                              void updateStaff(
                                member,
                                {
                                  role:
                                    event.target.value,
                                },
                              )
                          }
                          className="mt-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm"
                        >
                          <option value="hospital_staff">
                            Hospital staff
                          </option>

                          <option value="hospital_admin">
                            Hospital admin
                          </option>

                          <option value="doctor">
                            Doctor
                          </option>
                        </select>
                      </div>

                      <div>
                        <div className="text-xs uppercase tracking-wide text-slate-400">
                          Access
                        </div>

                        <div className="mt-2">
                          <span
                            className={[
                              "rounded-full px-2.5 py-1 text-xs font-semibold",
                              active
                                ? "bg-emerald-50 text-emerald-700"
                                : "bg-slate-100 text-slate-600",
                            ].join(
                              " ",
                            )}
                          >
                            {active
                              ? "Active"
                              : "Inactive"}
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center lg:justify-end">
                        {canMutate ? (
                        <button
                          type="button"
                          disabled={busy}
                          onClick={
                            () =>
                              void updateStaff(
                                member,
                                {
                                  is_active:
                                    !active,
                                },
                              )
                          }
                          className={[
                            "rounded-xl px-3 py-2 text-sm font-medium",
                            active
                              ? "border border-rose-200 bg-white text-rose-700"
                              : "bg-emerald-600 text-white",
                          ].join(
                            " ",
                          )}
                        >
                          {active
                            ? "Deactivate"
                            : "Activate"}
                        </button>
                        ) : null}
                      </div>
                    </div>
                  );
                },
              )}
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
