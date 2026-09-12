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


export async function POST(
  request: Request,
) {

  const jar =
    await cookies();

  const token =
    jar.get(
      AUTH_COOKIE,
    )?.value;

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


  const body =
    await request.text();


  let upstream: Response;

  try {

    upstream =
      await fetch(
        `${BACKEND}/chat/stream`,
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json",

            Authorization:
              `Bearer ${token}`,
          },

          body,

          cache:
            "no-store",
        },
      );

  } catch (error) {

    console.error(
      "Chat stream proxy error:",
      error,
    );

    return Response.json(
      {
        detail:
          "MediBook chat service is unavailable.",
      },
      {
        status: 502,
      },
    );
  }


  if (!upstream.body) {

    const text =
      await upstream.text();

    return new Response(
      text,
      {
        status:
          upstream.status,

        headers: {
          "Content-Type":
            upstream.headers.get(
              "content-type",
            ) ??
            "application/json",
        },
      },
    );
  }


  return new Response(
    upstream.body,
    {
      status:
        upstream.status,

      headers: {
        "Content-Type":
          upstream.headers.get(
            "content-type",
          ) ??
          "application/x-ndjson; charset=utf-8",

        "Cache-Control":
          "no-cache, no-transform",

        Connection:
          "keep-alive",
      },
    },
  );
}
