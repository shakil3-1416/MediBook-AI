import Link from "next/link";

function ChatIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      className="h-5 w-5"
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M7 8h10M7 12h6m-9 8 3.5-3.5A8.5 8.5 0 1 1 20.5 13 8.5 8.5 0 0 1 12 17.5H8.5L4 20Z"
      />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      className="h-4 w-4"
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="m5 12 4 4L19 6"
      />
    </svg>
  );
}

export default function HomePage() {
  return (
    <main className="min-h-screen bg-white text-slate-950">
      <header className="border-b border-white/10 bg-slate-950">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
          <Link
            href="/"
            className="text-xl font-semibold tracking-tight text-white"
          >
            MediBook
          </Link>

          <div className="flex items-center gap-3">
            <Link
              href="/hospital-login"
              className="hidden rounded-xl px-4 py-2 text-sm font-medium text-slate-300 hover:bg-white/5 hover:text-white sm:inline-flex"
            >
              Hospital login
            </Link>

            <Link
              href="/widget/medibook-demo"
              className="rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-500"
            >
              Try MediBook
            </Link>
          </div>
        </div>
      </header>

      <section className="overflow-hidden bg-slate-950">
        <div className="mx-auto grid max-w-7xl gap-14 px-6 py-20 lg:grid-cols-2 lg:items-center lg:py-28">
          <div>
            <div className="inline-flex rounded-full border border-brand-400/20 bg-brand-400/10 px-3 py-1.5 text-sm font-medium text-brand-200">
              AI appointment scheduling for hospitals
            </div>

            <h1 className="mt-7 text-5xl font-semibold leading-[1.06] tracking-tight text-white sm:text-6xl">
              Add conversational appointment scheduling to your hospital website.
            </h1>

            <p className="mt-7 max-w-2xl text-lg leading-8 text-slate-300">
              MediBook connects patients to your hospital through one intelligent
              conversation. Patients can ask for the right doctor, check real
              availability, book appointments, reschedule, and cancel without
              navigating forms or directory filters.
            </p>

            <div className="mt-9 flex flex-wrap gap-3">
              <Link
                href="/widget/medibook-demo"
                className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-5 py-3 text-sm font-semibold text-white hover:bg-brand-500"
              >
                <ChatIcon />
                Open patient demo
              </Link>

              <Link
                href="/hospital-login"
                className="rounded-xl border border-white/15 bg-white/5 px-5 py-3 text-sm font-semibold text-white hover:bg-white/10"
              >
                Hospital workspace
              </Link>
            </div>

            <div className="mt-9 flex flex-wrap gap-5 text-sm text-slate-300">
              <div className="flex items-center gap-2">
                <CheckIcon />
                Hospital-scoped doctors
              </div>

              <div className="flex items-center gap-2">
                <CheckIcon />
                Live availability
              </div>

              <div className="flex items-center gap-2">
                <CheckIcon />
                Real appointment actions
              </div>
            </div>
          </div>

          <div className="rounded-[28px] border border-white/10 bg-white shadow-2xl">
            <div className="flex items-center gap-3 border-b border-slate-200 px-5 py-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-600 text-white">
                <ChatIcon />
              </div>

              <div>
                <div className="text-sm font-semibold">
                  MediBook Assistant
                </div>

                <div className="text-xs text-brand-600">
                  Connected to hospital scheduling
                </div>
              </div>
            </div>

            <div className="space-y-5 bg-slate-50 p-6">
              <div className="ml-auto max-w-[85%] rounded-2xl rounded-br-md bg-brand-600 px-4 py-3 text-sm leading-6 text-white">
                I need a female cardiologist tomorrow evening.
              </div>

              <div className="max-w-[90%] rounded-2xl rounded-bl-md border border-slate-200 bg-white px-4 py-3 text-sm leading-6 text-slate-700">
                I found a matching doctor in this hospital. I can check her
                real appointment availability for tomorrow evening.
              </div>

              <div className="ml-auto max-w-[85%] rounded-2xl rounded-br-md bg-brand-600 px-4 py-3 text-sm leading-6 text-white">
                Show me the available times.
              </div>

              <div className="max-w-[90%] rounded-2xl rounded-bl-md border border-slate-200 bg-white px-4 py-3 text-sm leading-6 text-slate-700">
                I found real available slots. Choose one and I will prepare the
                appointment for confirmation.
              </div>
            </div>

            <div className="border-t border-slate-200 p-4">
              <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-400">
                Type your message...
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="bg-white">
        <div className="mx-auto max-w-7xl px-6 py-20">
          <div className="max-w-3xl">
            <div className="text-sm font-semibold uppercase tracking-[0.14em] text-brand-600">
              How MediBook fits
            </div>

            <h2 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
              Your hospital keeps its website. MediBook adds the scheduling intelligence.
            </h2>

            <p className="mt-5 text-lg leading-8 text-slate-600">
              MediBook is a SaaS scheduling layer, not a replacement hospital
              website and not a public doctor marketplace.
            </p>
          </div>

          <div className="mt-12 grid gap-5 md:grid-cols-3">
            <div className="rounded-2xl border border-slate-200 p-6">
              <div className="text-sm font-semibold text-brand-600">
                01
              </div>

              <h3 className="mt-3 text-lg font-semibold">
                Install MediBook
              </h3>

              <p className="mt-2 text-sm leading-6 text-slate-600">
                Add the hospital-specific MediBook assistant to the hospital&apos;s
                existing website.
              </p>
            </div>

            <div className="rounded-2xl border border-slate-200 p-6">
              <div className="text-sm font-semibold text-brand-600">
                02
              </div>

              <h3 className="mt-3 text-lg font-semibold">
                Patients use conversation
              </h3>

              <p className="mt-2 text-sm leading-6 text-slate-600">
                They describe what they need naturally. MediBook searches the
                hospital&apos;s real doctor and schedule data behind the scenes.
              </p>
            </div>

            <div className="rounded-2xl border border-slate-200 p-6">
              <div className="text-sm font-semibold text-brand-600">
                03
              </div>

              <h3 className="mt-3 text-lg font-semibold">
                Hospital stays in control
              </h3>

              <p className="mt-2 text-sm leading-6 text-slate-600">
                Hospital staff manage appointments, doctors, schedules,
                capacity, access, and integrations from their operations workspace.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="bg-slate-50">
        <div className="mx-auto grid max-w-7xl gap-12 px-6 py-20 lg:grid-cols-2 lg:items-center">
          <div>
            <div className="text-sm font-semibold uppercase tracking-[0.14em] text-brand-600">
              Patient journey
            </div>

            <h2 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
              Everything happens through the assistant.
            </h2>

            <div className="mt-7 space-y-4 text-sm leading-6 text-slate-700">
              {[
                "Ask for a doctor using natural language",
                "Check real hospital availability",
                "Choose an actual available appointment slot",
                "Confirm before the appointment is created",
                "View appointments inside the assistant",
                "Reschedule through conversation",
                "Cancel through conversation",
              ].map((item) => (
                <div
                  key={item}
                  className="flex items-start gap-3"
                >
                  <div className="mt-1 text-brand-600">
                    <CheckIcon />
                  </div>

                  <span>{item}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-3xl bg-slate-950 p-7 text-white shadow-xl">
            <div className="text-sm font-medium text-brand-300">
              Hospital website
            </div>

            <div className="mt-5 rounded-2xl border border-white/10 bg-white/5 p-6">
              <div className="h-3 w-36 rounded bg-white/20" />
              <div className="mt-4 h-3 w-full rounded bg-white/10" />
              <div className="mt-2 h-3 w-4/5 rounded bg-white/10" />

              <div className="mt-12 flex justify-end">
                <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-600 shadow-lg">
                  <ChatIcon />
                </div>
              </div>

              <div className="mt-4 rounded-2xl bg-white p-5 text-slate-800">
                <div className="font-semibold">
                  MediBook
                </div>

                <p className="mt-2 text-sm leading-6 text-slate-600">
                  Hi. Tell me what kind of appointment you need and I will
                  check this hospital&apos;s real availability.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="bg-brand-700">
        <div className="mx-auto flex max-w-7xl flex-col gap-8 px-6 py-16 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="text-sm font-semibold text-brand-200">
              MediBook for hospitals
            </div>

            <h2 className="mt-2 max-w-2xl text-3xl font-semibold text-white">
              Add AI-powered appointment scheduling without replacing your hospital website.
            </h2>
          </div>

          <div className="flex flex-wrap gap-3">
            <Link
              href="/widget/medibook-demo"
              className="rounded-xl bg-white px-5 py-3 text-sm font-semibold text-brand-700"
            >
              Try the assistant
            </Link>

            <Link
              href="/hospital-login"
              className="rounded-xl border border-white/20 bg-white/10 px-5 py-3 text-sm font-semibold text-white"
            >
              Hospital login
            </Link>
          </div>
        </div>
      </section>

      <footer className="bg-slate-950">
        <div className="mx-auto flex max-w-7xl flex-col justify-between gap-3 px-6 py-8 text-sm text-slate-400 sm:flex-row">
          <span>MediBook</span>
          <span>
            Conversational appointment infrastructure for hospitals
          </span>
        </div>
      </footer>
    </main>
  );
}
