import { NextRequest, NextResponse } from "next/server";

const BACKEND =
  process.env.BACKEND_URL ??
  "http://127.0.0.1:8000";

function safeNext(
  value: FormDataEntryValue | null,
) {
  if (
    typeof value === "string" &&
    value.startsWith("/") &&
    !value.startsWith("//")
  ) {
    return value;
  }

  return "/widget/medibook-demo";
}

function signupUrl(
  request: NextRequest,
  next: string,
  error: string,
) {
  const url =
    new URL(
      "/signup",
      process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000",
    );

  url.searchParams.set(
    "next",
    next,
  );

  url.searchParams.set(
    "error",
    error,
  );

  return url;
}

export async function POST(
  request: NextRequest,
) {
  const form =
    await request.formData();

  const fullName =
    String(
      form.get("full_name") ?? "",
    ).trim();

  const email =
    String(
      form.get("email") ?? "",
    ).trim();

  const phone =
    String(
      form.get("phone") ?? "",
    ).trim();

  const password =
    String(
      form.get("password") ?? "",
    );

  const confirmPassword =
    String(
      form.get("confirm_password") ?? "",
    );

  const next =
    safeNext(
      form.get("next"),
    );

  if (
    !fullName ||
    !email ||
    !phone ||
    !password
  ) {
    return NextResponse.redirect(
      signupUrl(
        request,
        next,
        "All fields are required.",
      ),
      303,
    );
  }

  if (
    password !==
    confirmPassword
  ) {
    return NextResponse.redirect(
      signupUrl(
        request,
        next,
        "Passwords do not match.",
      ),
      303,
    );
  }

  if (
    password.length < 8
  ) {
    return NextResponse.redirect(
      signupUrl(
        request,
        next,
        "Password must be at least 8 characters.",
      ),
      303,
    );
  }

  try {
    const signup =
      await fetch(
        `${BACKEND}/api/v1/auth/signup`,
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json",
          },

          body:
            JSON.stringify({
              full_name:
                fullName,
              email,
              phone,
              password,
            }),

          cache: "no-store",
        },
      );

    if (!signup.ok) {
      const raw =
        await signup.text();

      let message =
        "Could not create account.";

      try {
        const data =
          JSON.parse(raw);

        if (
          typeof data.detail ===
          "string"
        ) {
          message =
            data.detail;
        }
      } catch {}

      return NextResponse.redirect(
        signupUrl(
          request,
          next,
          message,
        ),
        303,
      );
    }

    const login =
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

    if (!login.ok) {
      const url =
        new URL(
          "/login",
          request.url,
        );

      url.searchParams.set(
        "next",
        next,
      );

      return NextResponse.redirect(
        url,
        303,
      );
    }

    const data =
      await login.json();

    const token =
      data.access_token ??
      data.token ??
      data.session_token ??
      data.accessToken;

    if (!token) {
      const url =
        new URL(
          "/login",
          request.url,
        );

      url.searchParams.set(
        "next",
        next,
      );

      return NextResponse.redirect(
        url,
        303,
      );
    }

    const result =
      NextResponse.redirect(
        new URL(
          next,
          process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000",
        ),
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
      signupUrl(
        request,
        next,
        "MediBook is temporarily unavailable.",
      ),
      303,
    );
  }
}
