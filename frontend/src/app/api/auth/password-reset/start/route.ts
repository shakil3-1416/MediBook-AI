import {
  backendBaseUrl,
} from "@/lib/patient-server-auth";


export async function POST(
  request: Request,
) {

  const response =
    await fetch(
      `${backendBaseUrl()}/api/v1/identity/password/reset/start`,
      {
        method: "POST",

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

  return new Response(
    await response.text(),
    {
      status:
        response.status,

      headers: {
        "Content-Type":
          "application/json",
      },
    },
  );
}
