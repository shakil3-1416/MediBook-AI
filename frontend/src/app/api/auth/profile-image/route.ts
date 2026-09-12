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

  const body =
    await request.arrayBuffer();

  const contentType =
    request.headers.get(
      "content-type",
    )
    ??
    "application/octet-stream";

  const response =
    await fetch(
      `${backendBaseUrl()}/api/v1/identity/profile/image`,
      {
        method: "POST",

        headers: {
          ...auth,
          "Content-Type":
            contentType,
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
