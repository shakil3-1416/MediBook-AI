"use client";

import Link from "next/link";

import {
  FormEvent,
  useEffect,
  useState,
} from "react";


type Appointment = {
  appointment_id: string;
  confirmation_code: string;
  status: string;

  doctor: {
    id: string;
    name: string;
  };

  patient: {
    name: string;
    phone: string | null;
    email: string | null;
  };

  slot: {
    id: string | null;
    date: string | null;
    time: string | null;
  };

  booked_at: string | null;
  cancelled_at: string | null;
};


type Payload = {
  hospital: {
    id: string;
    slug: string;
    name: string;
  };

  count: number;

  appointments: Appointment[];
};


function badge(
  value: string,
) {
  const status =
    value.toLowerCase();

  if (
    status ===
    "confirmed"
  ) {
    return "bg-brand-50 text-brand-700";
  }

  if (
    status ===
    "cancelled"
  ) {
    return "bg-rose-50 text-rose-700";
  }

  return "bg-amber-50 text-amber-700";
}


export default function HospitalAppointmentsPage() {

  const [
    data,
    setData,
  ] =
    useState<
      Payload | null
    >(null);


  const [
    loading,
    setLoading,
  ] =
    useState(
      true,
    );


  const [
    error,
    setError,
  ] =
    useState<
      string | null
    >(null);


  const [
    status,
    setStatus,
  ] =
    useState(
      "all",
    );


  const [
    search,
    setSearch,
  ] =
    useState(
      "",
    );


  const [
    dateFrom,
    setDateFrom,
  ] =
    useState(
      "",
    );


  const [
    dateTo,
    setDateTo,
  ] =
    useState(
      "",
    );


  async function load(
    values?: {
      status?: string;
      search?: string;
      dateFrom?: string;
      dateTo?: string;
    },
  ) {
    setLoading(
      true,
    );

    setError(
      null,
    );


    const params =
      new URLSearchParams({
        hospital:
          "",

        limit:
          "200",
      });


    const nextStatus =
      values?.status ??
      status;


    const nextSearch =
      values?.search ??
      search;


    const nextFrom =
      values?.dateFrom ??
      dateFrom;


    const nextTo =
      values?.dateTo ??
      dateTo;


    if (
      nextStatus
      &&
      nextStatus !==
        "all"
    ) {
      params.set(
        "status",
        nextStatus,
      );
    }


    if (
      nextSearch.trim()
    ) {
      params.set(
        "search",
        nextSearch.trim(),
      );
    }


    if (nextFrom) {
      params.set(
        "date_from",
        nextFrom,
      );
    }


    if (nextTo) {
      params.set(
        "date_to",
        nextTo,
      );
    }


    try {
      const response =
        await fetch(
          `/api/dashboard/hospital-appointments?${params.toString()}`,
          {
            cache:
              "no-store",
          },
        );


      if (
        !response.ok
      ) {
        throw new Error(
          await response.text(),
        );
      }


      const payload =
        await response.json();


      setData(
        payload,
      );

    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not load appointments.",
      );

    } finally {
      setLoading(
        false,
      );
    }
  }


  useEffect(
    () => {
      queueMicrotask(() => {
        void load();
      });
    },
    [],
  );


  function submit(
    event:
      FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    void load();
  }


  function changeStatus(
    value: string,
  ) {
    setStatus(
      value,
    );

    void load({
      status:
        value,
    });
  }


  function clearFilters() {
    setStatus(
      "all",
    );

    setSearch(
      "",
    );

    setDateFrom(
      "",
    );

    setDateTo(
      "",
    );


    void load({
      status:
        "all",

      search:
        "",

      dateFrom:
        "",

      dateTo:
        "",
    });
  }


  return (
    <main data-medibook-hospital className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
          <div>
            <Link
              href="/hospital-dashboard"
              className="text-sm font-medium text-brand-600 hover:text-brand-700"
            >
              ← Hospital overview
            </Link>

            <h1 className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">
              Appointments
            </h1>

            <p className="mt-1 text-sm text-slate-500">
              Search and inspect hospital appointment activity
            </p>
          </div>

          <div className="rounded-full bg-brand-50 px-3 py-1.5 text-sm font-medium text-brand-700">
            {
              data?.count ??
              0
            }{" "}
            results
          </div>
        </div>
      </header>


      <div className="mx-auto max-w-7xl px-6 py-8">
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex flex-wrap gap-2">
            {[
              "all",
              "confirmed",
              "cancelled",
            ].map(
              (
                item,
              ) => (
                <button
                  key={
                    item
                  }
                  onClick={
                    () =>
                      changeStatus(
                        item,
                      )
                  }
                  className={
                    status ===
                    item
                      ? "rounded-xl bg-brand-600 px-4 py-2 text-sm font-medium text-white"
                      : "rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium capitalize text-slate-700 hover:bg-slate-50"
                  }
                >
                  {
                    item
                  }
                </button>
              ),
            )}
          </div>


          <form
            onSubmit={
              submit
            }
            className="mt-5 grid gap-3 lg:grid-cols-[1fr_180px_180px_auto_auto]"
          >
            <input
              value={
                search
              }
              onChange={
                event =>
                  setSearch(
                    event.target.value,
                  )
              }
              placeholder="Search confirmation code, doctor or patient"
              className="rounded-xl border border-slate-200 px-4 py-2.5 text-sm outline-none ring-brand-500 focus:ring-2"
            />


            <input
              type="date"
              value={
                dateFrom
              }
              onChange={
                event =>
                  setDateFrom(
                    event.target.value,
                  )
              }
              className="rounded-xl border border-slate-200 px-3 py-2.5 text-sm"
            />


            <input
              type="date"
              value={
                dateTo
              }
              onChange={
                event =>
                  setDateTo(
                    event.target.value,
                  )
              }
              className="rounded-xl border border-slate-200 px-3 py-2.5 text-sm"
            />


            <button
              type="submit"
              className="rounded-xl bg-brand-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-brand-700"
            >
              Search
            </button>


            <button
              type="button"
              onClick={
                clearFilters
              }
              className="rounded-xl border border-slate-200 px-5 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Clear
            </button>
          </form>
        </section>


        {error ? (
          <div className="mt-6 rounded-2xl border border-rose-200 bg-white p-6 text-sm text-rose-700">
            {error}
          </div>
        ) : null}


        <section className="mt-6 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          {loading ? (
            <div className="p-8 text-sm text-slate-500">
              Loading appointments...
            </div>
          ) : !data ||
            data.appointments.length ===
              0 ? (
            <div className="p-8 text-sm text-slate-500">
              No appointments match these filters.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200">
                <thead className="bg-slate-50">
                  <tr className="text-left text-xs font-medium uppercase tracking-wide text-slate-500">
                    <th className="px-5 py-3">
                      Patient
                    </th>

                    <th className="px-5 py-3">
                      Doctor
                    </th>

                    <th className="px-5 py-3">
                      Appointment
                    </th>

                    <th className="px-5 py-3">
                      Confirmation
                    </th>

                    <th className="px-5 py-3">
                      Status
                    </th>
                  </tr>
                </thead>


                <tbody className="divide-y divide-slate-100">
                  {data.appointments.map(
                    (
                      appointment,
                    ) => (
                      <tr
                        key={
                          appointment.appointment_id
                        }
                        className="text-sm text-slate-700"
                      >
                        <td className="px-5 py-4">
                          <div className="font-medium text-slate-950">
                            {
                              appointment.patient.name
                            }
                          </div>

                          <div className="mt-1 text-xs text-slate-500">
                            {
                              appointment.patient.phone ??
                              appointment.patient.email ??
                              "No contact shown"
                            }
                          </div>
                        </td>


                        <td className="whitespace-nowrap px-5 py-4 font-medium text-slate-900">
                          {
                            appointment.doctor.name
                          }
                        </td>


                        <td className="whitespace-nowrap px-5 py-4">
                          <div>
                            {
                              appointment.slot.date ??
                              "No date"
                            }
                          </div>

                          <div className="mt-1 text-xs text-slate-500">
                            {
                              appointment.slot.time ??
                              "No time"
                            }
                          </div>
                        </td>


                        <td className="whitespace-nowrap px-5 py-4 font-mono text-xs">
                          {
                            appointment.confirmation_code
                          }
                        </td>


                        <td className="whitespace-nowrap px-5 py-4">
                          <span
                            className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium capitalize ${badge(
                              appointment.status,
                            )}`}
                          >
                            {
                              appointment.status
                            }
                          </span>
                        </td>
                      </tr>
                    ),
                  )}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
