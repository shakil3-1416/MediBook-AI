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


async function auth() {
  return (
    await cookies()
  ).get(
    "medibook_hospital_session",
  )?.value;
}


async function relay(
  request: NextRequest,
  method: string,
) {
  const token =
    await auth();

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

  const hospital =
    request.nextUrl.searchParams
      .get("hospital") ??
    "medibook-demo";

  const id =
    request.nextUrl.searchParams
      .get("id");

  const health =
    request.nextUrl.searchParams
      .get("health") === "1";

  let url =
    `${BACKEND}/api/v1/hospital-operations/`
    + `${encodeURIComponent(hospital)}/integrations`;

  if (id) {
    url +=
      `/${encodeURIComponent(id)}`;
  }

  if (health) {
    url += "/health-check";
  }

  const body =
    method === "GET"
      ? undefined
      : await request.text();

  const response =
    await fetch(
      url,
      {
        method,
        headers: {
          Authorization:
            `Bearer ${token}`,
          ...(body
            ? {
                "Content-Type":
                  "application/json",
              }
            : {}),
        },
        body:
          body || undefined,
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


export function POST(
  request: NextRequest,
) {
  return relay(
    request,
    "POST",
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
