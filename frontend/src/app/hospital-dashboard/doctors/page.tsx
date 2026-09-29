"use client";

import {
  Edit3,
  Plus,
  RefreshCw,
  Search,
  Stethoscope,
  X,
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


type Doctor =
  Record<
    string,
    unknown
  >;


type DoctorForm = {
  full_name: string;
  specialty_id: string;
  gender: string;
  qualification: string;
  experience_years: string;
  clinic_name: string;
  clinic_location: string;
  consultation_fee: string;
  source_mode: string;
  external_doctor_id: string;
  public_profile: string;
  operational_metadata: string;
};


const EMPTY_FORM: DoctorForm = {
  full_name: "",
  specialty_id: "",
  gender: "",
  qualification: "",
  experience_years: "",
  clinic_name: "",
  clinic_location: "",
  consultation_fee: "",
  source_mode: "managed",
  external_doctor_id: "",
  public_profile: "{}",
  operational_metadata: "{}",
};


function textValue(
  value: unknown,
): string {
  if (
    value === null ||
    value === undefined
  ) {
    return "";
  }

  return String(
    value,
  );
}


function jsonValue(
  value: unknown,
): string {
  if (
    value === null ||
    value === undefined
  ) {
    return "{}";
  }

  if (
    typeof value ===
      "string"
  ) {
    return value;
  }

  try {
    return JSON.stringify(
      value,
      null,
      2,
    );
  } catch {
    return "{}";
  }
}


function doctorToForm(
  doctor: Doctor,
): DoctorForm {
  return {
    full_name:
      textValue(
        doctor.full_name,
      ),

    specialty_id:
      textValue(
        doctor.specialty_id,
      ),

    gender:
      textValue(
        doctor.gender,
      ),

    qualification:
      textValue(
        doctor.qualification,
      ),

    experience_years:
      textValue(
        doctor.experience_years,
      ),

    clinic_name:
      textValue(
        doctor.clinic_name,
      ),

    clinic_location:
      textValue(
        doctor.clinic_location,
      ),

    consultation_fee:
      textValue(
        doctor.consultation_fee,
      ),

    source_mode:
      textValue(
        doctor.source_mode,
      ) || "managed",

    external_doctor_id:
      textValue(
        doctor.external_doctor_id,
      ),

    public_profile:
      jsonValue(
        doctor.public_profile,
      ),

    operational_metadata:
      jsonValue(
        doctor.operational_metadata,
      ),
  };
}


function parseJsonField(
  raw: string,
  label: string,
): Record<
  string,
  unknown
> {
  const trimmed =
    raw.trim();

  if (!trimmed) {
    return {};
  }

  const value =
    JSON.parse(
      trimmed,
    ) as unknown;

  if (
    !value ||
    typeof value !==
      "object" ||
    Array.isArray(
      value,
    )
  ) {
    throw new Error(
      `${label} must be a JSON object.`,
    );
  }

  return value as Record<
    string,
    unknown
  >;
}


function toPayload(
  form: DoctorForm,
) {
  const payload:
    Record<
      string,
      unknown
    > = {};

  if (
    form.full_name.trim()
  ) {
    payload.full_name =
      form.full_name.trim();
  }

  if (
    form.specialty_id.trim()
  ) {
    payload.specialty_id =
      form.specialty_id.trim();
  }

  if (
    form.gender.trim()
  ) {
    payload.gender =
      form.gender.trim();
  }

  if (
    form.qualification.trim()
  ) {
    payload.qualification =
      form.qualification.trim();
  }

  if (
    form.experience_years.trim()
  ) {
    const years =
      Number(
        form.experience_years,
      );

    if (
      !Number.isFinite(
        years,
      )
    ) {
      throw new Error(
        "Experience years must be numeric.",
      );
    }

    payload.experience_years =
      years;
  }

  if (
    form.clinic_name.trim()
  ) {
    payload.clinic_name =
      form.clinic_name.trim();
  }

  if (
    form.clinic_location.trim()
  ) {
    payload.clinic_location =
      form.clinic_location.trim();
  }

  if (
    form.consultation_fee.trim()
  ) {
    const fee =
      Number(
        form.consultation_fee,
      );

    if (
      !Number.isFinite(
        fee,
      )
    ) {
      throw new Error(
        "Consultation fee must be numeric.",
      );
    }

    payload.consultation_fee =
      fee;
  }

  if (
    form.source_mode.trim()
  ) {
    payload.source_mode =
      form.source_mode.trim();
  }

  if (
    form.external_doctor_id.trim()
  ) {
    payload.external_doctor_id =
      form.external_doctor_id.trim();
  }

  payload.public_profile =
    parseJsonField(
      form.public_profile,
      "Public profile",
    );

  payload.operational_metadata =
    parseJsonField(
      form.operational_metadata,
      "Operational metadata",
    );

  return payload;
}


export default function HospitalDoctorsPage() {
  const {
    activeWorkspace,
  } =
    useHospitalWorkspace();

  const canMutate =
    activeWorkspace?.role ===
      "hospital_admin";

  const [
    doctors,
    setDoctors,
  ] =
    useState<
      Doctor[]
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

  const [
    formOpen,
    setFormOpen,
  ] =
    useState(false);

  const [
    editingDoctor,
    setEditingDoctor,
  ] =
    useState<
      Doctor | null
    >(null);

  const [
    form,
    setForm,
  ] =
    useState<DoctorForm>(
      EMPTY_FORM,
    );


  async function load() {
    setLoading(true);
    setError(null);

    try {
      const response =
        await hospitalOpsRequest<
          unknown
        >(
          "/api/dashboard/hospital-doctors",
        );

      setDoctors(
        normalizeCollection(
          response,
        ),
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not load doctors.",
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


  function openCreate() {
    setEditingDoctor(
      null,
    );

    setForm(
      EMPTY_FORM,
    );

    setError(
      null,
    );

    setSuccess(
      null,
    );

    setFormOpen(
      true,
    );
  }


  function openEdit(
    doctor: Doctor,
  ) {
    setEditingDoctor(
      doctor,
    );

    setForm(
      doctorToForm(
        doctor,
      ),
    );

    setError(
      null,
    );

    setSuccess(
      null,
    );

    setFormOpen(
      true,
    );
  }


  async function submit(
    event: FormEvent,
  ) {
    event.preventDefault();

    if (!canMutate) {
      setError(
        "Only hospital administrators can modify doctors.",
      );

      return;
    }

    setBusy(true);
    setError(null);
    setSuccess(null);

    try {
      const payload =
        toPayload(
          form,
        );

      if (
        !editingDoctor
      ) {
        if (
          !form.full_name.trim()
        ) {
          throw new Error(
            "Doctor name is required.",
          );
        }

        await hospitalOpsRequest(
          "/api/dashboard/hospital-doctors",
          {
            method:
              "POST",

            body:
              JSON.stringify(
                payload,
              ),
          },
        );

        setSuccess(
          "Doctor created.",
        );
      } else {
        const id =
          editingDoctor.id ??
          editingDoctor.doctor_id;

        if (!id) {
          throw new Error(
            "Doctor record does not expose an ID.",
          );
        }

        await hospitalOpsRequest(
          `/api/dashboard/hospital-doctors?id=${encodeURIComponent(
            String(id),
          )}`,
          {
            method:
              "PATCH",

            body:
              JSON.stringify(
                payload,
              ),
          },
        );

        setSuccess(
          "Doctor updated.",
        );
      }

      setFormOpen(
        false,
      );

      setEditingDoctor(
        null,
      );

      setForm(
        EMPTY_FORM,
      );

      await load();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not save doctor.",
      );
    } finally {
      setBusy(false);
    }
  }


  async function toggleActivation(
    doctor: Doctor,
  ) {
    if (!canMutate) {
      setError(
        "Only hospital administrators can change doctor activation.",
      );

      return;
    }

    const id =
      doctor.id ??
      doctor.doctor_id;

    if (!id) {
      setError(
        "Doctor record does not expose an ID.",
      );

      return;
    }

    const active =
      doctor.is_active !==
      false;

    setBusy(true);
    setError(null);
    setSuccess(null);

    try {
      await hospitalOpsRequest(
        `/api/dashboard/hospital-doctors?id=${encodeURIComponent(
          String(id),
        )}&action=activation`,
        {
          method:
            "PATCH",

          body:
            JSON.stringify(
              {
                is_active:
                  !active,
              },
            ),
        },
      );

      setSuccess(
        active
          ? "Doctor deactivated."
          : "Doctor activated.",
      );

      await load();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not change doctor activation.",
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
          return doctors;
        }

        return doctors.filter(
          (doctor) =>
            JSON.stringify(
              doctor,
            )
              .toLowerCase()
              .includes(
                needle,
              ),
        );
      },
      [
        doctors,
        search,
      ],
    );


  function updateForm(
    key: keyof DoctorForm,
    value: string,
  ) {
    setForm(
      (
        current,
      ) => ({
        ...current,
        [key]:
          value,
      }),
    );
  }


  return (
    <main className="p-5 md:p-8">
      <div className="mx-auto max-w-7xl">
        <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
          <div>
            <div className="flex items-center gap-2 text-sm font-semibold text-purple-600">
              <Stethoscope size={16} />

              Hospital Operations
            </div>

            <h1 className="mt-2 text-3xl font-semibold tracking-tight">
              Doctors
            </h1>

            <p className="mt-2 text-sm text-slate-500">
              Manage the doctor registry for the active hospital workspace.
            </p>

            {!canMutate ? (
              <p className="mt-2 text-xs text-amber-700">
                Your role has read-only access to doctor administration.
              </p>
            ) : null}
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
              <RefreshCw size={16} />
              Refresh
            </button>

            {canMutate ? (
              <button
                type="button"
                onClick={
                  openCreate
                }
                className="inline-flex items-center gap-2 rounded-xl bg-purple-600 px-4 py-2 text-sm font-medium text-white"
              >
                <Plus size={16} />
                Add doctor
              </button>
            ) : null}
          </div>
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

        <div className="mt-6 rounded-2xl border border-slate-200 bg-white p-4">
          <div className="relative">
            <Search
              size={17}
              className="absolute left-3 top-3 text-slate-400"
            />

            <input
              value={
                search
              }
              onChange={
                (event) =>
                  setSearch(
                    event.target.value,
                  )
              }
              placeholder="Search doctors"
              className="w-full rounded-xl border border-slate-200 py-2.5 pl-10 pr-4 text-sm outline-none focus:border-purple-400"
            />
          </div>
        </div>

        <div className="mt-6 overflow-hidden rounded-2xl border border-slate-200 bg-white">
          {loading ? (
            <div className="p-8 text-sm text-slate-500">
              Loading doctors...
            </div>
          ) : filtered.length === 0 ? (
            <div className="p-8 text-sm text-slate-500">
              No doctors found.
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {filtered.map(
                (
                  doctor,
                  index,
                ) => {
                  const id =
                    doctor.id ??
                    doctor.doctor_id ??
                    index;

                  const active =
                    doctor.is_active !==
                    false;

                  return (
                    <div
                      key={
                        String(id)
                      }
                      className="grid gap-4 p-5 lg:grid-cols-[1.4fr_1fr_1fr_170px]"
                    >
                      <div>
                        <div className="font-semibold text-slate-950">
                          {displayValue(
                            doctor.full_name ??
                            doctor.name,
                          )}
                        </div>

                        <div className="mt-1 text-xs text-slate-500">
                          {displayValue(
                            doctor.qualification ??
                            doctor.specialty_name ??
                            doctor.specialty,
                          )}
                        </div>

                        <div className="mt-2 text-xs text-slate-400">
                          {displayValue(
                            doctor.clinic_name,
                          )}
                        </div>
                      </div>

                      <div>
                        <div className="text-xs uppercase tracking-wide text-slate-400">
                          Experience
                        </div>

                        <div className="mt-1 text-sm">
                          {displayValue(
                            doctor.experience_years,
                          )}
                        </div>
                      </div>

                      <div>
                        <div className="text-xs uppercase tracking-wide text-slate-400">
                          Consultation fee
                        </div>

                        <div className="mt-1 text-sm">
                          Tk{" "}
                          {displayValue(
                            doctor.consultation_fee,
                          )}
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

                      <div className="flex flex-col gap-2">
                        {canMutate ? (
                          <>
                            <button
                              type="button"
                              disabled={
                                busy
                              }
                              onClick={
                                () =>
                                  openEdit(
                                    doctor,
                                  )
                              }
                              className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-sm font-medium"
                            >
                              <Edit3 size={14} />
                              Edit
                            </button>

                            <button
                              type="button"
                              disabled={
                                busy
                              }
                              onClick={
                                () =>
                                  void toggleActivation(
                                    doctor,
                                  )
                              }
                              className={[
                                "rounded-xl px-3 py-2 text-sm font-medium",
                                active
                                  ? "border border-rose-200 text-rose-700"
                                  : "bg-emerald-600 text-white",
                              ].join(
                                " ",
                              )}
                            >
                              {active
                                ? "Deactivate"
                                : "Activate"}
                            </button>
                          </>
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

      {formOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4">
          <div className="max-h-[94vh] w-full max-w-4xl overflow-y-auto rounded-3xl bg-white shadow-2xl">
            <div className="sticky top-0 flex items-center justify-between border-b border-slate-200 bg-white px-6 py-5">
              <div>
                <h2 className="text-xl font-semibold">
                  {editingDoctor
                    ? "Edit doctor"
                    : "Add doctor"}
                </h2>

                <p className="mt-1 text-sm text-slate-500">
                  Doctor Registry
                </p>
              </div>

              <button
                type="button"
                onClick={
                  () =>
                    setFormOpen(
                      false,
                    )
                }
                className="rounded-xl p-2 text-slate-500 hover:bg-slate-100"
              >
                <X size={19} />
              </button>
            </div>

            <form
              onSubmit={
                submit
              }
              className="grid gap-5 p-6 md:grid-cols-2"
            >
              <label className="text-sm font-medium">
                Full name

                <input
                  required={
                    !editingDoctor
                  }
                  value={
                    form.full_name
                  }
                  onChange={
                    (event) =>
                      updateForm(
                        "full_name",
                        event.target.value,
                      )
                  }
                  className="mt-2 w-full rounded-xl border border-slate-200 px-3 py-2.5 font-normal"
                />
              </label>

              <label className="text-sm font-medium">
                Specialty ID

                <input
                  value={
                    form.specialty_id
                  }
                  onChange={
                    (event) =>
                      updateForm(
                        "specialty_id",
                        event.target.value,
                      )
                  }
                  className="mt-2 w-full rounded-xl border border-slate-200 px-3 py-2.5 font-normal"
                />
              </label>

              <label className="text-sm font-medium">
                Gender

                <input
                  value={
                    form.gender
                  }
                  onChange={
                    (event) =>
                      updateForm(
                        "gender",
                        event.target.value,
                      )
                  }
                  className="mt-2 w-full rounded-xl border border-slate-200 px-3 py-2.5 font-normal"
                />
              </label>

              <label className="text-sm font-medium">
                Qualification

                <input
                  value={
                    form.qualification
                  }
                  onChange={
                    (event) =>
                      updateForm(
                        "qualification",
                        event.target.value,
                      )
                  }
                  className="mt-2 w-full rounded-xl border border-slate-200 px-3 py-2.5 font-normal"
                />
              </label>

              <label className="text-sm font-medium">
                Experience years

                <input
                  type="number"
                  min="0"
                  value={
                    form.experience_years
                  }
                  onChange={
                    (event) =>
                      updateForm(
                        "experience_years",
                        event.target.value,
                      )
                  }
                  className="mt-2 w-full rounded-xl border border-slate-200 px-3 py-2.5 font-normal"
                />
              </label>

              <label className="text-sm font-medium">
                Consultation fee (Tk)

                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={
                    form.consultation_fee
                  }
                  onChange={
                    (event) =>
                      updateForm(
                        "consultation_fee",
                        event.target.value,
                      )
                  }
                  className="mt-2 w-full rounded-xl border border-slate-200 px-3 py-2.5 font-normal"
                />
              </label>

              <label className="text-sm font-medium">
                Clinic name

                <input
                  value={
                    form.clinic_name
                  }
                  onChange={
                    (event) =>
                      updateForm(
                        "clinic_name",
                        event.target.value,
                      )
                  }
                  className="mt-2 w-full rounded-xl border border-slate-200 px-3 py-2.5 font-normal"
                />
              </label>

              <label className="text-sm font-medium">
                Clinic location

                <input
                  value={
                    form.clinic_location
                  }
                  onChange={
                    (event) =>
                      updateForm(
                        "clinic_location",
                        event.target.value,
                      )
                  }
                  className="mt-2 w-full rounded-xl border border-slate-200 px-3 py-2.5 font-normal"
                />
              </label>

              <label className="text-sm font-medium">
                Source mode

                <select
                  value={
                    form.source_mode
                  }
                  onChange={
                    (event) =>
                      updateForm(
                        "source_mode",
                        event.target.value,
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

              <label className="text-sm font-medium">
                External doctor ID

                <input
                  value={
                    form.external_doctor_id
                  }
                  onChange={
                    (event) =>
                      updateForm(
                        "external_doctor_id",
                        event.target.value,
                      )
                  }
                  className="mt-2 w-full rounded-xl border border-slate-200 px-3 py-2.5 font-normal"
                />
              </label>

              <label className="text-sm font-medium md:col-span-2">
                Public profile JSON

                <textarea
                  value={
                    form.public_profile
                  }
                  onChange={
                    (event) =>
                      updateForm(
                        "public_profile",
                        event.target.value,
                      )
                  }
                  className="mt-2 min-h-28 w-full rounded-xl border border-slate-200 bg-slate-950 p-3 font-mono text-xs text-slate-100"
                />
              </label>

              <label className="text-sm font-medium md:col-span-2">
                Operational metadata JSON

                <textarea
                  value={
                    form.operational_metadata
                  }
                  onChange={
                    (event) =>
                      updateForm(
                        "operational_metadata",
                        event.target.value,
                      )
                  }
                  className="mt-2 min-h-28 w-full rounded-xl border border-slate-200 bg-slate-950 p-3 font-mono text-xs text-slate-100"
                />
              </label>

              <div className="flex justify-end gap-3 border-t border-slate-100 pt-5 md:col-span-2">
                <button
                  type="button"
                  onClick={
                    () =>
                      setFormOpen(
                        false,
                      )
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
                  className="rounded-xl bg-purple-600 px-5 py-2 text-sm font-medium text-white disabled:opacity-50"
                >
                  {busy
                    ? "Saving..."
                    : editingDoctor
                      ? "Save changes"
                      : "Create doctor"}
                </button>
              </div>
            </form>
          </div>
        </div>
      ) : null}
    </main>
  );
}
