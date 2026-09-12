import {
  cookies,
} from "next/headers";

import {
  AUTH_COOKIE,
} from "@/lib/auth-cookie";


export const runtime =
  "nodejs";

export const dynamic =
  "force-dynamic";


const BACKEND =
  process.env.MEDIBOOK_INTERNAL_API_URL ??
  "http://127.0.0.1:8000/api/v1";


async function authToken() {
  const jar =
    await cookies();

  return jar.get(
    AUTH_COOKIE,
  )?.value;
}


export async function GET() {

  const token =
    await authToken();

  if (!token) {
    return Response.json(
      {
        detail:
          "Authentication required.",
      },
      {
        status: 401,
      },
    );
  }

  try {

    const upstream =
      await fetch(
        `${BACKEND}/conversations`,
        {
          headers: {
            Authorization:
              `Bearer ${token}`,
          },

          cache:
            "no-store",
        },
      );

    const body =
      await upstream.text();

    return new Response(
      body,
      {
        status:
          upstream.status,

        headers: {
          "Content-Type":
            "application/json; charset=utf-8",
        },
      },
    );

  } catch (error) {

    console.error(
      "Conversation list proxy error:",
      error,
    );

    return Response.json(
      {
        detail:
          "Conversation service unavailable.",
      },
      {
        status: 502,
      },
    );
  }
}


export async function POST() {

  const token =
    await authToken();

  if (!token) {
    return Response.json(
      {
        detail:
          "Authentication required.",
      },
      {
        status: 401,
      },
    );
  }

  try {

    const upstream =
      await fetch(
        `${BACKEND}/conversations`,
        {
          method: "POST",

          headers: {
            Authorization:
              `Bearer ${token}`,
          },

          cache:
            "no-store",
        },
      );

    const body =
      await upstream.text();

    return new Response(
      body,
      {
        status:
          upstream.status,

        headers: {
          "Content-Type":
            "application/json; charset=utf-8",
        },
      },
    );

  } catch (error) {

    console.error(
      "Conversation create proxy error:",
      error,
    );

    return Response.json(
      {
        detail:
          "Conversation service unavailable.",
      },
      {
        status: 502,
      },
    );
  }
}
