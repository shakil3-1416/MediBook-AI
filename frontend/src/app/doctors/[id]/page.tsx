"use client";

import {
  ArrowLeft,
  Building2,
  CalendarDays,
  CheckCircle2,
  Clock3,
  GraduationCap,
  MapPin,
  ShieldCheck,
  Stethoscope,
  UserRound,
  WalletCards,
} from "lucide-react";

import Link from "next/link";

import {
  use,
  useEffect,
  useMemo,
  useState,
} from "react";


type Doctor = {
  id: string;
  full_name: string;
  gender: string | null;
  qualification: string | null;
  experience_years: number | null;

  specialty: {
    id?: string;
    name: string;
  };

  clinic_name: string;
  clinic_location: string;
  consultation_fee: number;
};


type Slot = {
  id: string;
  date: string;
  time: string;
};


type Profile = {
  doctor: Doctor;
  next_available_slots: Slot[];
};


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

  const period =
    hour >= 12
      ? "PM"
      : "AM";

  return (
    `${hour % 12 || 12}:` +
    `${minute} ${period}`
  );
}


function displayDate(
  value: string,
) {

  const parsed =
    new Date(
      `${value}T00:00:00`,
    );

  return new Intl.DateTimeFormat(
    "en-US",
    {
      weekday:
        "short",

      day:
        "numeric",

      month:
        "short",
    },
  ).format(parsed);
}


