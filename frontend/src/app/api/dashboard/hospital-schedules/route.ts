import {
  NextRequest,
  NextResponse,
} from "next/server";

import {
  cookies,
} from "next/headers";


const BACKEND =
  process.env.BACKEND_URL ??
  "http://127.0.0.1:8000";


async function token() {
  const store =
    await cookies();

  return store.get(
    "medibook_hospital_session",
  )?.value;
}


function base(
  hospital: string,
  doctorId: string,
) {
  return (
    `${BACKEND}/api/v1/hospital-operations/`
    + `${encodeURIComponent(hospital)}`
    + `/doctors/${encodeURIComponent(doctorId)}`
    + "/schedule"
  );
}


async function relay(
  url: string,
  accessToken: string,
  method: string,
  payload?: unknown,
) {
  const response =
    await fetch(
      url,
      {
        method,
        headers: {
          Authorization:
            `Bearer ${accessToken}`,
          ...(payload === undefined
            ? {}
            : {
                "Content-Type":
                  "application/json",
              }),
        },
        body:
          payload === undefined
            ? undefined
            : JSON.stringify(
                payload,
              ),
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
          ) ??
          "application/json",
      },
    },
  );
}


export async function GET(
  request: NextRequest,
) {
  const hospital =
    request.nextUrl.searchParams
      .get("hospital")
      ?.trim();

  const doctorId =
    request.nextUrl.searchParams
      .get("doctor_id")
      ?.trim();

  const accessToken =
    await token();

  if (!accessToken) {
    return NextResponse.json(
      {
        detail:
          "Hospital authentication required.",
      },
      {
        status: 401,
      },
    );
  }

  if (!hospital || !doctorId) {
    return NextResponse.json(
      {
        detail:
          "Hospital and doctor_id are required.",
      },
      {
        status: 422,
      },
    );
  }

  return relay(
    base(
      hospital,
      doctorId,
    ),
    accessToken,
    "GET",
  );
}


export async function POST(
  request: NextRequest,
) {
  const body =
    await request.json() as {
      hospital?: string;
      doctor_id?: string;
      action?: string;
      payload?: unknown;
    };

  const hospital =
    String(
      body.hospital ?? "",
    ).trim();

  const doctorId =
    String(
      body.doctor_id ?? "",
    ).trim();

  const action =
    String(
      body.action ?? "",
    ).trim();

  const accessToken =
    await token();

  if (!accessToken) {
    return NextResponse.json(
      {
        detail:
          "Hospital authentication required.",
      },
      {
        status: 401,
      },
    );
  }

  const suffix: Record<
    string,
    string
  > = {
    rule:
      "/rules",
    exception:
      "/exceptions",
    preview:
      "/preview",
    apply:
      "/apply",
  };

  if (
    !hospital ||
    !doctorId ||
    !suffix[action]
  ) {
    return NextResponse.json(
      {
        detail:
          "Invalid schedule request.",
      },
      {
        status: 422,
      },
    );
  }

  return relay(
    base(
      hospital,
      doctorId,
    ) + suffix[action],
    accessToken,
    "POST",
    body.payload ?? {},
  );
}


export async function PATCH(
  request: NextRequest,
) {
  const body =
    await request.json() as {
      hospital?: string;
      doctor_id?: string;
      resource?: string;
      id?: string;
      payload?: unknown;
    };

  const hospital =
    String(
      body.hospital ?? "",
    ).trim();

  const doctorId =
    String(
      body.doctor_id ?? "",
    ).trim();

  const resource =
    String(
      body.resource ?? "",
    ).trim();

  const id =
    String(
      body.id ?? "",
    ).trim();

  const accessToken =
    await token();

  if (!accessToken) {
    return NextResponse.json(
      {
        detail:
          "Hospital authentication required.",
      },
      {
        status: 401,
      },
    );
  }

  const segment =
    resource === "rule"
      ? "rules"
      : resource === "exception"
      ? "exceptions"
      : null;

  if (
    !hospital ||
    !doctorId ||
    !segment ||
    !id
  ) {
    return NextResponse.json(
      {
        detail:
          "Invalid schedule update.",
      },
      {
        status: 422,
      },
    );
  }

  return relay(
    base(
      hospital,
      doctorId,
    )
      + `/${segment}/`
      + encodeURIComponent(id),
    accessToken,
    "PATCH",
    body.payload ?? {},
  );
}
