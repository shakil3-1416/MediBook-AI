import {
  NextResponse,
} from "next/server";

import {
  cookies,
} from "next/headers";


const BACKEND =
  process.env.BACKEND_URL ??
  "http://127.0.0.1:8000";


export async function GET(
  _request: Request,
  context: {
    params: Promise<{
      hospitalSlug: string;
    }>;
  },
) {
  const {
    hospitalSlug,
  } = await context.params;

  const cookieStore =
    await cookies();

  const token =
    cookieStore.get(
      "medibook_session",
    )?.value;


  if (!token) {
    return NextResponse.json(
      {
        detail:
          "Authentication required.",
        requires_auth:
          true,
      },
      {
        status: 401,
      },
    );
  }


  const response =
    await fetch(
      `${BACKEND}/api/v1/appointments?include_cancelled=true`,
      {
        cache:
          "no-store",

        headers: {
          Authorization:
            `Bearer ${token}`,

          "X-MediBook-Hospital-Slug":
            hospitalSlug,
        },
      },
    );


  return new NextResponse(
    await response.text(),
    {
      status:
        response.status,

      headers: {
        "Content-Type":
          "application/json",
      },
    },
  );
}
