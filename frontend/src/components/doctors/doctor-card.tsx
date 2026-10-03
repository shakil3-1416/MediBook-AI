"use client";

import {
  Building2,
  MapPin,
  Stethoscope,
} from "lucide-react";

import Link from "next/link";

import type {
  Doctor,
} from "@/types/api";


export function DoctorCard({
  doctor,
}: {
  doctor: Doctor;
}) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5">
      <div className="flex gap-4">
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-brand-50 text-brand-700">
          <Stethoscope
            size={21}
          />
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h3 className="font-bold">
                {doctor.full_name}
              </h3>

              <p className="mt-1 text-sm font-semibold text-brand-700">
                {
                  doctor.specialty
                    .name
                }
              </p>
            </div>

            <div className="text-right">
              <div className="text-xs text-slate-500">
                Consultation
              </div>

              <div className="font-bold">
                Tk{" "}
                {Number(
                  doctor.consultation_fee
                ).toLocaleString(
                  "en-BD"
                )}
              </div>
            </div>
          </div>

          <p className="mt-3 text-sm text-slate-600">
            {
              doctor.qualification
            }
            {" · "}
            {
              doctor.experience_years
            }{" "}
            years experience
          </p>

          <div className="mt-4 space-y-2 text-sm text-slate-500">
            <div className="flex items-center gap-2">
              <Building2
                size={15}
              />

              {
                doctor.clinic_name
              }
            </div>

            <div className="flex items-center gap-2">
              <MapPin
                size={15}
              />

              {
                doctor.clinic_location
              }
            </div>
          </div>

          <div className="mt-5 flex gap-2">
            <Link
              href={`/doctors/${doctor.id}`}
              className="rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-semibold text-white"
            >
              View availability
            </Link>

            <Link
              href={`/assistant?doctor=${encodeURIComponent(
                doctor.full_name
              )}`}
              className="rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-semibold"
            >
              Ask AI
            </Link>
          </div>
        </div>
      </div>
    </article>
  );
}
