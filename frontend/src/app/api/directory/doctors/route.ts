import {
  NextRequest,
  NextResponse,
} from "next/server";


const API =
  process.env.MEDIBOOK_INTERNAL_API_URL ??
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://127.0.0.1:8000/api/v1";


export async function GET(
  request: NextRequest,
) {
  try {
    const query =
      request.nextUrl.searchParams.toString();

    const url =
      `${API}/doctors` +
      (query ? `?${query}` : "");

    const response =
      await fetch(
        url,
        {
          cache: "no-store",
        },
      );

    const body =
      await response.text();

    return new NextResponse(
      body,
      {
        status: response.status,
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
        count: 0,
        page: 1,
        page_size: 18,
        pages: 0,
        doctors: [],
      },
      {
        status: 503,
      },
    );
  }
}
