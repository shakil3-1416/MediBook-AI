import {
  NextResponse,
} from "next/server";

import {
  backendBaseUrl,
  patientAuthorization,
} from "@/lib/patient-server-auth";


export async function PATCH(
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

  const body =
    await request.text();

  const response =
    await fetch(
      `${backendBaseUrl()}/api/v1/identity/profile`,
      {
        method: "PATCH",

        headers: {
          ...auth,
          "Content-Type":
            "application/json",
        },

        body,

        cache: "no-store",
      },
    );

  const data =
    await response.json();

  return NextResponse.json(
    data,
    {
      status:
        response.status,
    },
  );
}
