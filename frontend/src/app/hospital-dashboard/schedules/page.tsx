"use client";

import {
  useEffect,
  useState,
} from "react";
import {
  useRouter,
} from "next/navigation";


type Doctor = {
  id: string;
  full_name: string;
  source_mode?: string;
  specialty?:
    | string
    | {
        name?: string;
      };
};


type Rule = {
  id: string;
  weekday: number;
  start_time: string;
  end_time: string;
  slot_duration_minutes: number;
  capacity: number;
  valid_from: string | null;
  valid_until: string | null;
  is_active: boolean;
};


type ScheduleException = {
  id: string;
  exception_date: string;
  kind: string;
  start_time: string | null;
  end_time: string | null;
  reason: string | null;
  is_active: boolean;
};


type ScheduleData = {
  doctor_id: string;
  source_mode: string;
  editable: boolean;
  rules: Rule[];
  exceptions: ScheduleException[];
};


type Preview = {
  desired_slots: number;
  existing_slots: number;
  conflicts: Array<{
    slot_id: string;
    slot_date: string;
    start_time: string;
    active_appointments: number;
    reason: string;
  }>;
};


const HOSPITAL =
  "";

const WEEKDAYS = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
];


function specialty(
  doctor: Doctor,
) {
  if (
    typeof doctor.specialty
    === "string"
  ) {
    return doctor.specialty;
  }

  return (
    doctor.specialty?.name ??
    "Doctor"
  );
}


