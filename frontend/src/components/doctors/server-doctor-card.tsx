import {
  ArrowRight,
  MapPin,
  Stethoscope,
} from "lucide-react";

import Link from "next/link";

import type {
  Doctor,
} from "@/lib/server/medibook";


export function ServerDoctorCard({
  doctor,
}: {
  doctor: Doctor;
}) {
  return (
    <article className="group rounded-2xl border border-slate-200 bg-white p-5 transition hover:border-slate-300 hover:shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-slate-950">
            {doctor.full_name}
          </h2>

          <div className="mt-2 flex items-center gap-2 text-sm font-semibold text-brand-700">
            <Stethoscope
              size={15}
            />

            {
              doctor.specialty.name
            }
          </div>
        </div>

        <div className="rounded-xl bg-brand-50 px-3 py-2 text-right">
          <div className="text-xs text-brand-700">
            Consultation
          </div>

          <div className="font-bold text-brand-950">
            Tk{" "}
            {Number(
              doctor.consultation_fee,
            ).toLocaleString(
              "en-BD",
            )}
          </div>
        </div>
      </div>

      <div className="mt-4 text-sm text-slate-500">
        {
          doctor.qualification
        }
        {" · "}
        {
          doctor.experience_years
        }{" "}
        years experience
      </div>

      <div className="mt-3 flex items-center gap-2 text-sm text-slate-500">
        <MapPin
          size={15}
        />

        {
          doctor.clinic_name
        }
        {" · "}
        {
          doctor.clinic_location
        }
      </div>

      <Link
        href={`/doctors/${doctor.id}`}
        prefetch
        className="mt-5 inline-flex items-center gap-2 text-sm font-bold text-brand-700 transition group-hover:gap-3"
      >
        View profile

        <ArrowRight
          size={15}
        />
      </Link>
    </article>
  );
}
