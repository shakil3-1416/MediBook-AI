async function platformSummary() {
  const base =
    process.env.NEXT_PUBLIC_APP_URL
    ??
    "http://localhost:3000";

  try {
    const response =
      await fetch(
        `${base}/api/dashboard/platform-summary`,
        {
          cache:
            "no-store",
        },
      );

    if (!response.ok) {
      return null;
    }

    return response.json();

  } catch {
    return null;
  }
}


export default async function ControlDashboard() {
  const data =
    await platformSummary();

  return (
    <main className="min-h-screen bg-slate-50 p-6 md:p-10">

      <div className="mx-auto max-w-7xl">

        <p className="text-sm font-semibold text-slate-500">
          MediBook SaaS
        </p>


        <h1 className="mt-2 text-3xl font-semibold">
          Platform control
        </h1>


        <div className="mt-8 grid gap-4 md:grid-cols-3">

          <Metric
            label="Hospital tenants"
            value={
              data
                ?.total_hospitals
              ?? 0
            }
          />

          <Metric
            label="Doctors connected"
            value={
              data
                ?.total_doctors
              ?? 0
            }
          />

          <Metric
            label="Platform status"
            value="Operational"
          />

        </div>


        <div className="mt-8 overflow-hidden rounded-2xl border border-slate-200 bg-white">

          <div className="border-b border-slate-200 px-6 py-4">

            <h2 className="font-semibold">
              Hospitals
            </h2>

          </div>


          <div className="divide-y divide-slate-100">

            {
              data
                ?.hospitals
                ?.map(
                  (
                    hospital:
                      {
                        id:
                          string;

                        name:
                          string;

                        slug:
                          string;

                        status:
                          string;

                        doctor_count:
                          number;
                      },
                  ) => (

                  <div
                    key={
                      hospital.id
                    }
                    className="grid gap-2 px-6 py-5 md:grid-cols-4"
                  >

                    <div className="font-medium">
                      {
                        hospital.name
                      }
                    </div>

                    <div className="text-sm text-slate-500">
                      {
                        hospital.slug
                      }
                    </div>

                    <div className="text-sm">
                      {
                        hospital
                          .doctor_count
                      }{" "}
                      doctors
                    </div>

                    <div className="text-sm capitalize">
                      {
                        hospital.status
                      }
                    </div>

                  </div>

                ),
              )
            }

          </div>

        </div>

      </div>

    </main>
  );
}


function Metric({
  label,
  value,
}: {
  label: string;
  value:
    string | number;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6">

      <div className="text-sm text-slate-500">
        {label}
      </div>

      <div className="mt-2 text-2xl font-semibold">
        {value}
      </div>

    </div>
  );
}
