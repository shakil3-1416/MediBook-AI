import {
  NextResponse,
} from "next/server";

import {
  backendBaseUrl,
  patientAuthorization,
} from "@/lib/patient-server-auth";


export async function POST(
  request: Request,
) {

  const auth =
    await patientAuthorization();

  if (!auth) {
    return NextResponse.json(
      {
        detail:
          "Authentication required.",
      },
      {
        status: 401,
      },
    );
  }

  const response =
    await fetch(
      `${backendBaseUrl()}/api/v1/identity/email/change/verify`,
      {
        method: "POST",

        headers: {
          ...auth,
          "Content-Type":
            "application/json",
        },

        body:
          await request.text(),

        cache:
          "no-store",
      },
    );

  return new Response(
    await response.text(),
    {
      status:
        response.status,

      headers: {
        "Content-Type":
          "application/json",
      },
    },
  );
}
