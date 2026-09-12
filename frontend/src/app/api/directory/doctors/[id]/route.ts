import {
  NextResponse,
} from "next/server";


const API =
  process.env.MEDIBOOK_INTERNAL_API_URL ??
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://127.0.0.1:8000/api/v1";


export async function GET(
  _request: Request,
  context: {
    params:
      Promise<{
        id: string;
      }>;
  },
) {

  const {
    id,
  } =
    await context.params;


  try {

    const response =
      await fetch(
        `${API}/doctors/${id}`,
        {
          cache:
            "no-store",
        },
      );


    const body =
      await response.text();


    return new NextResponse(
      body,
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

  } catch {

    return NextResponse.json(
      {
        detail:
          "Doctor profile unavailable.",
      },
      {
        status: 503,
      },
    );
  }
}
