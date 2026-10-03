import Link from "next/link";

export default async function LoginPage({
  searchParams,
}: {
  searchParams:
    Promise<{
      next?: string;
      error?: string;
    }>;
}) {
  const params =
    await searchParams;

  const next =
    params.next?.startsWith("/")
      ? params.next
      : "/widget/medibook-demo";

  return (
    <main className="grid min-h-screen bg-white lg:grid-cols-2">

      <section className="relative hidden overflow-hidden bg-brand-700 p-14 text-white lg:flex lg:flex-col lg:justify-between">

        <div className="relative z-10 flex items-center gap-3">

          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white font-bold text-brand-700">
            M
          </div>

          <div>
            <div className="font-semibold">
              MediBook
            </div>

            <div className="text-xs text-brand-100">
              AI hospital appointment assistant
            </div>
          </div>

        </div>


        <div className="relative z-10 max-w-xl">

          <p className="mb-5 text-sm text-brand-100">
            Healthcare appointments through conversation
          </p>

          <h1 className="text-5xl font-semibold leading-[1.08] tracking-tight">
            Find the right doctor.
            <br />
            Book in the same chat.
          </h1>

          <p className="mt-6 max-w-lg text-lg leading-8 text-brand-100">
            Sign in to continue your conversation,
            fees and availability. Book, reschedule
            or cancel without navigating a hospital portal.
          </p>

        </div>


        <div className="relative z-10 text-sm text-brand-100">
          Connected securely to the hospital&apos;s appointment system.
        </div>


        <div className="absolute -right-40 -top-40 h-[520px] w-[520px] rounded-full bg-white/10" />

        <div className="absolute -bottom-48 -left-28 h-[500px] w-[500px] rounded-full bg-brand-950/20" />

      </section>


      <section className="flex min-h-screen items-center justify-center px-6 py-12">

        <div className="w-full max-w-md">

          <div className="mb-9 flex items-center gap-3 lg:hidden">

            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-brand-700 font-bold text-white">
              M
            </div>

            <span className="text-xl font-semibold">
              MediBook
            </span>

          </div>


          <h2 className="text-3xl font-semibold tracking-tight">
            Welcome back
          </h2>

          <p className="mt-2 text-sm leading-6 text-slate-500">
            Sign in and continue directly to the MediBook assistant.
          </p>


          {params.error && (

            <div className="mt-6 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm leading-6 text-red-700">
              {params.error}
            </div>

          )}


          <form
            action="/api/auth/login-browser"
            method="POST"
            className="mt-8 space-y-5"
          >

            <input
              type="hidden"
              name="next"
              value={next}
            />


            <div>

              <label className="mb-2 block text-sm font-medium text-slate-700">
                Email
              </label>

              <input
                name="email"
                type="email"
                autoComplete="email"
                required
                placeholder="you@example.com"
                className="w-full rounded-2xl border border-brand-200 px-4 py-3.5 text-sm outline-none focus:border-brand-500 focus:ring-4 focus:ring-brand-100"
              />

            </div>


            <div>

              <label className="mb-2 block text-sm font-medium text-slate-700">
                Password
              </label>

              <input
                name="password"
                type="password"
                autoComplete="current-password"
                required
                placeholder="Enter your password"
                className="w-full rounded-2xl border border-brand-200 px-4 py-3.5 text-sm outline-none focus:border-brand-500 focus:ring-4 focus:ring-brand-100"
              />

            </div>


            <button className="w-full rounded-2xl bg-brand-700 px-4 py-3.5 text-sm font-semibold text-white transition hover:bg-brand-800">
              Continue to MediBook
            </button>


          <div className="mt-4 text-center">
            <a
              href="/forgot-password"
              className="text-sm font-medium text-brand-700 hover:text-brand-800"
            >
              Forgot password?
            </a>
          </div>

</form>


          <div className="mt-7 border-t border-slate-100 pt-6 text-center">

            <p className="text-sm text-slate-500">
              Don&apos;t have an account?
            </p>

            <Link
              href={`/signup?next=${encodeURIComponent(next)}`}
              className="mt-3 inline-flex w-full items-center justify-center rounded-2xl border border-brand-200 px-4 py-3.5 text-sm font-semibold text-brand-700 hover:bg-brand-50"
            >
              Create an account
            </Link>

          </div>

        </div>

      </section>

    </main>
  );
}
