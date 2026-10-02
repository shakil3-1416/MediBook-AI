import { NextRequest, NextResponse } from "next/server";

const PATIENT_SESSION = "medibook_session";
const STAFF_SESSION = "medibook_hospital_session";
const PATIENT_HOSPITAL = "medibook_patient_hospital";

const PATIENT_PAGES = ["/assistant", "/appointments", "/profile"];

function under(pathname: string, prefix: string) {
  return pathname === prefix || pathname.startsWith(`${prefix}/`);
}

function signIn(request: NextRequest, page: string) {
  const url = new URL(page, request.url);
  url.searchParams.set("next", request.nextUrl.pathname);
  return NextResponse.redirect(url);
}

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const patient = request.cookies.get(PATIENT_SESSION)?.value;
  const staff = request.cookies.get(STAFF_SESSION)?.value;

  // Remember which hospital's assistant a patient opened, so pages outside
  // the assistant, such as My appointments, stay in that hospital.
  const assistant = pathname.match(/^\/(?:widget|embed)\/([a-z0-9-]{1,80})(?:\/|$)/i);
  if (assistant) {
    const response = NextResponse.next();
    response.cookies.set(PATIENT_HOSPITAL, assistant[1].toLowerCase(), {
      httpOnly: true,
      sameSite: "lax",
      secure: process.env.NODE_ENV === "production",
      path: "/",
      maxAge: 60 * 60 * 24 * 30,
    });
    return response;
  }

  if (PATIENT_PAGES.some((page) => under(pathname, page)) && patient === undefined) {
    return signIn(request, "/login");
  }

  if (under(pathname, "/hospital-dashboard") && staff === undefined) {
    return signIn(request, "/hospital-login");
  }

  if (under(pathname, "/control") && staff === undefined && patient === undefined) {
    return signIn(request, "/login");
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/assistant/:path*",
    "/appointments/:path*",
    "/profile/:path*",
    "/hospital-dashboard/:path*",
    "/control/:path*",
    "/widget/:path*",
    "/embed/:path*",
  ],
};
