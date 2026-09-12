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
        `${BACKEND}/api/v1/auth/login`,
        {
          method: "POST",
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

    let data: {
      detail?: unknown;
      access_token?: string;
      token?: string;
      session_token?: string;
      accessToken?: string;
      user?: unknown;
    } = {};

    try {
      data =
        JSON.parse(text);
    } catch {
      data = {
        detail:
          text ||
          "Invalid backend response",
      };
    }

    if (!response.ok) {
      return NextResponse.json(
        data,
        {
          status:
            response.status,
        },
      );
    }

    const token =
      data.access_token ??
      data.token ??
      data.session_token ??
      data.accessToken;

    if (!token) {
      return NextResponse.json(
        {
          detail:
            "Authentication succeeded but no session token was returned.",
        },
        {
          status: 502,
        },
      );
    }

    const result =
      NextResponse.json({
        ok: true,
        user:
          data.user ??
          null,
      });

    result.cookies.set(
      "medibook_session",
      token,
      {
        httpOnly:
          true,

        sameSite:
          "lax",

        secure:
          process.env.NODE_ENV ===
          "production",

        path:
          "/",

        maxAge:
          60 * 60 * 24 * 7,
      },
    );

    return result;

  } catch {
    return NextResponse.json(
      {
        detail:
          "MediBook authentication service is unavailable.",
      },
      {
        status: 500,
      },
    );
  }
}
