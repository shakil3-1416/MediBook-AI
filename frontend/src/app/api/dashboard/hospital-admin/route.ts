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


async function relay(
  request: NextRequest,
  method: string,
) {
  const token =
    (
      await cookies()
    ).get(
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

  const params =
    request.nextUrl.searchParams;

  const hospital =
    params.get("hospital") ??
    "medibook-demo";

  const resource =
    params.get("resource") ??
    "audit";

  if (
    ![
      "audit",
      "staff",
      "settings",
    ].includes(resource)
  ) {
    return NextResponse.json(
      {
        detail:
          "Invalid resource.",
      },
      {
        status: 422,
      },
    );
  }

  const response =
    await fetch(
      `${BACKEND}/api/v1/hospital-operations/${encodeURIComponent(hospital)}/${resource}`,
      {
        method,
        headers: {
          Authorization:
            `Bearer ${token}`,
          "Content-Type":
            "application/json",
        },
        body:
          method === "GET"
            ? undefined
            : await request.text(),
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


export function GET(
  request: NextRequest,
) {
  return relay(
    request,
    "GET",
  );
}


export function PATCH(
  request: NextRequest,
) {
  return relay(
    request,
    "PATCH",
  );
}
