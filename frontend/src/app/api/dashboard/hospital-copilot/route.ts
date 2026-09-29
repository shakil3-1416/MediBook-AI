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

  const action =
    request.nextUrl.searchParams.get(
      "action",
    ) ??
    "query";

  const proposalId =
    request.nextUrl.searchParams.get(
      "proposalId",
    );

  let path =
    `/api/v1/hospital-operations/${encodeURIComponent(
      hospital,
    )}/copilot/query`;

  if (
    action ===
    "proposal"
  ) {
    path =
      `/api/v1/hospital-operations/${encodeURIComponent(
        hospital,
      )}/copilot/proposals`;
  }

  if (
    action ===
      "proposal-get" &&
    proposalId
  ) {
    path =
      `/api/v1/hospital-operations/${encodeURIComponent(
        hospital,
      )}/copilot/proposals/${encodeURIComponent(
        proposalId,
      )}`;
  }

  if (
    action ===
      "proposal-confirm" &&
    proposalId
  ) {
    path =
      `/api/v1/hospital-operations/${encodeURIComponent(
        hospital,
      )}/copilot/proposals/${encodeURIComponent(
        proposalId,
      )}/confirm`;
  }


  if (
    action ===
      "proposal-execute" &&
    proposalId
  ) {
    path =
      `/api/v1/hospital-operations/${encodeURIComponent(
        hospital,
      )}/copilot/proposals/${encodeURIComponent(
        proposalId,
      )}/execute`;
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
