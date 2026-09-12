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


type Context = {
  params:
    Promise<{
      id: string;
    }>;
};


export async function GET(
  _request: Request,
  context: Context,
) {

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

  const {
    id,
  } = await context.params;

  const upstream =
    await fetch(
      `${BACKEND}/conversations/${encodeURIComponent(id)}`,
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
}


export async function DELETE(
  _request: Request,
  context: Context,
) {

  const token =
    await authToken();

  if (!token) {
    return new Response(
      null,
      {
        status: 401,
      },
    );
  }

  const {
    id,
  } = await context.params;

  const upstream =
    await fetch(
      `${BACKEND}/conversations/${encodeURIComponent(id)}`,
      {
        method: "DELETE",

        headers: {
          Authorization:
            `Bearer ${token}`,
        },

        cache:
          "no-store",
      },
    );

  return new Response(
    null,
    {
      status:
        upstream.status,
    },
  );
}
