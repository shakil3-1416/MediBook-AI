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


async function getToken() {

  const jar =
    await cookies();

  return jar.get(
    AUTH_COOKIE,
  )?.value;
}


export async function GET(
  request: Request,
) {

  const token =
    await getToken();

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


  const incoming =
    new URL(request.url);

  const upstreamUrl =
    new URL(
      `${BACKEND}/appointments`,
    );


  incoming.searchParams.forEach(
    (
      value,
      key,
    ) => {
      upstreamUrl.searchParams.set(
        key,
        value,
      );
    },
  );


  try {

    const upstream =
      await fetch(
        upstreamUrl,
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
            upstream.headers.get(
              "content-type",
            ) ??
            "application/json; charset=utf-8",
        },
      },
    );

  } catch (error) {

    console.error(
      "Appointments proxy error:",
      error,
    );

    return Response.json(
      {
        detail:
          "Appointment service unavailable.",
      },
      {
        status: 502,
      },
    );
  }
}
