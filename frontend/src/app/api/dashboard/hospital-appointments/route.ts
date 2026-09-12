import {
  NextRequest,
  NextResponse,
} from "next/server";

import {
  cookies,
} from "next/headers";


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


  const query =
    request.nextUrl
      .searchParams;


  const hospital =
    query.get(
      "hospital",
    )
    ??
    "medibook-demo";


  const backendQuery =
    new URLSearchParams();


  for (const key of [
    "status",
    "date_from",
    "date_to",
    "search",
    "limit",
  ]) {
    const value =
      query.get(
        key,
      );


    if (value) {
      backendQuery.set(
        key,
        value,
      );
    }
  }


  const suffix =
    backendQuery
      .toString();


  const url =
    `${BACKEND}/api/v1/hospital-operations/${encodeURIComponent(
      hospital,
    )}/appointments`
    +
    (
      suffix
        ? `?${suffix}`
        : ""
    );


  const response =
    await fetch(
      url,
      {
        headers: {
          Authorization:
            `Bearer ${token}`,
        },

        cache:
          "no-store",
      },
    );


  const raw =
    await response.text();


  return new NextResponse(
    raw,
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
