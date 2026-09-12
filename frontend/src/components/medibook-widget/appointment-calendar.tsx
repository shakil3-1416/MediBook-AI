"use client";

import {
  useEffect,
  useMemo,
  useState,
} from "react";


type Appointment = {
  id?: string;

  appointment_id?: string;

  confirmation_code?: string;

  status?: string;

  doctor_name?: string;

  specialty?: string;

  clinic_name?: string;

  clinic_location?: string;

  slot_date?: string;

  start_time?: string;

  date?: string;

  time?: string;

  doctor?: {
    name?: string;

    full_name?: string;

    specialty?:
      | string
      | {
          name?: string;
        };

    clinic_name?: string;

    clinic_location?: string;
  };

  slot?: {
    slot_date?: string;
    start_time?: string;
  };
};


type Props = {
  hospitalSlug: string;

  open: boolean;

  onClose: () => void;
};


function appointmentDate(
  appointment: Appointment,
) {
  return (
    appointment.date
    ??
    appointment.slot_date
    ??
    appointment.slot?.slot_date
    ??
    ""
  );
}


function appointmentTime(
  appointment: Appointment,
) {
  return (
    appointment.time
    ??
    appointment.start_time
    ??
    appointment.slot?.start_time
    ??
    ""
  );
}


function doctorName(
  appointment: Appointment,
) {
  return (
    appointment.doctor_name
    ??
    appointment.doctor?.name
    ??
    appointment.doctor?.full_name
    ??
    "Doctor"
  );
}


function specialtyName(
  appointment: Appointment,
) {
  const doctorSpecialty =
    appointment.doctor?.specialty;

  return (
    appointment.specialty
    ??
    (
      typeof doctorSpecialty === "string"
        ? doctorSpecialty
        : doctorSpecialty?.name
    )
    ??
    ""
  );
}


function clinicName(
  appointment: Appointment,
) {
  return (
    appointment.clinic_name
    ??
    appointment.doctor?.clinic_name
    ??
    ""
  );
}


function clinicLocation(
  appointment: Appointment,
) {
  return (
    appointment.clinic_location
    ??
    appointment.doctor?.clinic_location
    ??
    ""
  );
}


function isoDate(
  date: Date,
) {
  const year =
    date.getFullYear();

  const month =
    String(
      date.getMonth() + 1,
    ).padStart(
      2,
      "0",
    );

  const day =
    String(
      date.getDate(),
    ).padStart(
      2,
      "0",
    );

  return (
    `${year}-${month}-${day}`
  );
}


function monthTitle(
  date: Date,
) {
  return new Intl.DateTimeFormat(
    "en",
    {
      month:
        "long",

      year:
        "numeric",
    },
  ).format(
    date,
  );
}


function friendlyDate(
  value: string,
) {
  if (!value) {
    return "";
  }

  const date =
    new Date(
      `${value}T00:00:00`,
    );

  return new Intl.DateTimeFormat(
    "en",
    {
      weekday:
        "long",

      month:
        "long",

      day:
        "numeric",

      year:
        "numeric",
    },
  ).format(
    date,
  );
}


function friendlyTime(
  value: string,
) {
  if (!value) {
    return "";
  }

  const [
    hourString,
    minuteString,
  ] =
    value.split(":");

  const hour =
    Number(
      hourString,
    );

  const minute =
    Number(
      minuteString ??
      "0",
    );

  if (
    Number.isNaN(
      hour,
    )
  ) {
    return value;
  }

  const date =
    new Date();

  date.setHours(
    hour,
    minute,
    0,
    0,
  );

  return new Intl.DateTimeFormat(
    "en",
    {
      hour:
        "numeric",

      minute:
        "2-digit",
    },
  ).format(
    date,
  );
}


