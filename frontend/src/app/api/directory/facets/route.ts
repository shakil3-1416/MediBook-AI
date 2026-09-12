import {
  NextRequest,
} from "next/server";


export const runtime =
  "nodejs";

export const dynamic =
  "force-dynamic";


const API =
  process.env.MEDIBOOK_INTERNAL_API_URL ??
  "http://127.0.0.1:8000/api/v1";


type Doctor = {
  id: string;
  full_name: string;
  gender: string;
  qualification: string;
  experience_years: number;
  specialty: {
    id: string;
    name: string;
  };
  clinic_name: string;
  clinic_location: string;
  consultation_fee: string;
};


type DoctorResponse = {
  count: number;
  doctors: Doctor[];
};


export async function GET(
  request: NextRequest,
) {

  try {

    const upstream =
      await fetch(
        `${API}/doctors`,
        {
          cache:
            "no-store",
        },
      );

    if (!upstream.ok) {

      return Response.json(
        {
          detail:
            "Unable to load doctor facets.",
        },
        {
          status:
            upstream.status,
        },
      );
    }


    const data =
      await upstream.json() as DoctorResponse;


    const doctors =
      Array.isArray(
        data.doctors,
      )
        ? data.doctors
        : [];


    const search =
      request.nextUrl.searchParams
        .get("search")
        ?.trim()
        .toLowerCase() ?? "";


    const filtered =
      search
        ? doctors.filter(
            doctor => {

              const haystack = [
                doctor.full_name,
                doctor.gender,
                doctor.qualification,
                doctor.specialty?.name,
                doctor.clinic_name,
                doctor.clinic_location,
              ]
                .filter(Boolean)
                .join(" ")
                .toLowerCase();

              return haystack.includes(
                search,
              );
            },
          )
        : doctors;


    const specialties =
      Array.from(
        new Set(
          filtered
            .map(
              doctor =>
                doctor.specialty?.name,
            )
            .filter(Boolean),
        ),
      ).sort();


    const genders =
      Array.from(
        new Set(
          filtered
            .map(
              doctor =>
                doctor.gender,
            )
            .filter(Boolean),
        ),
      ).sort();


    const locations =
      Array.from(
        new Set(
          filtered
            .map(
              doctor =>
                doctor.clinic_location,
            )
            .filter(Boolean),
        ),
      ).sort();


    const fees =
      filtered
        .map(
          doctor =>
            Number(
              doctor.consultation_fee,
            ),
        )
        .filter(
          value =>
            Number.isFinite(value),
        );


    const experience =
      filtered
        .map(
          doctor =>
            Number(
              doctor.experience_years,
            ),
        )
        .filter(
          value =>
            Number.isFinite(value),
        );


    return Response.json(
      {
        specialties,
        genders,
        locations,

        consultation_fee: {
          min:
            fees.length
              ? Math.min(...fees)
              : null,

          max:
            fees.length
              ? Math.max(...fees)
              : null,
        },

        experience_years: {
          min:
            experience.length
              ? Math.min(...experience)
              : null,

          max:
            experience.length
              ? Math.max(...experience)
              : null,
        },
      },
    );

  } catch (error) {

    console.error(
      "Doctor facets BFF error:",
      error,
    );

    return Response.json(
      {
        detail:
          "Doctor directory unavailable.",
      },
      {
        status: 502,
      },
    );
  }
}
