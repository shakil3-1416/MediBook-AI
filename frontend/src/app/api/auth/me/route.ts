import {
  NextResponse,
} from "next/server";

import {
  backendBaseUrl,
  patientAuthorization,
} from "@/lib/patient-server-auth";


export async function GET() {

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
      `${backendBaseUrl()}/api/v1/identity/profile`,
      {
        headers: auth,
        cache: "no-store",
      },
    );

  const data =
    await response.json();

  if (!response.ok) {
    return NextResponse.json(
      data,
      {
        status:
          response.status,
      },
    );
  }

  // Keep both response shapes working:
  // profile page can read fields directly,
  // widget can read payload.user.
  return NextResponse.json(
    {
      ...data,
      user: data,
    },
  );
}