export default function DoctorProfilePage({
  params,
}: {
  params:
    Promise<{
      id: string;
    }>;
}) {

  const {
    id,
  } =
    use(params);


  const [
    profile,
    setProfile,
  ] =
    useState<
      Profile | null
    >(null);

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


  useEffect(
    () => {

      async function load() {

        try {

          const response =
            await fetch(
              `/api/directory/doctors/${id}`,
              {
                cache:
                  "no-store",
              },
            );


          if (
            !response.ok
          ) {

            throw new Error(
              "Doctor profile could not be loaded.",
            );
          }


          setProfile(
            await response.json(),
          );

        } catch (
          reason
        ) {

          setError(
            reason instanceof Error
              ? reason.message
              : "Doctor profile unavailable.",
          );

        } finally {

          setLoading(
            false,
          );
        }
      }


      void load();

    },
    [
      id,
    ],
  );


  const groupedSlots =
    useMemo(
      () => {

        const map =
          new Map<
            string,
            Slot[]
          >();


        for (
          const slot
          of profile
            ?.next_available_slots ??
          []
        ) {

          const existing =
            map.get(
              slot.date,
            ) ??
            [];

          existing.push(
            slot,
          );

          map.set(
            slot.date,
            existing,
          );
        }


        return Array.from(
          map.entries(),
        );

      },
      [
        profile,
      ],
    );


  if (loading) {

    return (
      <main className="mx-auto max-w-6xl px-5 py-8">

        <div className="h-[460px] animate-pulse rounded-[32px] bg-slate-100" />

      </main>
    );
  }


  if (
    error ||
    !profile
  ) {

    return (
      <main className="mx-auto max-w-6xl px-5 py-8">

        <Link
          href="/doctors"
          className="text-sm font-semibold text-slate-500"
        >
          ← Back to doctors
        </Link>


        <div className="mt-6 rounded-3xl border border-red-200 bg-red-50 p-8 text-red-800">

          {
            error ??
            "Doctor unavailable."
          }

        </div>

      </main>
    );
  }


  const {
    doctor,
  } =
    profile;


  return (
    <main className="mx-auto max-w-6xl px-5 py-8 md:px-8 md:py-10">

      <Link
        href="/doctors"
        className="inline-flex items-center gap-2 text-sm font-semibold text-slate-500 transition hover:text-slate-950"
      >

        <ArrowLeft
          size={16}
        />

        Back to doctors

      </Link>


      <section className="mt-6 overflow-hidden rounded-[32px] border border-slate-200 bg-white shadow-sm">

        <div className="bg-gradient-to-br from-emerald-50 via-white to-white p-7 md:p-10">

          <div className="flex flex-col gap-6 md:flex-row md:items-start">

            <div className="flex h-24 w-24 shrink-0 items-center justify-center rounded-[28px] bg-emerald-100 text-emerald-700">

              <UserRound
                size={40}
              />

            </div>


            <div className="min-w-0 flex-1">

              <div className="flex flex-wrap items-center gap-2">

                <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-bold text-emerald-800">

                  {
                    doctor.specialty.name
                  }

                </span>


                <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">

                  <ShieldCheck
                    size={13}
                  />

                  MediBook provider

                </span>

              </div>


              <h1 className="mt-4 text-3xl font-bold tracking-tight text-slate-950 md:text-4xl">

                {
                  doctor.full_name
                }

              </h1>


              <div className="mt-6 grid gap-4 text-sm text-slate-600 sm:grid-cols-2">

                <Info
                  icon={
                    <Building2
                      size={17}
                    />
                  }
                  title="Hospital / Clinic"
                >
                  {
                    doctor.clinic_name
                  }
                </Info>


                <Info
                  icon={
                    <MapPin
                      size={17}
                    />
                  }
                  title="Location"
                >
                  {
                    doctor.clinic_location
                  }
                </Info>


                <Info
                  icon={
                    <GraduationCap
                      size={17}
                    />
                  }
                  title="Qualification"
                >
                  {
                    doctor.qualification ??
                    "Qualification information unavailable"
                  }
                </Info>


                <Info
                  icon={
                    <Stethoscope
                      size={17}
                    />
                  }
                  title="Experience"
                >
                  {
                    doctor.experience_years ??
                    0
                  } years
                </Info>

              </div>

            </div>


            <div className="h-fit min-w-[190px] rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">

              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-400">

                <WalletCards
                  size={15}
                />

                Consultation

              </div>


              <div className="mt-2 text-2xl font-bold text-slate-950">

                Tk {
                  doctor.consultation_fee.toLocaleString()
                }

              </div>


              <div className="mt-2 text-xs text-slate-500">

                Pay according to clinic policy.

              </div>

            </div>

          </div>

        </div>


        <div className="border-t border-slate-100 p-7 md:p-10">

          <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">

            <div>

              <h2 className="text-xl font-bold text-slate-950">

                Available appointments

              </h2>


              <p className="mt-1 text-sm text-slate-500">

                Choose an available time.
                MediBook will show the
                booking summary before
                anything is confirmed.

              </p>

            </div>


            <div className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-700">

              <CheckCircle2
                size={15}
              />

              Live availability

            </div>

          </div>


          {groupedSlots.length ===
          0 ? (

            <div className="mt-7 rounded-3xl border border-dashed border-slate-300 bg-slate-50 px-6 py-12 text-center">

              <CalendarDays
                size={30}
                className="mx-auto text-slate-300"
              />

              <h3 className="mt-3 font-bold text-slate-900">

                No open appointments

              </h3>

              <p className="mt-1 text-sm text-slate-500">

                This doctor&apos;s future
                slots are currently full.

              </p>

            </div>

          ) : (

            <div className="mt-7 space-y-6">

              {groupedSlots.map(
                (
                  [
                    date,
                    slots,
                  ],
                ) => (

                  <section
                    key={date}
                  >

                    <div className="flex items-center gap-2 text-sm font-bold text-slate-800">

                      <CalendarDays
                        size={16}
                        className="text-emerald-600"
                      />

                      {
                        displayDate(
                          date,
                        )
                      }

                    </div>


                    <div className="mt-3 flex flex-wrap gap-2">

                      {slots.map(
                        slot => {

                          const readable =
                            displayTime(
                              slot.time,
                            );


                          const prompt =
                            encodeURIComponent(
                              `Book ${doctor.full_name} on ${slot.date} at ${readable}`,
                            );


                          return (

                            <Link
                              key={
                                slot.id
                              }
                              href={
                                `/assistant?prompt=${prompt}`
                              }
                              className="group inline-flex min-w-[116px] items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 transition hover:border-emerald-500 hover:bg-emerald-50 hover:text-emerald-800"
                            >

                              <Clock3
                                size={15}
                                className="text-slate-400 transition group-hover:text-emerald-600"
                              />

                              {
                                readable
                              }

                            </Link>

                          );
                        },
                      )}

                    </div>

                  </section>

                ),
              )}

            </div>

          )}

        </div>

      </section>

    </main>
  );
}


function Info({
  icon,
  title,
  children,
}: {
  icon:
    React.ReactNode;

  title:
    string;

  children:
    React.ReactNode;
}) {

  return (
    <div className="flex items-start gap-3">

      <div className="mt-0.5 text-slate-400">

        {icon}

      </div>


      <div>

        <div className="text-xs font-semibold text-slate-400">

          {title}

        </div>

        <div className="mt-1 font-medium text-slate-700">

          {children}

        </div>

      </div>

    </div>
  );
}
