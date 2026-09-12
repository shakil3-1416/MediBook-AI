import {
  NextResponse,
} from "next/server";

import {
  cookies,
} from "next/headers";


const BACKEND =
  process.env.BACKEND_URL ??
  "http://127.0.0.1:8000";


export async function GET() {
  const store =
    await cookies();


  const token =
    store.get(
      "medibook_hospital_session",
    )?.value;


  if (!token) {
    return NextResponse.json(
      {
        authenticated:
          false,
      },
      {
        status: 401,
      },
    );
  }


  const response =
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


  if (!response.ok) {
    return NextResponse.json(
      {
        authenticated:
          false,
      },
      {
        status:
          response.status,
      },
    );
  }


  const user =
    await response.json();


  return NextResponse.json(
    {
      authenticated:
        true,

      user,
    },
  );
}
