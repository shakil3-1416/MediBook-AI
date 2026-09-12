import { NextResponse } from "next/server";

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
  const { hospitalSlug } =
    await context.params;

  const url =
    new URL(request.url);

  const query =
    url.searchParams.toString();

  const response =
    await fetch(
      `${BACKEND}/api/v1/hospital-public/${hospitalSlug}/doctors${
        query ? `?${query}` : ""
      }`,
      { cache: "no-store" },
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
