import {
  NextRequest,
  NextResponse,
} from "next/server";


const SESSION_COOKIE =
  "medibook_session";


const PROTECTED = [
  "/assistant",
  "/appointments",
  "/profile",
];


export function proxy(
  request: NextRequest,
) {

  const pathname =
    request.nextUrl.pathname;


  const protectedRoute =
    PROTECTED.some(
      route =>
        pathname === route ||
        pathname.startsWith(
          `${route}/`
        ),
    );


  if (!protectedRoute) {

    return NextResponse.next();
  }


  const session =
    request.cookies.get(
      SESSION_COOKIE,
    )?.value;


  if (session) {

    return NextResponse.next();
  }


  const login =
    new URL(
      "/login",
      request.url,
    );

  login.searchParams.set(
    "next",
    pathname,
  );


  return NextResponse.redirect(
    login,
  );
}


export const config = {
  matcher: [
    "/assistant/:path*",
    "/appointments/:path*",
    "/profile/:path*",
  ],
};
