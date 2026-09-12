import { NextResponse } from "next/server";

const BACKEND =
  process.env.BACKEND_URL ??
  "http://127.0.0.1:8000";

export async function POST(
  request: Request,
) {
  try {
    const body =
      await request.json();

    const response =
      await fetch(
        `${BACKEND}/api/v1/auth/signup`,
        {
          method:
            "POST",

          headers: {
            "Content-Type":
              "application/json",
          },

          body:
            JSON.stringify(body),

          cache:
            "no-store",
        },
      );

    const text =
      await response.text();

    let data: unknown = {};

    try {
      data =
        JSON.parse(text);
    } catch {
      data = {
        detail:
          text,
      };
    }

    return NextResponse.json(
      data,
      {
        status:
          response.status,
      },
    );

  } catch {
    return NextResponse.json(
      {
        detail:
          "MediBook signup service is unavailable.",
      },
      {
        status: 500,
      },
    );
  }
}
