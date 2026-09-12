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
      conversationId: string;
    }>;
  },
) {
  const {
    hospitalSlug,
    conversationId,
  } = await context.params;

  const url =
    new URL(request.url);

  const visitorId =
    url.searchParams.get(
      "visitor_id",
    );

  const response =
    await fetch(
      `${BACKEND}/api/v1/widget-conversations/${hospitalSlug}/${conversationId}?visitor_id=${encodeURIComponent(
        visitorId ?? "",
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
