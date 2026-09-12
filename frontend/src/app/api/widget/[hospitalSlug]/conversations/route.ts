import {
  NextResponse,
} from "next/server";

const BACKEND =
  process.env.BACKEND_URL ??
  "http://127.0.0.1:8000";

export async function GET(
  request: Request,
  context: {
    params: Promise<{
      hospitalSlug: string;
    }>;
  },
) {
  const {
    hospitalSlug,
  } = await context.params;

  const url =
    new URL(request.url);

  const visitorId =
    url.searchParams.get(
      "visitor_id",
    );

  if (!visitorId) {
    return NextResponse.json(
      {
        detail:
          "visitor_id required",
      },
      {
        status: 400,
      },
    );
  }

  const response =
    await fetch(
      `${BACKEND}/api/v1/widget-conversations/${hospitalSlug}?visitor_id=${encodeURIComponent(
        visitorId,
      )}`,
      {
        cache: "no-store",
      },
    );

  return new NextResponse(
    await response.text(),
    {
      status: response.status,
      headers: {
        "Content-Type":
          "application/json",
      },
    },
  );
}


export async function POST(
  request: Request,
  context: {
    params: Promise<{
      hospitalSlug: string;
    }>;
  },
) {
  const {
    hospitalSlug,
  } = await context.params;

  const body =
    await request.json();

  const response =
    await fetch(
      `${BACKEND}/api/v1/widget-conversations`,
      {
        method: "POST",
        headers: {
          "Content-Type":
            "application/json",
        },
        body: JSON.stringify({
          hospital_slug:
            hospitalSlug,
          visitor_id:
            body.visitor_id,
        }),
      },
    );

  return new NextResponse(
    await response.text(),
    {
      status: response.status,
      headers: {
        "Content-Type":
          "application/json",
      },
    },
  );
}
