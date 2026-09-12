import {
  NextResponse,
} from "next/server";

import {
  cookies,
} from "next/headers";


export async function POST() {
  const cookieStore =
    await cookies();


  cookieStore.set(
    "medibook_hospital_session",
    "",
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
        0,
    },
  );


  return NextResponse.json(
    {
      logged_out:
        true,
    },
  );
}
