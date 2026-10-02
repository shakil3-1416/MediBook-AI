import {
  NextRequest,
  NextResponse,
} from "next/server";

import {
  staffSessionToken,
} from "@/lib/server/hospital-context";



const BACKEND =
  process.env.BACKEND_URL ??
  "http://127.0.0.1:8000";


async function relay(
  request: NextRequest,
  method: string,
) {

  const token =
    await staffSessionToken();

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


  const action =
    request.nextUrl.searchParams.get(
      "action",
    ) ??
    "overview";

  const hospitalSlug =
    request.nextUrl.searchParams.get(
      "hospital",
    );


  let path =
    "/api/v1/platform-control-v2/overview";


  if (
    action ===
    "hospitals"
  ) {
    path =
      "/api/v1/platform-control-v2/hospitals";
  }


  if (
    action ===
      "detail" &&
    hospitalSlug
  ) {
    path =
      `/api/v1/platform-control-v2/hospitals/${encodeURIComponent(
        hospitalSlug,
      )}`;
  }


  if (
    action ===
    "provision"
  ) {
    path =
      "/api/v1/platform-control-v2/hospitals";
  }


  if (
    action ===
      "status" &&
    hospitalSlug
  ) {
    path =
      `/api/v1/platform-control-v2/hospitals/${encodeURIComponent(
        hospitalSlug,
      )}/status`;
  }


  const body =
    method === "GET"
      ? undefined
      : await request.text();


  const response =
    await fetch(
      `${BACKEND}${path}`,
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
          body ||
          undefined,

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
