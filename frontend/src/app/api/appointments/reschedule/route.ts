import {
  cookies,
} from "next/headers";

import {
  AUTH_COOKIE,
} from "@/lib/auth-cookie";

import {
  patientHospitalSlug,
} from "@/lib/server/hospital-context";


export const runtime =
  "nodejs";

export const dynamic =
  "force-dynamic";


const BACKEND =
  process.env.MEDIBOOK_INTERNAL_API_URL ??
  "http://127.0.0.1:8000/api/v1";


export async function POST(
  request: Request,
) {

  const jar =
    await cookies();

  const token =
    jar.get(
      AUTH_COOKIE,
    )?.value;


  if (!token) {

    return Response.json(
      {
        detail:
          "Authentication required.",
      },
      {
        status: 401,
      },
    );
  }


  const body =
    await request.text();


  try {

    const upstream =
      await fetch(
        `${BACKEND}/appointments/reschedule`,
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json",

            Authorization:
              `Bearer ${token}`,
            "X-MediBook-Hospital-Slug":
              await patientHospitalSlug(
                new URL(request.url).searchParams.get("hospital"),
              ),
          },

          body,

          cache:
            "no-store",
        },
      );


    return new Response(
      await upstream.text(),
      {
        status:
          upstream.status,

        headers: {
          "Content-Type":
            upstream.headers.get(
              "content-type",
            ) ??
            "application/json",
        },
      },
    );

  } catch (error) {

    console.error(
      "Reschedule appointment proxy error:",
      error,
    );

    return Response.json(
      {
        detail:
          "Appointment service unavailable.",
      },
      {
        status: 502,
      },
    );
  }
}
