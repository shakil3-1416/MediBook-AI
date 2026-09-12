import {
  NextResponse,
} from "next/server";

const BACKEND =
  process.env.BACKEND_URL ??
  "http://127.0.0.1:8000";

export async function POST(
  request: Request,
  context: {
    params: Promise<{
      hospitalSlug: string;
      conversationId: string;
    }>;
  },
) {
  const {
    conversationId,
  } = await context.params;

  const body =
    await request.json();

  const response =
    await fetch(
      `${BACKEND}/api/v1/widget-conversations/${conversationId}/messages`,
      {
        method: "POST",
        headers: {
          "Content-Type":
            "application/json",
        },
        body:
          JSON.stringify(body),
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