export default function HospitalSchedulesPage() {
  const router =
    useRouter();

  const [
    doctors,
    setDoctors,
  ] = useState<Doctor[]>([]);

  const [
    doctorId,
    setDoctorId,
  ] = useState("");

  const [
    schedule,
    setSchedule,
  ] = useState<ScheduleData | null>(
    null,
  );

  const [
    preview,
    setPreview,
  ] = useState<Preview | null>(
    null,
  );

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    busy,
    setBusy,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState<string | null>(
    null,
  );

  const [
    weekday,
    setWeekday,
  ] = useState("0");

  const [
    startTime,
    setStartTime,
  ] = useState("09:00");

  const [
    endTime,
    setEndTime,
  ] = useState("17:00");

  const [
    duration,
    setDuration,
  ] = useState("20");

  const [
    capacity,
    setCapacity,
  ] = useState("1");

  const [
    exceptionDate,
    setExceptionDate,
  ] = useState("");

  const [
    exceptionKind,
    setExceptionKind,
  ] = useState("leave");

  const [
    exceptionStart,
    setExceptionStart,
  ] = useState("");

  const [
    exceptionEnd,
    setExceptionEnd,
  ] = useState("");

  const [
    reason,
    setReason,
  ] = useState("");

  const [
    rangeStart,
    setRangeStart,
  ] = useState("");

  const [
    rangeEnd,
    setRangeEnd,
  ] = useState("");


  async function parseError(
    response: Response,
  ) {
    const text =
      await response.text();

    try {
      const body =
        JSON.parse(text);

      return (
        typeof body.detail
        === "string"
          ? body.detail
          : body.detail?.message ??
            text
      );
    } catch {
      return text ||
        `HTTP ${response.status}`;
    }
  }


  async function loadDoctors() {
    const response =
      await fetch(
        `/api/dashboard/hospital-doctors?hospital=${HOSPITAL}`,
        {
          cache:
            "no-store",
        },
      );

    if (
      response.status === 401 ||
      response.status === 403
    ) {
      router.replace(
        "/hospital-login",
      );

      return;
    }

    if (!response.ok) {
      throw new Error(
        await parseError(
          response,
        ),
      );
    }

    const body =
      await response.json() as {
        doctors?: Doctor[];
      };

    const values =
      body.doctors ?? [];

    setDoctors(
      values,
    );

    if (
      values.length &&
      !doctorId
    ) {
      setDoctorId(
        values[0].id,
      );
    }
  }


  async function loadSchedule(
    selected: string,
  ) {
    if (!selected) {
      return;
    }

    const response =
      await fetch(
        `/api/dashboard/hospital-schedules?hospital=${HOSPITAL}&doctor_id=${encodeURIComponent(selected)}`,
        {
          cache:
            "no-store",
        },
      );

    if (
      response.status === 401 ||
      response.status === 403
    ) {
      router.replace(
        "/hospital-login",
      );

      return;
    }

    if (!response.ok) {
      throw new Error(
        await parseError(
          response,
        ),
      );
    }

    setSchedule(
      await response.json(),
    );

    setPreview(
      null,
    );
  }


  useEffect(
    () => {
      queueMicrotask(
        async () => {
          try {
            await loadDoctors();
          } catch (err) {
            setError(
              err instanceof Error
                ? err.message
                : "Could not load doctors.",
            );
          } finally {
            setLoading(false);
          }
        },
      );
    },
    [],
  );


  useEffect(
    () => {
      if (!doctorId) {
        return;
      }

      queueMicrotask(
        async () => {
          try {
            setError(null);
            await loadSchedule(
              doctorId,
            );
          } catch (err) {
            setError(
              err instanceof Error
                ? err.message
                : "Could not load schedule.",
            );
          }
        },
      );
    },
    [doctorId],
  );


  async function post(
    action: string,
    payload: unknown,
  ) {
    setBusy(true);
    setError(null);

    try {
      const response =
        await fetch(
          "/api/dashboard/hospital-schedules",
          {
            method:
              "POST",
            headers: {
              "Content-Type":
                "application/json",
            },
            body:
              JSON.stringify({
                hospital:
                  HOSPITAL,
                doctor_id:
                  doctorId,
                action,
                payload,
              }),
          },
        );

      if (!response.ok) {
        const text =
          await response.text();

        let message =
          text;

        try {
          const body =
            JSON.parse(
              text,
            );

          message =
            typeof body.detail
            === "string"
              ? body.detail
              : body.detail?.message ??
                text;

          if (
            body.detail?.conflicts
          ) {
            setPreview({
              desired_slots: 0,
              existing_slots: 0,
              conflicts:
                body.detail.conflicts,
            });
          }
        } catch {
          // Preserve raw backend error.
        }

        throw new Error(
          message,
        );
      }

      return await response.json();

    } finally {
      setBusy(false);
    }
  }


  async function createRule() {
    try {
      await post(
        "rule",
        {
          weekday:
            Number(weekday),
          start_time:
            startTime,
          end_time:
            endTime,
          slot_duration_minutes:
            Number(duration),
          capacity:
            Number(capacity),
        },
      );

      await loadSchedule(
        doctorId,
      );

    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not create rule.",
      );
    }
  }


  async function createException() {
    try {
      const payload: {
        exception_date: string;
        kind: string;
        reason: string | null;
        start_time?: string;
        end_time?: string;
      } = {
        exception_date:
          exceptionDate,
        kind:
          exceptionKind,
        reason:
          reason.trim() || null,
      };

      if (
        exceptionStart &&
        exceptionEnd
      ) {
        payload.start_time =
          exceptionStart;
        payload.end_time =
          exceptionEnd;
      }

      await post(
        "exception",
        payload,
      );

      await loadSchedule(
        doctorId,
      );

    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not create exception.",
      );
    }
  }


  async function previewSchedule() {
    try {
      const result =
        await post(
          "preview",
          {
            start_date:
              rangeStart,
            end_date:
              rangeEnd,
          },
        );

      setPreview(
        result as Preview,
      );

    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not preview schedule.",
      );
    }
  }


  async function applySchedule() {
    if (
      !window.confirm(
        "Apply this schedule to the selected date range? Existing booked appointments will be protected.",
      )
    ) {
      return;
    }

    try {
      await post(
        "apply",
        {
          start_date:
            rangeStart,
          end_date:
            rangeEnd,
        },
      );

      await previewSchedule();

    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not apply schedule.",
      );
    }
  }


  async function deactivate(
    resource:
      | "rule"
      | "exception",
    id: string,
  ) {
    setBusy(true);

    try {
      const response =
        await fetch(
          "/api/dashboard/hospital-schedules",
          {
            method:
              "PATCH",
            headers: {
              "Content-Type":
                "application/json",
            },
            body:
              JSON.stringify({
                hospital:
                  HOSPITAL,
                doctor_id:
                  doctorId,
                resource,
                id,
                payload: {
                  is_active:
                    false,
                },
              }),
          },
        );

      if (!response.ok) {
        throw new Error(
          await parseError(
            response,
          ),
        );
      }

      await loadSchedule(
        doctorId,
      );

    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Schedule update failed.",
      );

    } finally {
      setBusy(false);
    }
  }


  if (loading) {
    return (
      <main className="min-h-screen bg-slate-50 p-8">
        <div className="mx-auto max-w-7xl rounded-2xl border border-slate-200 bg-white p-8">
          Loading schedules...
        </div>
      </main>
    );
  }


  const editable =
    schedule?.editable ??
    false;


  return (
    <main className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
          <div>
            <div className="text-sm font-semibold text-purple-600">
              MediBook Hospital Operations
            </div>

            <h1 className="mt-1 text-2xl font-semibold text-slate-950">
              Doctor schedules
            </h1>

            <p className="mt-1 text-sm text-slate-500">
              Weekly availability, exceptions and conflict-safe slot generation
            </p>
          </div>

          <div className="flex gap-2">

          </div>
        </div>
      </header>

      <div className="mx-auto max-w-7xl space-y-6 px-6 py-8">
        {error && (
          <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
            {error}
          </div>
        )}

        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <label className="text-sm font-medium text-slate-700">
            Doctor
          </label>

          <select
            value={doctorId}
            onChange={
              (event) =>
                setDoctorId(
                  event.target.value,
                )
            }
            className="mt-2 w-full rounded-xl border border-slate-300 px-3 py-2.5"
          >
            {doctors.map(
              (doctor) => (
                <option
                  key={doctor.id}
                  value={doctor.id}
                >
                  {doctor.full_name}
                  {" · "}
                  {specialty(
                    doctor,
                  )}
                </option>
              ),
            )}
          </select>

          {schedule && (
            <div className="mt-3 text-sm text-slate-500">
              Source mode:{" "}
              <strong className="text-slate-700">
                {schedule.source_mode}
              </strong>
            </div>
          )}

          {schedule &&
            !editable && (
              <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
                This doctor&apos;s schedule is managed by an external system. MediBook is read-only for schedule changes.
              </div>
            )}
        </section>

        <div className="grid gap-6 lg:grid-cols-2">
          <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-950">
              Weekly rules
            </h2>

            <div className="mt-5 grid gap-3 sm:grid-cols-2">
              <select
                value={weekday}
                disabled={!editable || busy}
                onChange={
                  (event) =>
                    setWeekday(
                      event.target.value,
                    )
                }
                className="rounded-xl border border-slate-300 px-3 py-2"
              >
                {WEEKDAYS.map(
                  (name, index) => (
                    <option
                      key={name}
                      value={index}
                    >
                      {name}
                    </option>
                  ),
                )}
              </select>

              <input
                type="number"
                min="5"
                max="240"
                value={duration}
                disabled={!editable || busy}
                onChange={
                  (event) =>
                    setDuration(
                      event.target.value,
                    )
                }
                placeholder="Minutes"
                className="rounded-xl border border-slate-300 px-3 py-2"
              />

              <input
                type="time"
                value={startTime}
                disabled={!editable || busy}
                onChange={
                  (event) =>
                    setStartTime(
                      event.target.value,
                    )
                }
                className="rounded-xl border border-slate-300 px-3 py-2"
              />

              <input
                type="time"
                value={endTime}
                disabled={!editable || busy}
                onChange={
                  (event) =>
                    setEndTime(
                      event.target.value,
                    )
                }
                className="rounded-xl border border-slate-300 px-3 py-2"
              />

              <input
                type="number"
                min="1"
                max="50"
                value={capacity}
                disabled={!editable || busy}
                onChange={
                  (event) =>
                    setCapacity(
                      event.target.value,
                    )
                }
                className="rounded-xl border border-slate-300 px-3 py-2"
              />

              <button
                type="button"
                disabled={!editable || busy}
                onClick={
                  () => {
                    void createRule();
                  }
                }
                className="rounded-xl bg-purple-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-40"
              >
                Add rule
              </button>
            </div>

            <div className="mt-6 space-y-3">
              {schedule?.rules.map(
                (rule) => (
                  <div
                    key={rule.id}
                    className="flex items-center justify-between rounded-xl border border-slate-200 p-4"
                  >
                    <div>
                      <div className="font-medium text-slate-900">
                        {WEEKDAYS[
                          rule.weekday
                        ]}
                      </div>

                      <div className="mt-1 text-sm text-slate-500">
                        {rule.start_time.slice(
                          0,
                          5,
                        )}
                        {" to "}
                        {rule.end_time.slice(
                          0,
                          5,
                        )}
                        {" · "}
                        {rule.slot_duration_minutes}
                        {" min · capacity "}
                        {rule.capacity}
                      </div>
                    </div>

                    {rule.is_active &&
                      editable && (
                        <button
                          type="button"
                          disabled={busy}
                          onClick={
                            () => {
                              void deactivate(
                                "rule",
                                rule.id,
                              );
                            }
                          }
                          className="text-sm font-medium text-rose-600"
                        >
                          Disable
                        </button>
                      )}
                  </div>
                ),
              )}
            </div>
          </section>

          <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-950">
              Exceptions
            </h2>

            <div className="mt-5 grid gap-3 sm:grid-cols-2">
              <input
                type="date"
                value={exceptionDate}
                disabled={!editable || busy}
                onChange={
                  (event) =>
                    setExceptionDate(
                      event.target.value,
                    )
                }
                className="rounded-xl border border-slate-300 px-3 py-2"
              />

              <select
                value={exceptionKind}
                disabled={!editable || busy}
                onChange={
                  (event) =>
                    setExceptionKind(
                      event.target.value,
                    )
                }
                className="rounded-xl border border-slate-300 px-3 py-2"
              >
                <option value="leave">
                  Leave
                </option>
                <option value="closure">
                  Closure
                </option>
                <option value="unavailable">
                  Unavailable
                </option>
                <option value="override">
                  Override
                </option>
              </select>

              <input
                type="time"
                value={exceptionStart}
                disabled={!editable || busy}
                onChange={
                  (event) =>
                    setExceptionStart(
                      event.target.value,
                    )
                }
                className="rounded-xl border border-slate-300 px-3 py-2"
              />

              <input
                type="time"
                value={exceptionEnd}
                disabled={!editable || busy}
                onChange={
                  (event) =>
                    setExceptionEnd(
                      event.target.value,
                    )
                }
                className="rounded-xl border border-slate-300 px-3 py-2"
              />

              <input
                value={reason}
                disabled={!editable || busy}
                onChange={
                  (event) =>
                    setReason(
                      event.target.value,
                    )
                }
                placeholder="Reason"
                className="rounded-xl border border-slate-300 px-3 py-2"
              />

              <button
                type="button"
                disabled={
                  !editable ||
                  busy ||
                  !exceptionDate
                }
                onClick={
                  () => {
                    void createException();
                  }
                }
                className="rounded-xl bg-purple-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-40"
              >
                Add exception
              </button>
            </div>

            <div className="mt-6 space-y-3">
              {schedule?.exceptions.map(
                (item) => (
                  <div
                    key={item.id}
                    className="flex items-center justify-between rounded-xl border border-slate-200 p-4"
                  >
                    <div>
                      <div className="font-medium capitalize text-slate-900">
                        {item.kind}
                      </div>

                      <div className="mt-1 text-sm text-slate-500">
                        {item.exception_date}
                        {item.reason
                          ? ` · ${item.reason}`
                          : ""}
                      </div>
                    </div>

                    {item.is_active &&
                      editable && (
                        <button
                          type="button"
                          disabled={busy}
                          onClick={
                            () => {
                              void deactivate(
                                "exception",
                                item.id,
                              );
                            }
                          }
                          className="text-sm font-medium text-rose-600"
                        >
                          Disable
                        </button>
                      )}
                  </div>
                ),
              )}
            </div>
          </section>
        </div>

        <section className="rounded-2xl border border-purple-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-950">
            Preview and apply
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            MediBook checks existing bookings before changing concrete appointment slots.
          </p>

          <div className="mt-5 flex flex-wrap gap-3">
            <input
              type="date"
              value={rangeStart}
              onChange={
                (event) =>
                  setRangeStart(
                    event.target.value,
                  )
              }
              className="rounded-xl border border-slate-300 px-3 py-2"
            />

            <input
              type="date"
              value={rangeEnd}
              onChange={
                (event) =>
                  setRangeEnd(
                    event.target.value,
                  )
              }
              className="rounded-xl border border-slate-300 px-3 py-2"
            />

            <button
              type="button"
              disabled={
                busy ||
                !rangeStart ||
                !rangeEnd
              }
              onClick={
                () => {
                  void previewSchedule();
                }
              }
              className="rounded-xl border border-purple-200 bg-purple-50 px-4 py-2 text-sm font-medium text-purple-700"
            >
              Preview
            </button>

            <button
              type="button"
              disabled={
                !editable ||
                busy ||
                !preview ||
                preview.conflicts.length >
                  0
              }
              onClick={
                () => {
                  void applySchedule();
                }
              }
              className="rounded-xl bg-purple-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-40"
            >
              Apply schedule
            </button>
          </div>

          {preview && (
            <div className="mt-6">
              <div className="grid gap-3 sm:grid-cols-3">
                <div className="rounded-xl bg-slate-50 p-4">
                  <div className="text-xs uppercase tracking-wide text-slate-500">
                    Desired slots
                  </div>
                  <div className="mt-1 text-2xl font-semibold">
                    {preview.desired_slots}
                  </div>
                </div>

                <div className="rounded-xl bg-slate-50 p-4">
                  <div className="text-xs uppercase tracking-wide text-slate-500">
                    Existing slots
                  </div>
                  <div className="mt-1 text-2xl font-semibold">
                    {preview.existing_slots}
                  </div>
                </div>

                <div className="rounded-xl bg-slate-50 p-4">
                  <div className="text-xs uppercase tracking-wide text-slate-500">
                    Conflicts
                  </div>
                  <div className="mt-1 text-2xl font-semibold">
                    {preview.conflicts.length}
                  </div>
                </div>
              </div>

              {preview.conflicts.length >
                0 && (
                <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50 p-4">
                  <div className="font-medium text-rose-800">
                    Schedule cannot be applied yet
                  </div>

                  <div className="mt-2 space-y-2 text-sm text-rose-700">
                    {preview.conflicts.map(
                      (conflict) => (
                        <div
                          key={
                            conflict.slot_id
                          }
                        >
                          {conflict.slot_date}
                          {" "}
                          {conflict.start_time.slice(
                            0,
                            5,
                          )}
                          {": "}
                          {conflict.active_appointments}
                          {" active appointment(s), "}
                          {conflict.reason}
                        </div>
                      ),
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
