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


function normalizeTime(
  value: unknown,
): string {
  return String(
    value ?? "",
  )
    .trim()
    .slice(0, 5);
}


export async function POST(
  request: NextRequest,
  context: {
    params:
      Promise<{
        hospitalSlug:
          string;
      }>;
  },
) {
  const {
    hospitalSlug,
  } =
    await context.params;


  const store =
    await cookies();


  const token =
    store.get(
      "medibook_session",
    )?.value;


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


  let body: {
    confirmation_code?: string | null;
    new_slot_id?: string | null;
    slot_date?: string | null;
    start_time?: string | null;
  };

  try {
    body =
      await request.json();
  } catch {
    return NextResponse.json(
      {
        detail:
          "Invalid JSON body.",
      },
      {
        status: 400,
      },
    );
  }


  const confirmationCode =
    String(
      body.confirmation_code ??
      "",
    ).trim();


  if (!confirmationCode) {
    return NextResponse.json(
      {
        detail:
          "confirmation_code is required.",
      },
      {
        status: 422,
      },
    );
  }


  // --------------------------------------------------
  // If caller already knows the exact slot ID,
  // forward it directly.
  // --------------------------------------------------

  let newSlotId =
    body.new_slot_id
      ? String(
          body.new_slot_id,
        )
      : null;


  // --------------------------------------------------
  // Browser UI currently supplies date/time.
  // Resolve them deterministically to a real slot ID.
  // --------------------------------------------------

  if (!newSlotId) {
    const slotDate =
      String(
        body.slot_date ??
        "",
      ).trim();

    const startTime =
      normalizeTime(
        body.start_time,
      );


    if (
      !slotDate ||
      !startTime
    ) {
      return NextResponse.json(
        {
          detail:
            "Provide new_slot_id or slot_date + start_time.",
        },
        {
          status: 422,
        },
      );
    }


    // 1. Load this patient's appointments.
    const appointmentsResponse =
      await fetch(
        `${BACKEND}/api/v1/appointments`,
        {
          headers: {
            Authorization:
              `Bearer ${token}`,
          },

          cache:
            "no-store",
        },
      );


    if (!appointmentsResponse.ok) {
      const detail =
        await appointmentsResponse.text();

      return new NextResponse(
        detail,
        {
          status:
            appointmentsResponse.status,
        },
      );
    }


    const appointmentsRaw =
      await appointmentsResponse.json();


    const appointments =
      Array.isArray(
        appointmentsRaw,
      )
        ? appointmentsRaw
        : appointmentsRaw.appointments ??
          appointmentsRaw.items ??
          [];


    const appointment =
      appointments.find(
        (
          item: {
            confirmation_code?: string | null;
            doctor_id?: string | null;
            doctor?: {
              id?: string | null;
            } | null;
          },
        ) =>
          String(
            item.confirmation_code ??
            "",
          ) ===
          confirmationCode,
      );


    if (!appointment) {
      return NextResponse.json(
        {
          detail:
            "Appointment not found.",
        },
        {
          status: 404,
        },
      );
    }


    const doctorId =
      appointment.doctor?.id ??
      appointment.doctor_id;


    if (!doctorId) {
      return NextResponse.json(
        {
          detail:
            "Appointment doctor identity is missing.",
        },
        {
          status: 409,
        },
      );
    }


    // 2. Load real available slots for THIS doctor
    //    inside THIS hospital tenant.
    const slotsResponse =
      await fetch(
        `${BACKEND}/api/v1/hospital-public/${encodeURIComponent(
          hospitalSlug,
        )}/doctors/${encodeURIComponent(
          String(
            doctorId,
          ),
        )}/slots`,
        {
          cache:
            "no-store",
        },
      );


    if (!slotsResponse.ok) {
      const detail =
        await slotsResponse.text();

      return new NextResponse(
        detail,
        {
          status:
            slotsResponse.status,
        },
      );
    }


    const slotsRaw =
      await slotsResponse.json();


    const slots =
      Array.isArray(
        slotsRaw,
      )
        ? slotsRaw
        : slotsRaw.available_slots ??
          slotsRaw.slots ??
          slotsRaw.items ??
          [];


    const matchingSlot =
      slots.find(
        (
          slot: {
            id?: string | null;
            slot_id?: string | null;
            slot_date?: string | null;
            date?: string | null;
            start_time?: string | null;
            time?: string | null;
            is_available?: boolean | null;
          },
        ) => {
          const date =
            String(
              slot.slot_date ??
              slot.date ??
              "",
            );

          const time =
            normalizeTime(
              slot.start_time ??
              slot.time,
            );

          const available =
            slot.is_available !==
            false;

          return (
            available &&
            date ===
              slotDate &&
            time ===
              startTime
          );
        },
      );


    if (!matchingSlot) {
      return NextResponse.json(
        {
          detail:
            "The requested appointment time is no longer available.",
        },
        {
          status: 409,
        },
      );
    }


    newSlotId =
      String(
        matchingSlot.id ??
        matchingSlot.slot_id ??
        "",
      );


    if (!newSlotId) {
      return NextResponse.json(
        {
          detail:
            "Matched slot has no slot ID.",
        },
        {
          status: 409,
        },
      );
    }
  }


  // --------------------------------------------------
  // 3. Forward the ACTUAL backend contract.
  // --------------------------------------------------

  const response =
    await fetch(
      `${BACKEND}/api/v1/appointments/reschedule`,
      {
        method:
          "POST",

        headers: {
          Authorization:
            `Bearer ${token}`,

          "Content-Type":
            "application/json",
        },

        body:
          JSON.stringify({
            confirmation_code:
              confirmationCode,

            new_slot_id:
              newSlotId,
          }),

        cache:
          "no-store",
      },
    );


  const raw =
    await response.text();


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
