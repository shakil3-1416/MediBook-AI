"use client";

import {
  Stethoscope,
} from "lucide-react";

import Link from "next/link";
import {
  usePathname,
} from "next/navigation";


export function MediBookFooter() {

  const pathname =
    usePathname();


  if (
    pathname === "/login" ||
    pathname === "/signup" ||
    pathname.startsWith(
      "/assistant",
    )
  ) {
    return null;
  }


  return (
    <footer className="mt-16 border-t border-slate-200 bg-white">

      <div className="mx-auto grid max-w-7xl gap-8 px-5 py-10 md:grid-cols-[1fr_auto] md:px-8">

        <div>

          <div className="flex items-center gap-2 font-black text-slate-950">

            <Stethoscope
              size={18}
              className="text-brand-600"
            />

            MediBook

          </div>

          <p className="mt-3 max-w-xl text-sm leading-6 text-slate-500">

            Search doctors,
            discover available appointments,
            and manage your bookings
            from one healthcare scheduling platform.

          </p>

        </div>


        <div className="flex flex-wrap gap-x-6 gap-y-3 text-sm font-semibold text-slate-500">

          <Link
            href="/doctors"
            className="hover:text-slate-950"
          >
            Doctors
          </Link>

          <Link
            href="/assistant"
            className="hover:text-slate-950"
          >
            Assistant
          </Link>

          <Link
            href="/appointments"
            className="hover:text-slate-950"
          >
            Appointments
          </Link>

          <Link
            href="/profile"
            className="hover:text-slate-950"
          >
            Profile
          </Link>

        </div>

      </div>

    </footer>
  );
}
