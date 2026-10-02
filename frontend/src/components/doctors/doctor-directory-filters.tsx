"use client";

import {
  Search,
} from "lucide-react";

import {
  usePathname,
  useRouter,
  useSearchParams,
} from "next/navigation";

import {
  useEffect,
  useState,
} from "react";


export function DoctorDirectoryFilters() {
  const router =
    useRouter();

  const pathname =
    usePathname();

  const searchParams =
    useSearchParams();

  const [name, setName] =
    useState(
      searchParams.get("name") ?? "",
    );

  const [
    specialty,
    setSpecialty,
  ] = useState(
    searchParams.get(
      "specialty",
    ) ?? "",
  );

  const [
    location,
    setLocation,
  ] = useState(
    searchParams.get(
      "location",
    ) ?? "",
  );

  const [gender, setGender] =
    useState(
      searchParams.get("gender") ?? "",
    );


  useEffect(() => {
    const timer =
      window.setTimeout(() => {
        const params =
          new URLSearchParams();

        const values = {
          name,
          specialty,
          location,
          gender,
        };

        for (
          const [
            key,
            value,
          ] of Object.entries(
            values,
          )
        ) {
          const clean =
            value.trim();

          if (clean) {
            params.set(
              key,
              clean,
            );
          }
        }

        const query =
          params.toString();

        router.replace(
          query
            ? `${pathname}?${query}`
            : pathname,
          {
            scroll: false,
          },
        );
      }, 300);

    return () => {
      window.clearTimeout(
        timer,
      );
    };
  }, [
    gender,
    location,
    name,
    pathname,
    router,
    specialty,
  ]);


  return (
    <section className="mt-7 grid gap-3 rounded-2xl border border-slate-200 bg-white p-4 md:grid-cols-2 xl:grid-cols-4">
      <label className="relative">
        <Search
          size={16}
          className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-500"
        />

        <input
          value={name}
          onChange={(
            event,
          ) =>
            setName(
              event.target.value,
            )
          }
          placeholder="Doctor name"
          className="h-11 w-full rounded-xl border border-slate-200 pl-9 pr-3 text-sm outline-none transition focus:border-emerald-500"
        />
      </label>

      <input
        value={specialty}
        onChange={(
          event,
        ) =>
          setSpecialty(
            event.target.value,
          )
        }
        placeholder="Specialty"
        className="h-11 rounded-xl border border-slate-200 px-3 text-sm outline-none transition focus:border-emerald-500"
      />

      <input
        value={location}
        onChange={(
          event,
        ) =>
          setLocation(
            event.target.value,
          )
        }
        placeholder="Location"
        className="h-11 rounded-xl border border-slate-200 px-3 text-sm outline-none transition focus:border-emerald-500"
      />

      <select
        value={gender}
        onChange={(
          event,
        ) =>
          setGender(
            event.target.value,
          )
        }
        className="h-11 rounded-xl border border-slate-200 bg-white px-3 text-sm outline-none transition focus:border-emerald-500"
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
    </section>
  );
}
