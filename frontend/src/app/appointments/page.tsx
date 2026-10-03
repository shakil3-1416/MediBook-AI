"use client";

import {
  Building2,
  CalendarClock,
  CalendarDays,
  CheckCircle2,
  Clock3,
  MapPin,
  RefreshCcw,
  Stethoscope,
  X,
  XCircle,
} from "lucide-react";

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";


type Appointment = {
  appointment_id: string;
  confirmation_code: string;
  status: string;

  doctor: {
    id: string;
    name: string;
    specialty: string;
    clinic_name: string;
    clinic_location: string;
  };

  date: string;
  time: string;
  consultation_fee: number;
};


type Slot = {
  id: string;
  date: string;
  time: string;
};


type DoctorProfile = {
  next_available_slots: Slot[];
};


type Tab =
  | "upcoming"
  | "past"
  | "cancelled";


function displayTime(
  value: string,
) {

  const [
    hourString,
    minute,
  ] =
    value.split(":");

  const hour =
    Number(
      hourString,
    );

  return (
    `${hour % 12 || 12}:` +
    `${minute} ` +
    `${hour >= 12 ? "PM" : "AM"}`
  );
}


function displayDate(
  value: string,
) {

  return new Intl.DateTimeFormat(
    "en-US",
    {
      weekday: "short",
      day: "numeric",
      month: "short",
      year: "numeric",
    },
  ).format(
    new Date(
      `${value}T00:00:00`,
    ),
  );
}


function appointmentMoment(
  appointment: Appointment,
) {

  return new Date(
    `${appointment.date}T${appointment.time}:00`,
  );
}


