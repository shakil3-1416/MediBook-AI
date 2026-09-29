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

const RESOURCES =
  new Set([
    "audit",
    "staff",
    "settings",
  ]);


async function relay(
  request: NextRequest,
  method: string,
) {
  const cookieStore =
    await cookies();

  const token =
    cookieStore.get(
      "medibook_hospital_session",
    )?.value;

  const hospital =
    cookieStore.get(
      "medibook_active_hospital",
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

  if (!hospital) {
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

  const resource =
    request.nextUrl
      .searchParams
      .get("resource");

  if (
    !resource ||
    !RESOURCES.has(
      resource,
    )
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

  const id =
    request.nextUrl
      .searchParams
      .get("id");

  const params =
    new URLSearchParams(
      request.nextUrl.searchParams,
    );

  params.delete(
    "resource",
  );

  params.delete(
    "id",
  );

  let url =
    `${BACKEND}/api/v1/hospital-operations/${encodeURIComponent(
      hospital,
    )}/${resource}`;

  if (id) {
    url +=
      `/${encodeURIComponent(id)}`;
  }

  const suffix =
    params.toString();

  if (suffix) {
    url +=
      `?${suffix}`;
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


export function PATCH(
  request: NextRequest,
) {
  return relay(
    request,
    "PATCH",
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
