"use client";

import {
  Building2,
  ChevronLeft,
  ChevronRight,
  MapPin,
  Search,
  SlidersHorizontal,
  Stethoscope,
  UserRound,
} from "lucide-react";

import Link from "next/link";

import {
  useEffect,
  useState,
} from "react";

import {
  SearchableCombobox,
  type SearchOption,
} from "@/components/searchable-combobox";


type Doctor = {
  id: string;
  full_name: string;
  gender: string | null;
  qualification: string | null;
  experience_years: number | null;

  specialty: {
    id: string;
    name: string;
  };

  clinic_name: string;
  clinic_location: string;
  consultation_fee: number;
};


type DirectoryResponse = {
  count: number;
  page: number;
  page_size: number;
  pages: number;
  doctors: Doctor[];
};


type FacetResponse = {
  cities: SearchOption[];
  areas: SearchOption[];
  specialties: SearchOption[];
  hospitals: SearchOption[];
};


const PAGE_SIZE =
  18;


export default function DoctorsPage() {

  const [
    data,
    setData,
  ] =
    useState<DirectoryResponse>({
      count: 0,
      page: 1,
      page_size:
        PAGE_SIZE,
      pages: 0,
      doctors: [],
    });


  const [
    facets,
    setFacets,
  ] =
    useState<FacetResponse>({
      cities: [],
      areas: [],
      specialties: [],
      hospitals: [],
    });


  const [
    query,
    setQuery,
  ] =
    useState("");

  const [
    city,
    setCity,
  ] =
    useState("");

  const [
    area,
    setArea,
  ] =
    useState("");

  const [
    specialty,
    setSpecialty,
  ] =
    useState("");

  const [
    hospital,
    setHospital,
  ] =
    useState("");


  const [
    gender,
    setGender,
  ] =
    useState("");

  const [
    maxFee,
    setMaxFee,
  ] =
    useState("");

  const [
    page,
    setPage,
  ] =
    useState(1);

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


  /*
   * City + specialty suggestions come from the DB.
   * Area suggestions dynamically change after city selection.
   */
  useEffect(
    () => {
      const controller =
        new AbortController();

      const timer =
        window.setTimeout(
          async () => {
            try {
              const params =
                new URLSearchParams();

              if (city) {
                params.set(
                  "city",
                  city,
                );
              }

              const response =
                await fetch(
                  `/api/directory/facets?${params.toString()}`,
                  {
                    cache:
                      "no-store",
                    signal:
                      controller.signal,
                  },
                );

              if (!response.ok) {
                return;
              }

              const result:
                FacetResponse =
                  await response.json();

              setFacets(result);

            } catch {
              // Expected when a fast filter change aborts
              // the previous request.
            }
          },
          100,
        );

      return () => {
        window.clearTimeout(
          timer,
        );

        controller.abort();
      };
    },
    [
      city,
    ],
  );


  /*
   * Directory itself is server filtered and paginated.
   */
  useEffect(
    () => {
      const controller =
        new AbortController();

      const timer =
        window.setTimeout(
          async () => {
            setLoading(true);
            setError(null);

            const params =
              new URLSearchParams({
                page:
                  String(page),

                page_size:
                  String(
                    PAGE_SIZE,
                  ),
              });


            if (query.trim()) {
              params.set(
                "q",
                query.trim(),
              );
            }

            if (city) {
              params.set(
                "city",
                city,
              );
            }

            if (area) {
              params.set(
                "area",
                area,
              );
            }

            if (specialty) {
              params.set(
                "specialty",
                specialty,
              );
            }

            if (hospital) {
              params.set(
                "hospital",
                hospital,
              );
            }

            if (gender) {
              params.set(
                "gender",
                gender,
              );
            }

            if (maxFee) {
              params.set(
                "max_fee",
                maxFee,
              );
            }


            try {
              const response =
                await fetch(
                  `/api/directory/doctors?${params.toString()}`,
                  {
                    cache:
                      "no-store",
                    signal:
                      controller.signal,
                  },
                );

              if (!response.ok) {
                throw new Error(
                  "Doctor directory is temporarily unavailable.",
                );
              }

              const result:
                DirectoryResponse =
                  await response.json();

              setData(result);

            } catch (
              reason
            ) {
              if (
                reason instanceof DOMException &&
                reason.name ===
                  "AbortError"
              ) {
                return;
              }

              setError(
                reason instanceof Error
                  ? reason.message
                  : "Could not search doctors.",
              );

            } finally {
              if (
                !controller
                  .signal
                  .aborted
              ) {
                setLoading(false);
              }
            }
          },
          250,
        );

      return () => {
        window.clearTimeout(
          timer,
        );

        controller.abort();
      };
    },
    [
      query,
      city,
      area,
      specialty,
      hospital,
      gender,
      maxFee,
      page,
    ],
  );


  useEffect(
    () => {
      queueMicrotask(() => {
        setPage(1);
      });
    },
    [
      query,
      city,
      area,
      specialty,
      hospital,
      gender,
      maxFee,
    ],
  );


  function clearFilters() {
    setQuery("");
    setCity("");
    setArea("");
    setSpecialty("");
    setHospital("");
    setGender("");
    setMaxFee("");
    setPage(1);
  }


  const hasFilters =
    Boolean(
      query ||
      city ||
      area ||
      specialty ||
      hospital ||
      gender ||
      maxFee,
    );


  return (
    <main className="mx-auto max-w-7xl px-5 py-8 md:px-8 md:py-10">

      <section className="overflow-hidden rounded-[32px] bg-slate-950 px-6 py-9 text-white shadow-sm md:px-10 md:py-12">

        <div className="max-w-3xl">

          <div className="inline-flex items-center gap-2 rounded-full border border-brand-400/20 bg-brand-400/10 px-3 py-1.5 text-xs font-semibold text-brand-300">

            <Stethoscope
              size={14}
            />

            MediBook Doctor Network

          </div>


          <h1 className="mt-5 text-3xl font-bold tracking-tight md:text-5xl">

            Find the right doctor
            across Bangladesh.

          </h1>


          <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-300 md:text-base">

            Search by doctor,
            hospital, specialty,
            city or area. Results
            come directly from the
            MediBook directory.

          </p>


          <div className="relative mt-7 max-w-3xl">

            <Search
              size={19}
              className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400"
            />

            <input
              value={query}
              onChange={
                event =>
                  setQuery(
                    event.target.value,
                  )
              }
              placeholder="Search doctor, hospital, specialty or location"
              className="w-full rounded-2xl border border-white/10 bg-white py-4 pl-12 pr-4 text-sm text-slate-950 outline-none transition focus:ring-2 focus:ring-brand-400"
            />

          </div>

        </div>

      </section>


      <section className="mt-8 grid gap-6 lg:grid-cols-[280px_minmax(0,1fr)]">

        <aside className="h-fit rounded-3xl border border-slate-200 bg-white p-5 shadow-sm lg:sticky lg:top-6">

          <div className="flex items-center gap-2">

            <SlidersHorizontal
              size={17}
              className="text-brand-600"
            />

            <h2 className="font-bold text-slate-950">
              Search filters
            </h2>

          </div>


          <div className="mt-6 space-y-5">

            <SearchableCombobox
              label="Location"
              value={city}
              options={
                facets.cities
              }
              placeholder="Search city"
              onChange={
                value => {
                  setCity(value);
                  setArea("");
                }
              }
            />


            <SearchableCombobox
              label="Area"
              value={area}
              options={
                facets.areas
              }
              placeholder={
                city
                  ? `Search ${city} area`
                  : "Select city or search area"
              }
              onChange={setArea}
            />


            <SearchableCombobox
              label="Specialty"
              value={specialty}
              options={
                facets.specialties
              }
              placeholder="Search specialty"
              onChange={
                setSpecialty
              }
            />


            <SearchableCombobox
              label="Hospital / Clinic"
              value={hospital}
              options={
                facets.hospitals ??
                []
              }
              placeholder={
                city
                  ? `Search hospitals in ${city}`
                  : "Search hospital or clinic"
              }
              onChange={
                setHospital
              }
            />


            <label className="block">

              <span className="mb-1.5 block text-xs font-semibold text-slate-600">
                Gender
              </span>

              <select
                value={gender}
                onChange={
                  event =>
                    setGender(
                      event.target.value,
                    )
                }
                className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100"
              >

                <option value="">
                  Any gender
                </option>

                <option value="female">
                  Female
                </option>

                <option value="male">
                  Male
                </option>

              </select>

            </label>


            <label className="block">

              <span className="mb-1.5 block text-xs font-semibold text-slate-600">
                Maximum consultation fee
              </span>

              <select
                value={maxFee}
                onChange={
                  event =>
                    setMaxFee(
                      event.target.value,
                    )
                }
                className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100"
              >

                <option value="">
                  Any fee
                </option>

                <option value="800">
                  Up to Tk 800
                </option>

                <option value="1000">
                  Up to Tk 1,000
                </option>

                <option value="1200">
                  Up to Tk 1,200
                </option>

                <option value="1500">
                  Up to Tk 1,500
                </option>

                <option value="2000">
                  Up to Tk 2,000
                </option>

              </select>

            </label>


            {hasFilters && (

              <button
                type="button"
                onClick={
                  clearFilters
                }
                className="w-full rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-semibold text-slate-600 transition hover:bg-slate-50 hover:text-slate-950"
              >
                Clear all filters
              </button>

            )}

          </div>

        </aside>


        <div>

          <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">

            <div>

              <h2 className="text-xl font-bold text-slate-950">

                {city
                  ? `Doctors in ${city}`
                  : "Available doctors"}

              </h2>

              <p className="mt-1 text-sm text-slate-500">

                {loading
                  ? "Searching MediBook…"
                  : `${data.count.toLocaleString()} matching doctors`}

              </p>

            </div>


            {data.pages >
            1 && (

              <div className="text-xs font-semibold text-slate-500">

                Page {data.page} of {
                  data.pages
                }

              </div>

            )}

          </div>


          {error && (

            <div className="mt-6 rounded-3xl border border-red-200 bg-red-50 p-6">

              <div className="font-semibold text-red-900">
                Directory unavailable
              </div>

              <div className="mt-1 text-sm text-red-700">
                {error}
              </div>

            </div>

          )}


          {loading && (

            <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">

              {Array.from({
                length: 9,
              }).map(
                (
                  _,
                  index,
                ) => (
                  <div
                    key={index}
                    className="h-72 animate-pulse rounded-3xl bg-slate-100"
                  />
                ),
              )}

            </div>

          )}


          {!loading &&
          !error &&
          data.doctors.length ===
            0 && (

            <div className="mt-6 rounded-3xl border border-dashed border-slate-300 bg-white px-6 py-16 text-center">

              <Search
                size={32}
                className="mx-auto text-slate-300"
              />

              <h3 className="mt-4 text-lg font-bold text-slate-950">
                No doctors found
              </h3>

              <p className="mt-2 text-sm text-slate-500">
                Try another city,
                area, specialty or
                fee range.
              </p>

            </div>

          )}


          {!loading &&
          !error &&
          data.doctors.length >
            0 && (

            <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">

              {data.doctors.map(
                doctor => (

                  <article
                    key={doctor.id}
                    className="flex min-h-[290px] flex-col rounded-3xl border border-slate-200 bg-white p-5 shadow-sm transition duration-200 hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-md"
                  >

                    <div className="flex items-start gap-4">

                      <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-brand-50 text-brand-700">

                        <UserRound
                          size={21}
                        />

                      </div>


                      <div className="min-w-0">

                        <h3 className="truncate font-bold text-slate-950">
                          {doctor.full_name}
                        </h3>

                        <p className="mt-1 text-sm font-semibold text-brand-700">
                          {doctor.specialty.name}
                        </p>

                      </div>

                    </div>


                    <div className="mt-5 space-y-3 text-sm text-slate-600">

                      <div className="flex items-start gap-2.5">

                        <Building2
                          size={16}
                          className="mt-0.5 shrink-0 text-slate-400"
                        />

                        <span className="line-clamp-2">
                          {doctor.clinic_name}
                        </span>

                      </div>


                      <div className="flex items-start gap-2.5">

                        <MapPin
                          size={16}
                          className="mt-0.5 shrink-0 text-slate-400"
                        />

                        <span>
                          {doctor.clinic_location}
                        </span>

                      </div>


                      <div className="flex items-start gap-2.5">

                        <Stethoscope
                          size={16}
                          className="mt-0.5 shrink-0 text-slate-400"
                        />

                        <span>
                          {
                            doctor.experience_years ??
                            0
                          } years experience
                        </span>

                      </div>

                    </div>


                    <div className="mt-auto pt-5">

                      <div className="flex items-end justify-between border-t border-slate-100 pt-4">

                        <div>

                          <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">
                            Consultation
                          </div>

                          <div className="mt-1 text-lg font-bold text-slate-950">
                            Tk {
                              doctor.consultation_fee.toLocaleString()
                            }
                          </div>

                        </div>


                        {doctor.gender && (
                          <div className="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-semibold capitalize text-slate-600">
                            {doctor.gender}
                          </div>
                        )}

                      </div>


                      <Link
                        href={
                          `/doctors/${doctor.id}`
                        }
                        className="mt-4 flex w-full items-center justify-center rounded-xl bg-slate-950 px-4 py-3 text-sm font-semibold text-white transition hover:bg-brand-700"
                      >
                        View doctor
                      </Link>

                    </div>

                  </article>

                ),
              )}

            </div>

          )}


          {data.pages >
          1 && (

            <div className="mt-8 flex items-center justify-center gap-3">

              <button
                type="button"
                disabled={
                  page <= 1
                }
                onClick={
                  () =>
                    setPage(
                      current =>
                        Math.max(
                          1,
                          current - 1,
                        ),
                    )
                }
                className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
              >

                <ChevronLeft
                  size={16}
                />

                Previous

              </button>


              <span className="rounded-xl bg-slate-100 px-4 py-2.5 text-sm font-semibold text-slate-700">

                {page} / {
                  data.pages
                }

              </span>


              <button
                type="button"
                disabled={
                  page >=
                  data.pages
                }
                onClick={
                  () =>
                    setPage(
                      current =>
                        Math.min(
                          data.pages,
                          current + 1,
                        ),
                    )
                }
                className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
              >

                Next

                <ChevronRight
                  size={16}
                />

              </button>

            </div>

          )}

        </div>

      </section>

    </main>
  );
}
