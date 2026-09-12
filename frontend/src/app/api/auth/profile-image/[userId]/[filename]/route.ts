import {
  NextResponse,
} from "next/server";

import {
  backendBaseUrl,
  patientAuthorization,
} from "@/lib/patient-server-auth";


type RouteContext = {
  params:
    Promise<{
      userId: string;
      filename: string;
    }>;
};


export async function GET(
  _request: Request,
  context: RouteContext,
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

  const {
    userId,
    filename,
  } =
    await context.params;

  const response =
    await fetch(
      `${backendBaseUrl()}/api/v1/identity/profile/image/${
        encodeURIComponent(
          userId,
        )
      }/${
        encodeURIComponent(
          filename,
        )
      }`,
      {
        headers: auth,
        cache: "no-store",
      },
    );

  if (!response.ok) {

    let data: unknown = {
      detail:
        "Image unavailable.",
    };

    try {
      data =
        await response.json();
    } catch {
      // Keep generic error.
    }

    return NextResponse.json(
      data,
      {
        status:
          response.status,
      },
    );
  }

  return new Response(
    response.body,
    {
      status: 200,

      headers: {
        "Content-Type":
          response.headers.get(
            "content-type",
          )
          ??
          "application/octet-stream",

        "Cache-Control":
          "private, max-age=3600",
      },
    },
  );
}