export default function AppointmentCalendar({
  hospitalSlug,
  open,
  onClose,
}: Props) {
  const [
    appointments,
    setAppointments,
  ] =
    useState<
      Appointment[]
    >([]);


  const [
    loading,
    setLoading,
  ] =
    useState(
      false,
    );


  const [
    error,
    setError,
  ] =
    useState<
      string | null
    >(null);


  const [
    month,
    setMonth,
  ] =
    useState(
      () => {
        const now =
          new Date();

        return new Date(
          now.getFullYear(),
          now.getMonth(),
          1,
        );
      },
    );


  const [
    selectedDate,
    setSelectedDate,
  ] =
    useState(
      () =>
        isoDate(
          new Date(),
        ),
    );


  useEffect(
    () => {
      if (!open) {
        return;
      }

      let active =
        true;

      async function load() {
        setLoading(
          true,
        );

        setError(
          null,
        );

        try {
          const response =
            await fetch(
              `/api/widget/${encodeURIComponent(
                hospitalSlug,
              )}/appointments`,
              {
                cache:
                  "no-store",
              },
            );


          if (!response.ok) {
            throw new Error(
              "Could not load appointments.",
            );
          }


          const data =
            await response.json();


          const rows =
            Array.isArray(
              data,
            )
              ? data
              : Array.isArray(
                  data.appointments,
                )
                ? data.appointments
                : [];


          if (active) {
            setAppointments(
              rows,
            );
          }

        } catch (reason) {
          if (active) {
            setError(
              reason instanceof Error
                ? reason.message
                : "Could not load appointments.",
            );
          }

        } finally {
          if (active) {
            setLoading(
              false,
            );
          }
        }
      }


      void load();


      return () => {
        active =
          false;
      };
    },
    [
      open,
      hospitalSlug,
    ],
  );


  const appointmentsByDate =
    useMemo(
      () => {
        const map =
          new Map<
            string,
            Appointment[]
          >();


        for (
          const appointment
          of appointments
        ) {
          const date =
            appointmentDate(
              appointment,
            );

          if (!date) {
            continue;
          }


          const existing =
            map.get(
              date,
            )
            ??
            [];


          existing.push(
            appointment,
          );


          map.set(
            date,
            existing,
          );
        }


        return map;
      },
      [
        appointments,
      ],
    );


  const days =
    useMemo(
      () => {
        const first =
          new Date(
            month.getFullYear(),
            month.getMonth(),
            1,
          );


        const last =
          new Date(
            month.getFullYear(),
            month.getMonth() + 1,
            0,
          );


        const cells:
          Array<
            Date | null
          > =
            [];


        for (
          let i = 0;
          i < first.getDay();
          i += 1
        ) {
          cells.push(
            null,
          );
        }


        for (
          let day = 1;
          day <= last.getDate();
          day += 1
        ) {
          cells.push(
            new Date(
              month.getFullYear(),
              month.getMonth(),
              day,
            ),
          );
        }


        while (
          cells.length % 7
          !==
          0
        ) {
          cells.push(
            null,
          );
        }


        return cells;
      },
      [
        month,
      ],
    );


  const selectedAppointments =
    appointmentsByDate.get(
      selectedDate,
    )
    ??
    [];


  if (!open) {
    return null;
  }


  return (
    <div data-medibook-calendar className="absolute inset-0 z-40 flex flex-col bg-white">
      <header className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
        <div>
          <h2 className="text-lg font-semibold text-slate-950">
            My appointments
          </h2>

          <p className="mt-0.5 text-xs text-slate-500">
            Your schedule at this hospital
          </p>
        </div>


        <button
          type="button"
          onClick={
            onClose
          }
          aria-label="Close appointment calendar"
          className="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100"
        >
          Back to chat
        </button>
      </header>


      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-4xl p-5">
          <div className="flex items-center justify-between">
            <button
              type="button"
              aria-label="Previous month"
              onClick={
                () =>
                  setMonth(
                    new Date(
                      month.getFullYear(),
                      month.getMonth() - 1,
                      1,
                    ),
                  )
              }
              className="rounded-lg border border-slate-200 px-3 py-2 text-sm hover:bg-slate-50"
            >
              Previous
            </button>


            <h3 className="text-base font-semibold text-slate-900">
              {
                monthTitle(
                  month,
                )
              }
            </h3>


            <button
              type="button"
              aria-label="Next month"
              onClick={
                () =>
                  setMonth(
                    new Date(
                      month.getFullYear(),
                      month.getMonth() + 1,
                      1,
                    ),
                  )
              }
              className="rounded-lg border border-slate-200 px-3 py-2 text-sm hover:bg-slate-50"
            >
              Next
            </button>
          </div>


          <div className="mt-5 grid grid-cols-7 border-l border-t border-slate-200 text-center text-xs font-medium text-slate-500">
            {
              [
                "Sun",
                "Mon",
                "Tue",
                "Wed",
                "Thu",
                "Fri",
                "Sat",
              ].map(
                day => (
                  <div
                    key={
                      day
                    }
                    className="border-b border-r border-slate-200 py-2"
                  >
                    {
                      day
                    }
                  </div>
                ),
              )
            }


            {
              days.map(
                (
                  date,
                  index,
                ) => {
                  if (!date) {
                    return (
                      <div
                        key={
                          `empty-${index}`
                        }
                        className="min-h-20 border-b border-r border-slate-200 bg-slate-50/60"
                      />
                    );
                  }


                  const key =
                    isoDate(
                      date,
                    );


                  const count =
                    appointmentsByDate.get(
                      key,
                    )?.length
                    ??
                    0;


                  const selected =
                    key
                    ===
                    selectedDate;


                  return (
                    <button
                      key={
                        key
                      }
                      type="button"
                      onClick={
                        () =>
                          setSelectedDate(
                            key,
                          )
                      }
                      className={[
                        "relative min-h-20 border-b border-r border-slate-200 p-2 text-left transition",
                        selected
                          ? "bg-purple-50"
                          : "hover:bg-slate-50",
                      ].join(
                        " ",
                      )}
                    >
                      <span className="text-sm text-slate-700">
                        {
                          date.getDate()
                        }
                      </span>


                      {
                        count > 0
                          ? (
                            <span className="mt-2 block w-fit rounded-full bg-purple-100 px-2 py-0.5 text-[11px] font-semibold text-purple-700">
                              {
                                count
                              }
                              {
                                count === 1
                                  ? " appointment"
                                  : " appointments"
                              }
                            </span>
                          )
                          : null
                      }
                    </button>
                  );
                },
              )
            }
          </div>


          <section className="mt-8">
            <h3 className="text-base font-semibold text-slate-900">
              {
                friendlyDate(
                  selectedDate,
                )
              }
            </h3>


            {
              loading
                ? (
                  <p className="mt-4 text-sm text-slate-500">
                    Loading appointments...
                  </p>
                )
                : null
            }


            {
              error
                ? (
                  <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                    {
                      error
                    }
                  </div>
                )
                : null
            }


            {
              !loading
              &&
              !error
              &&
              selectedAppointments.length
              ===
              0
                ? (
                  <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-5 text-sm text-slate-500">
                    Nothing scheduled for this date.
                  </div>
                )
                : null
            }


            <div className="mt-4 space-y-3">
              {
                selectedAppointments.map(
                  (
                    appointment,
                    index,
                  ) => (
                    <article
                      key={
                        appointment.id
                        ??
                        appointment.confirmation_code
                        ??
                        index
                      }
                      className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
                    >
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div>
                          <h4 className="font-semibold text-slate-950">
                            {
                              doctorName(
                                appointment,
                              )
                            }
                          </h4>


                          {
                            specialtyName(
                              appointment,
                            )
                              ? (
                                <p className="mt-1 text-sm text-slate-600">
                                  {
                                    specialtyName(
                                      appointment,
                                    )
                                  }
                                </p>
                              )
                              : null
                          }
                        </div>


                        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium capitalize text-slate-600">
                          {
                            appointment.status
                            ??
                            "scheduled"
                          }
                        </span>
                      </div>


                      <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
                        <div>
                          <dt className="text-slate-400">
                            Time
                          </dt>

                          <dd className="mt-0.5 font-medium text-slate-700">
                            {
                              friendlyTime(
                                appointmentTime(
                                  appointment,
                                ),
                              )
                              ||
                              "Not available"
                            }
                          </dd>
                        </div>


                        {
                          clinicName(
                            appointment,
                          )
                            ? (
                              <div>
                                <dt className="text-slate-400">
                                  Hospital / chamber
                                </dt>

                                <dd className="mt-0.5 font-medium text-slate-700">
                                  {
                                    clinicName(
                                      appointment,
                                    )
                                  }
                                </dd>
                              </div>
                            )
                            : null
                        }


                        {
                          clinicLocation(
                            appointment,
                          )
                            ? (
                              <div>
                                <dt className="text-slate-400">
                                  Location
                                </dt>

                                <dd className="mt-0.5 font-medium text-slate-700">
                                  {
                                    clinicLocation(
                                      appointment,
                                    )
                                  }
                                </dd>
                              </div>
                            )
                            : null
                        }


                        {
                          appointment.confirmation_code
                            ? (
                              <div>
                                <dt className="text-slate-400">
                                  Confirmation
                                </dt>

                                <dd className="mt-0.5 font-mono text-sm font-medium text-slate-700">
                                  {
                                    appointment.confirmation_code
                                  }
                                </dd>
                              </div>
                            )
                            : null
                        }
                      </dl>


                      <p className="mt-5 border-t border-slate-100 pt-4 text-xs leading-5 text-slate-400">
                        Need to make a change? Return to the conversation and tell MediBook what you want to do.
                      </p>
                    </article>
                  ),
                )
              }
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
