import { NextRequest, NextResponse } from "next/server";

const BACKEND =
  process.env.BACKEND_URL ??
  "http://127.0.0.1:8000";

function safeNext(value: FormDataEntryValue | null) {
  if (
    typeof value === "string" &&
    value.startsWith("/") &&
    !value.startsWith("//")
  ) {
    return value;
  }

  return "/widget/medibook-demo";
}

function loginUrl(
  request: NextRequest,
  next: string,
  message: string,
) {
  const url = new URL(
    "/login",
    process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000",
  );

  url.searchParams.set(
    "next",
    next,
  );

  url.searchParams.set(
    "error",
    message,
  );

  return url;
}

export async function POST(
  request: NextRequest,
) {
  const form =
    await request.formData();

  const email =
    String(
      form.get("email") ?? "",
    ).trim();

  const password =
    String(
      form.get("password") ?? "",
    );

  const next =
    safeNext(
      form.get("next"),
    );

  if (!email || !password) {
    return NextResponse.redirect(
      loginUrl(
        request,
        next,
        "Email and password are required.",
      ),
      303,
    );
  }

  try {
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
            JSON.stringify({
              email,
              password,
            }),

          cache: "no-store",
        },
      );

    const raw =
      await response.text();

    let data: {
      detail?: unknown;
      access_token?: string;
      token?: string;
      session_token?: string;
      accessToken?: string;
    } = {};

    try {
      data =
        JSON.parse(raw);
    } catch {
      data = {
        detail: raw,
      };
    }

    if (!response.ok) {
      return NextResponse.redirect(
        loginUrl(
          request,
          next,
          typeof data.detail ===
            "string"
            ? data.detail
            : "Invalid email or password.",
        ),
        303,
      );
    }

    const token =
      data.access_token ??
      data.token ??
      data.session_token ??
      data.accessToken;

    if (!token) {
      return NextResponse.redirect(
        loginUrl(
          request,
          next,
          "MediBook could not create your session.",
        ),
        303,
      );
    }

    const destination =
      new URL(
        next,
        process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000",
      );

    const result =
      NextResponse.redirect(
        destination,
        303,
      );

    result.cookies.set(
      "medibook_session",
      token,
      {
        httpOnly: true,
        sameSite: "lax",
        secure:
          process.env.NODE_ENV ===
          "production",
        path: "/",
        maxAge:
          60 * 60 * 24 * 7,
      },
    );

    return result;

  } catch {
    return NextResponse.redirect(
      loginUrl(
        request,
        next,
        "Authentication service is unavailable.",
      ),
      303,
    );
  }
}
