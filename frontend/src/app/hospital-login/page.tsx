"use client";

import {
  FormEvent,
  useState,
} from "react";

import {
  useRouter,
} from "next/navigation";


export default function HospitalLoginPage() {
  const router =
    useRouter();


  const [
    email,
    setEmail,
  ] =
    useState(
      "",
    );


  const [
    password,
    setPassword,
  ] =
    useState(
      "",
    );


  const [
    loading,
    setLoading,
  ] =
    useState(
      false,
    );


  const [
    error,
    setError,
  ] =
    useState<
      string | null
    >(null);


  async function submit(
    event:
      FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setLoading(
      true,
    );

    setError(
      null,
    );


    try {
      const response =
        await fetch(
          "/api/auth/hospital-login",
          {
            method:
              "POST",

            headers: {
              "Content-Type":
                "application/json",
            },

            body:
              JSON.stringify({
                email,
                password,
              }),
          },
        );


      if (!response.ok) {
        let message =
          "Unable to sign in.";

        try {
          const body =
            await response.json();

          message =
            body.detail ??
            message;

        } catch {
          // Keep fallback.
        }

        throw new Error(
          message,
        );
      }


      const signedIn =
        (await response.json().catch(() => null)) as {
          user?: { role?: string };
        } | null;

      router.replace(
        signedIn?.user?.role === "platform_admin"
          ? "/control"
          : "/hospital-dashboard",
      );

      router.refresh();

    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to sign in.",
      );

    } finally {
      setLoading(
        false,
      );
    }
  }


  return (
    <main className="min-h-screen bg-slate-50 lg:grid lg:grid-cols-2">
      <section className="hidden bg-brand-700 p-12 text-white lg:flex lg:flex-col lg:justify-between">
        <div className="text-xl font-semibold">
          MediBook
        </div>

        <div className="max-w-lg">
          <div className="text-sm font-semibold uppercase tracking-[0.18em] text-brand-200">
            Hospital Operations
          </div>

          <h1 className="mt-5 text-5xl font-semibold leading-tight">
            Run appointment operations from one place.
          </h1>

          <p className="mt-6 max-w-md text-lg leading-8 text-brand-100">
            Manage appointment activity, doctors, schedules,
            availability and hospital integrations with
            tenant-isolated MediBook operations.
          </p>
        </div>

        <div className="text-sm text-brand-200">
          MediBook hospital workspace
        </div>
      </section>


      <section className="flex min-h-screen items-center justify-center px-6 py-12">
        <div className="w-full max-w-md">
          <div className="lg:hidden">
            <div className="text-xl font-semibold text-brand-700">
              MediBook
            </div>
          </div>


          <div className="mt-8 lg:mt-0">
            <div className="text-sm font-semibold text-brand-600">
              Hospital Operations
            </div>

            <h2 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">
              Sign in to your workspace
            </h2>

            <p className="mt-3 text-sm leading-6 text-slate-500">
              Use your MediBook hospital or platform account.
            </p>
          </div>


          <form
            onSubmit={
              submit
            }
            className="mt-8 space-y-5"
          >
            <div>
              <label className="text-sm font-medium text-slate-700">
                Email
              </label>

              <input
                type="email"
                autoComplete="email"
                required
                value={
                  email
                }
                onChange={
                  event =>
                    setEmail(
                      event.target.value,
                    )
                }
                className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none ring-brand-500 transition focus:ring-2"
                placeholder="you@hospital.com"
              />
            </div>


            <div>
              <label className="text-sm font-medium text-slate-700">
                Password
              </label>

              <input
                type="password"
                autoComplete="current-password"
                required
                value={
                  password
                }
                onChange={
                  event =>
                    setPassword(
                      event.target.value,
                    )
                }
                className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none ring-brand-500 transition focus:ring-2"
                placeholder="Enter your password"
              />
            </div>


            {error ? (
              <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                {error}
              </div>
            ) : null}


            <button
              disabled={
                loading
              }
              type="submit"
              className="w-full rounded-xl bg-brand-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {
                loading
                  ? "Signing in..."
                  : "Continue to hospital dashboard"
              }
            </button>
          </form>


          <p className="mt-6 text-xs leading-5 text-slate-500">
            Access to hospital data is validated by MediBook on
            the server. Signing in does not grant access to
            hospitals you are not assigned to.
          </p>
        </div>
      </section>
    </main>
  );
}
