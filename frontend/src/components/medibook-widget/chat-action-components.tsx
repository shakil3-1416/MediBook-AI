"use client";


export type ChatActionLike = {
  id: string;

  type:
    | "send_message"
    | "book_slot"
    | "confirm"
    | "cancel"
    | "reschedule";

  label: string;

  message: string;

  variant:
    | "primary"
    | "secondary"
    | "danger";

  payload?: {
    component?:
      | "doctor_card"
      | "availability_slot"
      | "appointment_preview";

    doctor_name?: string;
    specialty?: string;
    qualification?: string;

    experience_years?:
      | number
      | string
      | null;

    clinic_name?: string;
    clinic_location?: string;

    professional_interests?:
      | string
      | string[]
      | null;

    profile_image_url?: string;

    date?: string;
    start_time?: string;

    consultation_fee?:
      | number
      | string
      | null;
  } | null;
};


function DoctorCard({
  action,
}: {
  action: ChatActionLike;
}) {
  const data =
    action.payload;

  if (
    !data
    ||
    data.component
      !==
      "doctor_card"
    ||
    !data.doctor_name
  ) {
    return null;
  }

  const interests =
    Array.isArray(
      data.professional_interests,
    )
      ? data.professional_interests.join(
          " • ",
        )
      : data.professional_interests;

  return (
    <article className="medibook-message mt-3 overflow-hidden rounded-2xl border border-purple-100 bg-white shadow-sm">
      <div className="flex gap-4 p-4">
        <div className="flex h-14 w-14 shrink-0 items-center justify-center overflow-hidden rounded-2xl bg-purple-100 font-semibold text-purple-700">
          {data.profile_image_url ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={
                data.profile_image_url
              }
              alt=""
              className="h-full w-full object-cover"
            />
          ) : (
            data.doctor_name
              .replace(
                /^dr\.?\s*/i,
                "",
              )
              .charAt(0)
              .toUpperCase()
          )}
        </div>

        <div className="min-w-0 flex-1">
          <h3 className="text-[15px] font-semibold text-slate-950">
            {data.doctor_name}
          </h3>

          {data.specialty ? (
            <p className="mt-0.5 text-sm font-medium text-purple-700">
              {data.specialty}
            </p>
          ) : null}

          <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500">
            {data.qualification ? (
              <span>
                {data.qualification}
              </span>
            ) : null}

            {data.experience_years ? (
              <span>
                {data.experience_years} years experience
              </span>
            ) : null}
          </div>

          {data.clinic_name ||
          data.clinic_location ? (
            <p className="mt-3 text-sm text-slate-600">
              {data.clinic_name}

              {data.clinic_name &&
              data.clinic_location
                ? " · "
                : ""}

              {data.clinic_location}
            </p>
          ) : null}

          {interests ? (
            <p className="mt-2 text-xs leading-5 text-slate-500">
              {interests}
            </p>
          ) : null}
        </div>
      </div>
    </article>
  );
}


function AvailabilityGroup({
  actions,
}: {
  actions: ChatActionLike[];
}) {
  const slots =
    actions.filter(
      (action) =>
        action.payload?.component
          ===
        "availability_slot",
    );

  if (!slots.length) {
    return null;
  }

  const first =
    slots[0]?.payload;

  return (
    <section className="medibook-message mt-3 rounded-2xl border border-purple-100 bg-purple-50/50 p-4">
      <div className="text-xs font-semibold uppercase tracking-[0.12em] text-purple-600">
        Availability
      </div>

      {first?.doctor_name ? (
        <p className="mt-1 text-sm font-medium text-slate-800">
          {first.doctor_name}
        </p>
      ) : null}

      {first?.date ? (
        <p className="mt-1 text-xs text-slate-500">
          {first.date}
        </p>
      ) : null}

      <div className="mt-3 flex flex-wrap gap-2">
        {slots.map(
          (action) => {
            const time =
              action.payload
                ?.start_time;

            if (!time) {
              return null;
            }

            return (
              <span
                key={action.id}
                className="rounded-xl border border-purple-100 bg-white px-3 py-2 text-sm font-medium text-slate-700 shadow-sm"
              >
                {time}
              </span>
            );
          },
        )}
      </div>

      <p className="mt-3 text-xs text-slate-500">
        Tell MediBook which time you prefer.
      </p>
    </section>
  );
}


function AppointmentPreview({
  action,
}: {
  action: ChatActionLike;
}) {
  const data =
    action.payload;

  if (
    !data
    ||
    data.component
      !==
      "appointment_preview"
  ) {
    return null;
  }

  return (
    <section className="medibook-message mt-3 overflow-hidden rounded-2xl border border-purple-200 bg-white shadow-sm">
      <div className="border-b border-purple-100 bg-purple-50 px-4 py-3">
        <p className="text-xs font-semibold uppercase tracking-[0.12em] text-purple-600">
          Appointment preview
        </p>
      </div>

      <div className="p-4">
        {data.doctor_name ? (
          <h3 className="font-semibold text-slate-950">
            {data.doctor_name}
          </h3>
        ) : null}

        {data.specialty ? (
          <p className="mt-1 text-sm text-purple-700">
            {data.specialty}
          </p>
        ) : null}

        <dl className="mt-4 grid grid-cols-2 gap-4 text-sm">
          {data.date ? (
            <div>
              <dt className="text-xs text-slate-500">
                Date
              </dt>

              <dd className="mt-1 font-medium text-slate-700">
                {data.date}
              </dd>
            </div>
          ) : null}

          {data.start_time ? (
            <div>
              <dt className="text-xs text-slate-500">
                Time
              </dt>

              <dd className="mt-1 font-medium text-slate-700">
                {data.start_time}
              </dd>
            </div>
          ) : null}

          {data.clinic_name ? (
            <div className="col-span-2">
              <dt className="text-xs text-slate-500">
                Hospital / chamber
              </dt>

              <dd className="mt-1 font-medium text-slate-700">
                {data.clinic_name}
              </dd>
            </div>
          ) : null}

          {data.consultation_fee != null ? (
            <div>
              <dt className="text-xs text-slate-500">
                Consultation fee
              </dt>

              <dd className="mt-1 font-medium text-slate-700">
                Tk{" "}
                {String(
                  data.consultation_fee,
                )}
              </dd>
            </div>
          ) : null}
        </dl>

        <p className="mt-4 border-t border-slate-100 pt-3 text-xs leading-5 text-slate-500">
          Confirm or change this appointment by typing your response.
        </p>
      </div>
    </section>
  );
}


export default function ChatActionComponents({
  actions,
}: {
  actions?:
    | ChatActionLike[]
    | null;
}) {
  if (!actions?.length) {
    return null;
  }

  const doctorActions =
    actions.filter(
      (action) =>
        action.payload?.component
          ===
        "doctor_card",
    );

  const previewActions =
    actions.filter(
      (action) =>
        action.payload?.component
          ===
        "appointment_preview",
    );

  return (
    <div className="mt-2 space-y-3">
      {doctorActions.map(
        (action) => (
          <DoctorCard
            key={action.id}
            action={action}
          />
        ),
      )}

      <AvailabilityGroup
        actions={actions}
      />

      {previewActions.map(
        (action) => (
          <AppointmentPreview
            key={action.id}
            action={action}
          />
        ),
      )}
    </div>
  );
}
