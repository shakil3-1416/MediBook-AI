import {
  NextRequest,
  NextResponse,
} from "next/server";

import {
  cookies,
} from "next/headers";

import {
  AUTH_COOKIE,
  AUTH_MAX_AGE,
} from "@/lib/auth-cookie";


const BACKEND =
  process.env.BACKEND_URL ??
  "http://127.0.0.1:8000";


export async function POST(
  request: NextRequest,
) {
  const input =
    await request.json();


  const email =
    String(
      input.email ??
      "",
    );


  const code =
    String(
      input.code ??
      "",
    );


  const password =
    String(
      input.password ??
      "",
    );


  const verified =
    await fetch(
      `${BACKEND}/api/v1/auth/signup/verify`,
      {
        method:
          "POST",

        headers: {
          "Content-Type":
            "application/json",
        },

        body:
          JSON.stringify({
            email,
            code,
          }),

        cache:
          "no-store",
      },
    );


  const verificationText =
    await verified.text();


  if (!verified.ok) {
    return new NextResponse(
      verificationText,
      {
        status:
          verified.status,

        headers: {
          "Content-Type":
            "application/json",
        },
      },
    );
  }


  // Verification completed the account.
  // Authenticate immediately using the password
  // held only in this browser page's memory.
  const login =
    await fetch(
      `${BACKEND}/api/v1/auth/login`,
      {
        method:
          "POST",

        headers: {
          "Content-Type":
            "application/json",
        },

        body:
          JSON.stringify({
            email,
            password,
          }),

        cache:
          "no-store",
      },
    );


  if (!login.ok) {
    return NextResponse.json(
      {
        verified:
          true,

        authenticated:
          false,

        detail:
          "Email verified. Please sign in.",
      },
    );
  }


  const loginData =
    await login.json();


  const token =
    loginData.access_token ??
    loginData.token;


  if (!token) {
    return NextResponse.json(
      {
        verified:
          true,

        authenticated:
          false,
      },
    );
  }


  const cookieStore =
    await cookies();


  cookieStore.set(
    AUTH_COOKIE,
    token,
    {
      httpOnly:
        true,

      sameSite:
        "lax",

      secure:
        process.env.NODE_ENV
        === "production",

      path:
        "/",

      maxAge:
        AUTH_MAX_AGE,
    },
  );


  return NextResponse.json(
    {
      verified:
        true,

      authenticated:
        true,

      user:
        loginData.user,
    },
  );
}
