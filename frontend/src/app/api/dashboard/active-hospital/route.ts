import {
  NextResponse,
} from "next/server";

import {
  cookies,
} from "next/headers";


const ACTIVE_HOSPITAL_COOKIE =
  "medibook_active_hospital";


export async function GET() {
  const slug =
    (
      await cookies()
    ).get(
      ACTIVE_HOSPITAL_COOKIE,
    )?.value;

  if (!slug) {
    return NextResponse.json(
      {
        hospital: null,
      },
    );
  }

  return NextResponse.json(
    {
      hospital: slug,
    },
  );
}
