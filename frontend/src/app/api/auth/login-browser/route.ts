import { NextRequest, NextResponse } from "next/server";

const BACKEND =
  process.env.BACKEND_URL ??
  "http://127.0.0.1:8000";

const DEFAULT_NEXT = "/widget/medibook-demo";

function safeNext(value: FormDataEntryValue | null) {
  if (
    typeof value === "string" &&
    value.startsWith("/") &&
    !value.startsWith("//")
  ) {
    return value;
  }

  return DEFAULT_NEXT;
}

/*
 * Relative redirects keep people on the host and port they actually used.
 * The previous absolute URLs were built from NEXT_PUBLIC_APP_URL and fell
 * back to http://localhost:3000.
 */
function redirectTo(location: string) {
  return new NextResponse(null, {
    status: 303,
    headers: { Location: location },
  });
}

function backToLogin(next: string, message: string) {
  const params = new URLSearchParams({ next, error: message });
  return redirectTo(`/login?${params.toString()}`);
}

/* Platform admins belong in the control center unless they asked for a staff page. */
function landingFor(role: string | undefined, next: string) {
  if (
    role === "platform_admin" &&
    next.startsWith("/control") === false &&
    next.startsWith("/hospital-dashboard") === false
  ) {
    return "/control";
  }
  return next;
}

export async function POST(request: NextRequest) {
  const form = await request.formData();
  const email = String(form.get("email") ?? "").trim();
  const password = String(form.get("password") ?? "");
  const next = safeNext(form.get("next"));

  if (!email || !password) {
    return backToLogin(next, "Email and password are required.");
  }

  try {
    const response = await fetch(`${BACKEND}/api/v1/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
      cache: "no-store",
    });

    const raw = await response.text();

    let data: {
      detail?: unknown;
      access_token?: string;
      token?: string;
      session_token?: string;
      accessToken?: string;
      user?: { role?: string };
    } = {};

    try {
      data = JSON.parse(raw);
    } catch {
      data = { detail: raw };
    }

    if (!response.ok) {
      return backToLogin(
        next,
        typeof data.detail === "string" ? data.detail : "Invalid email or password.",
      );
    }

    const token =
      data.access_token ?? data.token ?? data.session_token ?? data.accessToken;

    if (!token) {
      return backToLogin(next, "MediBook could not create your session.");
    }

    const result = redirectTo(landingFor(data.user?.role, next));

    result.cookies.set("medibook_session", token, {
      httpOnly: true,
      sameSite: "lax",
      secure: process.env.NODE_ENV === "production",
      path: "/",
      maxAge: 60 * 60 * 24 * 7,
    });

    return result;
  } catch {
    return backToLogin(next, "Authentication service is unavailable.");
  }
}
