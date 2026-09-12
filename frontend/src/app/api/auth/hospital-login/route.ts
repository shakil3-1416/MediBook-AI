import {
  NextRequest,
  NextResponse,
} from "next/server";

import {
  cookies,
} from "next/headers";


const BACKEND =
  process.env.BACKEND_URL ??
  "http://127.0.0.1:8000";


export async function POST(
  request: NextRequest,
) {
  let body: {
    email?: string;
    password?: string;
  };


  try {
    body =
      await request.json();
  } catch {
    return NextResponse.json(
      {
        detail:
          "Invalid login request.",
      },
      {
        status: 400,
      },
    );
  }


  const email =
    String(
      body.email ??
      "",
    ).trim();


  const password =
    String(
      body.password ??
      "",
    );


  if (
    !email ||
    !password
  ) {
    return NextResponse.json(
      {
        detail:
          "Email and password are required.",
      },
      {
        status: 422,
      },
    );
  }


  // --------------------------------------------------
  // Authenticate against the real MediBook backend.
  // --------------------------------------------------

  const loginResponse =
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


  const loginRaw =
    await loginResponse.text();


  if (!loginResponse.ok) {
    return new NextResponse(
      loginRaw,
      {
        status:
          loginResponse.status,

        headers: {
          "Content-Type":
            loginResponse.headers.get(
              "content-type",
            )
            ??
            "application/json",
        },
      },
    );
  }


  let loginData: {
    access_token?: string;
    token?: string;
  };


  try {
    loginData =
      JSON.parse(
        loginRaw,
      );
  } catch {
    return NextResponse.json(
      {
        detail:
          "Invalid authentication response.",
      },
      {
        status: 502,
      },
    );
  }


  const token =
    loginData.access_token ??
    loginData.token;


  if (!token) {
    return NextResponse.json(
      {
        detail:
          "Authentication token missing.",
      },
      {
        status: 502,
      },
    );
  }


  // --------------------------------------------------
  // Verify the authenticated user with /auth/me.
  // This prevents trusting client-supplied role data.
  // --------------------------------------------------

  const meResponse =
    await fetch(
      `${BACKEND}/api/v1/auth/me`,
      {
        headers: {
          Authorization:
            `Bearer ${token}`,
        },

        cache:
          "no-store",
      },
    );


  if (!meResponse.ok) {
    return NextResponse.json(
      {
        detail:
          "Could not verify authenticated user.",
      },
      {
        status: 401,
      },
    );
  }


  const user =
    await meResponse.json();


  // --------------------------------------------------
  // Store the same HttpOnly session cookie used by the
  // rest of the MediBook frontend.
  //
  // Actual hospital authorization still belongs to the
  // backend hospital-operations endpoint.
  // --------------------------------------------------

  const cookieStore =
    await cookies();


  cookieStore.set(
    "medibook_hospital_session",
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
        60 * 60 * 12,
    },
  );


  return NextResponse.json(
    {
      authenticated:
        true,

      user,
    },
  );
}
