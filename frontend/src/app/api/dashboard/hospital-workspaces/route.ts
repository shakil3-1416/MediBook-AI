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

const ACTIVE_HOSPITAL_COOKIE =
  "medibook_active_hospital";


type Workspace = {
  id: string;
  slug: string;
  name: string;
  status: string;
  timezone: string;
  role: string;
};


async function getHospitalToken() {
  return (
    await cookies()
  ).get(
    "medibook_hospital_session",
  )?.value;
}


async function loadWorkspaces(
  token: string,
) {
  const response =
    await fetch(
      `${BACKEND}/api/v1/hospital/workspaces`,
      {
        headers: {
          Authorization:
            `Bearer ${token}`,
        },
        cache:
          "no-store",
      },
    );

  const raw =
    await response.text();

  return {
    response,
    raw,
  };
}


export async function GET() {
  const token =
    await getHospitalToken();

  if (!token) {
    return NextResponse.json(
      {
        detail:
          "Authentication required.",
      },
      {
        status: 401,
      },
    );
  }

  const {
    response,
    raw,
  } =
    await loadWorkspaces(
      token,
    );

  if (!response.ok) {
    return new NextResponse(
      raw,
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

  let workspaces: Workspace[];

  try {
    workspaces =
      JSON.parse(
        raw,
      ) as Workspace[];
  } catch {
    return NextResponse.json(
      {
        detail:
          "Invalid workspace response.",
      },
      {
        status: 502,
      },
    );
  }

  const cookieStore =
    await cookies();

  const storedSlug =
    cookieStore.get(
      ACTIVE_HOSPITAL_COOKIE,
    )?.value;

  let active =
    storedSlug
      ? workspaces.find(
          (workspace) =>
            workspace.slug ===
            storedSlug,
        )
      : undefined;

  if (!active) {
    active =
      workspaces[0];
  }

  const result =
    NextResponse.json(
      {
        workspaces,
        active:
          active ?? null,
      },
    );

  if (active) {
    result.cookies.set(
      ACTIVE_HOSPITAL_COOKIE,
      active.slug,
      {
        httpOnly: true,
        sameSite: "lax",
        secure:
          process.env.NODE_ENV ===
          "production",
        path: "/",
        maxAge:
          60 * 60 * 24 * 30,
      },
    );
  } else {
    result.cookies.delete(
      ACTIVE_HOSPITAL_COOKIE,
    );
  }

  return result;
}


export async function POST(
  request: NextRequest,
) {
  const token =
    await getHospitalToken();

  if (!token) {
    return NextResponse.json(
      {
        detail:
          "Authentication required.",
      },
      {
        status: 401,
      },
    );
  }

  let payload:
    | {
        hospital?: string;
      }
    | null =
    null;

  try {
    payload =
      await request.json();
  } catch {
    return NextResponse.json(
      {
        detail:
          "Invalid request body.",
      },
      {
        status: 400,
      },
    );
  }

  const requestedSlug =
    payload?.hospital?.trim();

  if (!requestedSlug) {
    return NextResponse.json(
      {
        detail:
          "Hospital is required.",
      },
      {
        status: 422,
      },
    );
  }

  const {
    response,
    raw,
  } =
    await loadWorkspaces(
      token,
    );

  if (!response.ok) {
    return new NextResponse(
      raw,
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

  let workspaces: Workspace[];

  try {
    workspaces =
      JSON.parse(
        raw,
      ) as Workspace[];
  } catch {
    return NextResponse.json(
      {
        detail:
          "Invalid workspace response.",
      },
      {
        status: 502,
      },
    );
  }

  const selected =
    workspaces.find(
      (workspace) =>
        workspace.slug ===
        requestedSlug,
    );

  if (!selected) {
    return NextResponse.json(
      {
        detail:
          "Hospital workspace is not available to this account.",
      },
      {
        status: 403,
      },
    );
  }

  const result =
    NextResponse.json(
      {
        active:
          selected,
      },
    );

  result.cookies.set(
    ACTIVE_HOSPITAL_COOKIE,
    selected.slug,
    {
      httpOnly: true,
      sameSite: "lax",
      secure:
        process.env.NODE_ENV ===
        "production",
      path: "/",
      maxAge:
        60 * 60 * 24 * 30,
    },
  );

  return result;
}
