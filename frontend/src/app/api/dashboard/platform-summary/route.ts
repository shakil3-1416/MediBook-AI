import {
  NextResponse,
} from "next/server";

import {
  cookies,
} from "next/headers";


const BACKEND =
  process.env.BACKEND_URL ??
  "http://127.0.0.1:8000";


export async function GET() {
  const store =
    await cookies();

  const token =
    store.get(
      "medibook_hospital_session",
    )?.value ??
    store.get(
      "medibook_access_token",
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


  const response =
    await fetch(
      `${BACKEND}/api/v1/platform-control-v2/overview`,
      {
        method:
          "GET",

        headers: {
          Authorization:
            `Bearer ${token}`,
        },

        cache:
          "no-store",
      },
    );


  return new NextResponse(
    await response.text(),
    {
      status:
        response.status,

      headers: {
        "Content-Type":
          response.headers.get(
            "content-type",
          ) ??
          "application/json",
      },
    },
  );
}
