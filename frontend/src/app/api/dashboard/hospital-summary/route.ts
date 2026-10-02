import {
  NextRequest,
  NextResponse,
} from "next/server";

import {
  cookies,
} from "next/headers";

import {
  activeHospitalSlug,
} from "@/lib/server/hospital-context";


const BACKEND =
  process.env.BACKEND_URL ??
  "http://127.0.0.1:8000";


export async function GET(
  request: NextRequest,
) {
  const cookieStore =
    await cookies();


  const token =
    cookieStore.get(
      "medibook_hospital_session",
    )?.value;


  if (!token) {
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


  const hospitalSlug =
    await activeHospitalSlug(
      request.nextUrl.searchParams.get("hospital"),
    );


  if (!hospitalSlug) {
    return NextResponse.json(
      {
        detail:
          "No active hospital workspace selected.",
      },
      {
        status: 422,
      },
    );
  }


  const response =
    await fetch(
      `${BACKEND}/api/v1/hospital-operations/${encodeURIComponent(
        hospitalSlug,
      )}/summary`,
      {
        headers: {
          Authorization:
            `Bearer ${token}`,
        },

        cache:
          "no-store",
      },
    );


  const body =
    await response.text();


  return new NextResponse(
    body,
    {
      status:
        response.status,

      headers: {
        "Content-Type":
          response.headers.get(
            "content-type",
          )
          ??
          "application/json",
      },
    },
  );
}