export default function AppointmentsPage() {

  const [
    appointments,
    setAppointments,
  ] =
    useState<Appointment[]>(
      [],
    );

  const [
    loading,
    setLoading,
  ] =
    useState(true);

  const [
    error,
    setError,
  ] =
    useState<string | null>(
      null,
    );

  const [
    tab,
    setTab,
  ] =
    useState<Tab>(
      "upcoming",
    );

  const [
    busyId,
    setBusyId,
  ] =
    useState<string | null>(
      null,
    );

  const [
    rescheduleAppointment,
    setRescheduleAppointment,
  ] =
    useState<Appointment | null>(
      null,
    );

  const [
    slots,
    setSlots,
  ] =
    useState<Slot[]>(
      [],
    );

  const [
    loadingSlots,
    setLoadingSlots,
  ] =
    useState(false);

  const [
    rescheduleError,
    setRescheduleError,
  ] =
    useState<string | null>(
      null,
    );


  const loadAppointments =
    useCallback(
      async () => {

        setLoading(true);
        setError(null);

        try {

          const response =
            await fetch(
              "/api/appointments?include_cancelled=true",
              {
                cache: "no-store",
              },
            );


          if (!response.ok) {

            throw new Error(
              "Could not load appointments.",
            );
          }


          const data =
            await response.json();


          setAppointments(
            Array.isArray(data)
              ? data
              : data.appointments ??
                [],
          );

        } catch (
          reason
        ) {

          setError(
            reason instanceof Error
              ? reason.message
              : "Appointments unavailable.",
          );

        } finally {

          setLoading(false);
        }
      },
      [],
    );


  useEffect(
    () => {

      queueMicrotask(() => {
        void loadAppointments();
      });

    },
    [
      loadAppointments,
    ],
  );


  const groups =
    useMemo(
      () => {

        const now =
          new Date();


        const active =
          appointments.filter(
            appointment =>
              appointment.status
                .toLowerCase() !==
              "cancelled",
          );


        return {
          upcoming:
            active
              .filter(
                appointment =>
                  appointmentMoment(
                    appointment,
                  ) >= now,
              )
              .sort(
                (
                  a,
                  b,
                ) =>
                  appointmentMoment(
                    a,
                  ).getTime()
                  -
                  appointmentMoment(
                    b,
                  ).getTime(),
              ),

          past:
            active
              .filter(
                appointment =>
                  appointmentMoment(
                    appointment,
                  ) < now,
              )
              .sort(
                (
                  a,
                  b,
                ) =>
                  appointmentMoment(
                    b,
                  ).getTime()
                  -
                  appointmentMoment(
                    a,
                  ).getTime(),
              ),

          cancelled:
            appointments.filter(
              appointment =>
                appointment.status
                  .toLowerCase() ===
                "cancelled",
            ),
        };
      },
      [
        appointments,
      ],
    );


  const visible =
    groups[tab];


  async function cancelAppointment(
    appointment: Appointment,
  ) {

    const confirmed =
      window.confirm(
        `Cancel your appointment with ${appointment.doctor.name} on ${displayDate(appointment.date)} at ${displayTime(appointment.time)}?`,
      );


    if (!confirmed) {
      return;
    }


    setBusyId(
      appointment.appointment_id,
    );


    try {

      const response =
        await fetch(
          "/api/appointments/cancel",
          {
            method: "POST",

            headers: {
              "Content-Type":
                "application/json",
            },

            body:
              JSON.stringify({
                appointment_id:
                  appointment.appointment_id,
              }),
          },
        );


      if (!response.ok) {

        const body =
          await response
            .json()
            .catch(
              () => ({}),
            );

        throw new Error(
          body.detail ??
          "Cancellation failed.",
        );
      }


      await loadAppointments();

    } catch (
      reason
    ) {

      window.alert(
        reason instanceof Error
          ? reason.message
          : "Cancellation failed.",
      );

    } finally {

      setBusyId(null);
    }
  }


  async function openReschedule(
    appointment: Appointment,
  ) {

    setRescheduleAppointment(
      appointment,
    );

    setSlots([]);
    setRescheduleError(null);
    setLoadingSlots(true);


    try {

      const response =
        await fetch(
          `/api/directory/doctors/${appointment.doctor.id}`,
          {
            cache: "no-store",
          },
        );


      if (!response.ok) {

        throw new Error(
          "Available times could not be loaded.",
        );
      }


      const data:
        DoctorProfile =
          await response.json();


      setSlots(
        data.next_available_slots ??
        [],
      );

    } catch (
      reason
    ) {

      setRescheduleError(
        reason instanceof Error
          ? reason.message
          : "Available times could not be loaded.",
      );

    } finally {

      setLoadingSlots(false);
    }
  }


  async function chooseRescheduleSlot(
    slot: Slot,
  ) {

    if (
      !rescheduleAppointment
    ) {
      return;
    }


    setBusyId(
      rescheduleAppointment
        .appointment_id,
    );

    setRescheduleError(
      null,
    );


    try {

      const response =
        await fetch(
          "/api/appointments/reschedule",
          {
            method: "POST",

            headers: {
              "Content-Type":
                "application/json",
            },

            body:
              JSON.stringify({
                appointment_id:
                  rescheduleAppointment
                    .appointment_id,

                new_slot_id:
                  slot.id,
              }),
          },
        );


      if (!response.ok) {

        const body =
          await response
            .json()
            .catch(
              () => ({}),
            );


        throw new Error(
          body.detail ??
          "Rescheduling failed.",
        );
      }


      setRescheduleAppointment(
        null,
      );

      setSlots([]);

      await loadAppointments();

    } catch (
      reason
    ) {

      setRescheduleError(
        reason instanceof Error
          ? reason.message
          : "Rescheduling failed.",
      );

    } finally {

      setBusyId(null);
    }
  }


  return (
    <main className="mx-auto max-w-6xl px-5 py-8 md:px-8 md:py-10">

      <section className="rounded-[32px] bg-slate-950 px-7 py-9 text-white md:px-10">

        <div className="flex flex-col gap-5 md:flex-row md:items-end md:justify-between">

          <div>

            <div className="text-sm font-bold text-brand-400">
              MediBook
            </div>


            <h1 className="mt-2 text-3xl font-bold tracking-tight">
              Your appointments
            </h1>


            <p className="mt-3 max-w-xl text-sm leading-6 text-slate-300">

              View upcoming visits,
              reschedule available
              appointments, or cancel
              when your plans change.

            </p>

          </div>


          <div className="grid grid-cols-3 gap-2">

            <Summary
              label="Upcoming"
              value={
                groups.upcoming.length
              }
            />

            <Summary
              label="Past"
              value={
                groups.past.length
              }
            />

            <Summary
              label="Cancelled"
              value={
                groups.cancelled.length
              }
            />

          </div>

        </div>

      </section>


      <div className="mt-7 flex gap-2 overflow-x-auto pb-1">

        <TabButton
          active={
            tab === "upcoming"
          }
          onClick={
            () =>
              setTab(
                "upcoming",
              )
          }
        >
          Upcoming
        </TabButton>


        <TabButton
          active={
            tab === "past"
          }
          onClick={
            () =>
              setTab(
                "past",
              )
          }
        >
          Past
        </TabButton>


        <TabButton
          active={
            tab === "cancelled"
          }
          onClick={
            () =>
              setTab(
                "cancelled",
              )
          }
        >
          Cancelled
        </TabButton>

      </div>


      {loading && (

        <div className="mt-6 space-y-4">

          {Array.from({
            length: 3,
          }).map(
            (
              _,
              index,
            ) => (

              <div
                key={index}
                className="h-48 animate-pulse rounded-3xl bg-slate-100"
              />

            ),
          )}

        </div>

      )}


      {error && (

        <div className="mt-6 rounded-3xl border border-red-200 bg-red-50 p-6 text-red-800">

          {error}

        </div>

      )}


      {!loading &&
      !error &&
      visible.length ===
        0 && (

        <div className="mt-6 rounded-3xl border border-dashed border-slate-300 bg-white px-6 py-16 text-center">

          <CalendarDays
            size={34}
            className="mx-auto text-slate-300"
          />

          <h2 className="mt-4 text-lg font-bold text-slate-950">

            No {
              tab
            } appointments

          </h2>

          <p className="mt-2 text-sm text-slate-500">

            Your appointments will
            appear here.

          </p>

        </div>

      )}


      {!loading &&
      !error &&
      visible.length >
        0 && (

        <div className="mt-6 space-y-4">

          {visible.map(
            appointment => {

              const cancelled =
                appointment.status
                  .toLowerCase() ===
                "cancelled";


              return (

                <article
                  key={
                    appointment.appointment_id
                  }
                  className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"
                >

                  <div className="flex flex-col gap-6 md:flex-row md:items-start md:justify-between">

                    <div className="flex gap-4">

                      <div className={[
                        "flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl",

                        cancelled
                          ? "bg-slate-100 text-slate-500"
                          : "bg-brand-50 text-brand-700",
                      ].join(
                        " ",
                      )}>

                        <Stethoscope
                          size={21}
                        />

                      </div>


                      <div>

                        <div className="flex flex-wrap items-center gap-2">

                          <h2 className="font-bold text-slate-950">

                            {
                              appointment.doctor.name
                            }

                          </h2>


                          <span className={[
                            "rounded-full px-2.5 py-1 text-[11px] font-bold capitalize",

                            cancelled
                              ? "bg-slate-100 text-slate-600"
                              : "bg-brand-100 text-brand-800",
                          ].join(
                            " ",
                          )}>

                            {
                              appointment.status
                            }

                          </span>

                        </div>


                        <div className="mt-1 text-sm font-semibold text-brand-700">

                          {
                            appointment.doctor.specialty
                          }

                        </div>


                        <div className="mt-4 grid gap-2 text-sm text-slate-600 sm:grid-cols-2">

                          <Detail
                            icon={
                              <Building2
                                size={15}
                              />
                            }
                          >
                            {
                              appointment.doctor.clinic_name
                            }
                          </Detail>


                          <Detail
                            icon={
                              <MapPin
                                size={15}
                              />
                            }
                          >
                            {
                              appointment.doctor.clinic_location
                            }
                          </Detail>


                          <Detail
                            icon={
                              <CalendarDays
                                size={15}
                              />
                            }
                          >
                            {
                              displayDate(
                                appointment.date,
                              )
                            }
                          </Detail>


                          <Detail
                            icon={
                              <Clock3
                                size={15}
                              />
                            }
                          >
                            {
                              displayTime(
                                appointment.time,
                              )
                            }
                          </Detail>

                        </div>

                      </div>

                    </div>


                    <div className="min-w-[170px]">

                      <div className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                        Consultation
                      </div>

                      <div className="mt-1 text-xl font-bold text-slate-950">
                        Tk {
                          appointment.consultation_fee.toLocaleString()
                        }
                      </div>

                      <div className="mt-2 text-xs text-slate-500">

                        Ref: {
                          appointment.confirmation_code
                        }

                      </div>

                    </div>

                  </div>


                  {tab ===
                  "upcoming" &&
                  !cancelled && (

                    <div className="mt-6 flex flex-wrap gap-2 border-t border-slate-100 pt-5">

                      <button
                        type="button"
                        disabled={
                          busyId ===
                          appointment.appointment_id
                        }
                        onClick={
                          () =>
                            void openReschedule(
                              appointment,
                            )
                        }
                        className="inline-flex items-center gap-2 rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:opacity-50"
                      >

                        <RefreshCcw
                          size={15}
                        />

                        Reschedule

                      </button>


                      <button
                        type="button"
                        disabled={
                          busyId ===
                          appointment.appointment_id
                        }
                        onClick={
                          () =>
                            void cancelAppointment(
                              appointment,
                            )
                        }
                        className="inline-flex items-center gap-2 rounded-xl border border-red-200 bg-white px-4 py-2.5 text-sm font-semibold text-red-700 transition hover:bg-red-50 disabled:opacity-50"
                      >

                        <XCircle
                          size={15}
                        />

                        Cancel appointment

                      </button>

                    </div>

                  )}

                </article>

              );
            },
          )}

        </div>

      )}


      {rescheduleAppointment && (

        <div className="fixed inset-0 z-[100] flex items-end justify-center bg-slate-950/50 p-0 backdrop-blur-sm sm:items-center sm:p-6">

          <div className="max-h-[90vh] w-full max-w-3xl overflow-hidden rounded-t-[28px] bg-white shadow-2xl sm:rounded-[28px]">

            <div className="flex items-start justify-between border-b border-slate-100 p-6">

              <div>

                <div className="flex items-center gap-2 text-sm font-bold text-brand-700">

                  <CalendarClock
                    size={17}
                  />

                  Reschedule appointment

                </div>


                <h2 className="mt-2 text-xl font-bold text-slate-950">

                  {
                    rescheduleAppointment.doctor.name
                  }

                </h2>


                <p className="mt-1 text-sm text-slate-500">

                  Select another currently
                  available appointment slot.

                </p>

              </div>


              <button
                type="button"
                onClick={
                  () => {
                    setRescheduleAppointment(
                      null,
                    );

                    setSlots([]);
                    setRescheduleError(null);
                  }
                }
                className="rounded-xl p-2 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
              >

                <X
                  size={19}
                />

              </button>

            </div>


            <div className="max-h-[65vh] overflow-y-auto p-6">

              {loadingSlots && (

                <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3">

                  {Array.from({
                    length: 9,
                  }).map(
                    (
                      _,
                      index,
                    ) => (

                      <div
                        key={index}
                        className="h-20 animate-pulse rounded-2xl bg-slate-100"
                      />

                    ),
                  )}

                </div>

              )}


              {rescheduleError && (

                <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">

                  {
                    rescheduleError
                  }

                </div>

              )}


              {!loadingSlots &&
              !rescheduleError &&
              slots.length ===
                0 && (

                <div className="rounded-2xl bg-slate-50 p-8 text-center text-sm text-slate-500">

                  No alternative
                  appointment slots
                  are currently available.

                </div>

              )}


              {!loadingSlots &&
              slots.length >
                0 && (

                <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-3">

                  {slots.map(
                    slot => (

                      <button
                        key={
                          slot.id
                        }
                        type="button"
                        disabled={
                          busyId ===
                          rescheduleAppointment.appointment_id
                        }
                        onClick={
                          () =>
                            void chooseRescheduleSlot(
                              slot,
                            )
                        }
                        className="rounded-2xl border border-slate-200 bg-white p-4 text-left transition hover:border-brand-500 hover:bg-brand-50 disabled:opacity-50"
                      >

                        <div className="text-sm font-bold text-slate-950">

                          {
                            displayDate(
                              slot.date,
                            )
                          }

                        </div>

                        <div className="mt-2 flex items-center gap-2 text-sm text-slate-600">

                          <Clock3
                            size={15}
                            className="text-brand-600"
                          />

                          {
                            displayTime(
                              slot.time,
                            )
                          }

                        </div>

                      </button>

                    ),
                  )}

                </div>

              )}

            </div>

          </div>

        </div>

      )}

    </main>
  );
}


function Summary({
  label,
  value,
}: {
  label: string;
  value: number;
}) {

  return (
    <div className="min-w-[82px] rounded-2xl border border-white/10 bg-white/10 px-3 py-3 text-center">

      <div className="text-xl font-bold">
        {value}
      </div>

      <div className="mt-0.5 text-[10px] font-semibold uppercase tracking-wide text-slate-300">
        {label}
      </div>

    </div>
  );
}


function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {

  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        "rounded-xl px-4 py-2.5 text-sm font-semibold transition",

        active
          ? "bg-slate-950 text-white"
          : "border border-slate-200 bg-white text-slate-600 hover:bg-slate-50",
      ].join(
        " ",
      )}
    >
      {children}
    </button>
  );
}


function Detail({
  icon,
  children,
}: {
  icon: React.ReactNode;
  children: React.ReactNode;
}) {

  return (
    <div className="flex items-start gap-2">

      <span className="mt-0.5 shrink-0 text-slate-400">
        {icon}
      </span>

      <span>
        {children}
      </span>

    </div>
  );
}
