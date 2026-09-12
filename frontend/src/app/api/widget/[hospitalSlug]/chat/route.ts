import {
  NextResponse,
} from "next/server";

import {
  cookies,
} from "next/headers";


const BACKEND =
  process.env.BACKEND_URL ??
  "http://127.0.0.1:8000";


export async function POST(
  request: Request,
  context: {
    params: Promise<{
      hospitalSlug: string;
    }>;
  },
) {
  const {
    hospitalSlug,
  } = await context.params;

  const payload =
    await request.json();

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
      `${BACKEND}/api/v1/chat/stream`,
      {
        method:
          "POST",

        headers: {
          "Content-Type":
            "application/json",

          Authorization:
            `Bearer ${token}`,

          "X-MediBook-Hospital-Slug":
            hospitalSlug,
        },

        body:
          JSON.stringify({
            ...payload,

            hospital_slug:
              hospitalSlug,
          }),
      },
    );


  return new NextResponse(
    response.body,
    {
      status:
        response.status,

      headers: {
        "Content-Type":
          response.headers.get(
            "Content-Type",
          )
          ??
          "text/plain; charset=utf-8",
      },
    },
  );
}
