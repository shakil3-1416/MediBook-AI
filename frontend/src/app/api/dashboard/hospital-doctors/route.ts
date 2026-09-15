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


export async function GET(
  request: NextRequest,
) {
  const hospital =
    request.nextUrl.searchParams
      .get("hospital")
      ?.trim();

  if (!hospital) {
    return NextResponse.json(
      {
        detail:
          "Hospital is required.",
      },
      {
        status: 422,
      },
    );
  }

  const cookieStore =
    await cookies();

  const token =
    cookieStore.get(
      "medibook_hospital_session",
    )?.value;

  if (!token) {
    return NextResponse.json(
      {
        detail:
          "Hospital authentication required.",
      },
      {
        status: 401,
      },
    );
  }

  const response =
    await fetch(
      `${BACKEND}/api/v1/hospital-operations/${encodeURIComponent(hospital)}/doctors`,
      {
        headers: {
          Authorization:
            `Bearer ${token}`,
        },
        cache:
          "no-store",
      },
    );

  return new NextResponse(
    await response.text(),
    {
      status:
        response.status,
      headers: {
        "Content-Type":
          response.headers.get(
            "content-type",
          ) ??
          "application/json",
      },
    },
  );
}
