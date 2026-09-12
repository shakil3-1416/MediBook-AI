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

  const body =
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
      },
      {
        status: 401,
      },
    );
  }


  const response =
    await fetch(
      `${BACKEND}/api/v1/appointments/cancel`,
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
          JSON.stringify(
            body,
          ),
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
