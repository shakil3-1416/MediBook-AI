import {
  NextRequest,
  NextResponse,
} from "next/server";


const BACKEND =
  process.env.BACKEND_URL ??
  "http://127.0.0.1:8000";


export async function POST(
  request: NextRequest,
) {
  const response =
    await fetch(
      `${BACKEND}/api/v1/auth/signup/start`,
      {
        method:
          "POST",

        headers: {
          "Content-Type":
            "application/json",
        },

        body:
          await request.text(),

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
          )
          ??
          "application/json",
      },
    },
  );
}
