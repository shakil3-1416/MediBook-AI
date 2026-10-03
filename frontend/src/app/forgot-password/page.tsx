"use client";

import {
  FormEvent,
  useState,
} from "react";


export default function ForgotPasswordPage() {

  const [
    email,
    setEmail,
  ] =
    useState("");

  const [
    code,
    setCode,
  ] =
    useState("");

  const [
    password,
    setPassword,
  ] =
    useState("");

  const [
    step,
    setStep,
  ] =
    useState<
      "email"
      |
      "verify"
      |
      "done"
    >(
      "email",
    );

  const [
    busy,
    setBusy,
  ] =
    useState(false);

  const [
    message,
    setMessage,
  ] =
    useState("");


  async function start(
    event: FormEvent,
  ) {
    event.preventDefault();

    setBusy(true);
    setMessage("");

    try {
      const response =
        await fetch(
          "/api/auth/password-reset/start",
          {
            method:
              "POST",

            headers: {
              "Content-Type":
                "application/json",
            },

            body:
              JSON.stringify(
                {
                  email,
                },
              ),
          },
        );

      const data =
        await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail
          ??
          "Could not start password reset.",
        );
      }

      setStep(
        "verify",
      );

      setMessage(
        "If the account exists, a verification code has been sent.",
      );

    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "Password reset failed.",
      );

    } finally {
      setBusy(false);
    }
  }


  async function verify(
    event: FormEvent,
  ) {
    event.preventDefault();

    setBusy(true);
    setMessage("");

    try {
      const response =
        await fetch(
          "/api/auth/password-reset/verify",
          {
            method:
              "POST",

            headers: {
              "Content-Type":
                "application/json",
            },

            body:
              JSON.stringify(
                {
                  email,
                  code,
                  new_password:
                    password,
                },
              ),
          },
        );

      const data =
        await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail
          ??
          "Password reset failed.",
        );
      }

      setStep(
        "done",
      );

      setMessage(
        "Your password has been updated.",
      );

    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "Password reset failed.",
      );

    } finally {
      setBusy(false);
    }
  }


  async function resend() {

    setBusy(true);
    setMessage("");

    try {
      const response =
        await fetch(
          "/api/auth/password-reset/resend",
          {
            method:
              "POST",

            headers: {
              "Content-Type":
                "application/json",
            },

            body:
              JSON.stringify(
                {
                  email,
                },
              ),
          },
        );

      if (!response.ok) {
        const data =
          await response.json();

        throw new Error(
          data.detail
          ??
          "Could not resend the code.",
        );
      }

      setMessage(
        "If the account exists, a new code has been sent.",
      );

    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "Could not resend the code.",
      );

    } finally {
      setBusy(false);
    }
  }


  return (
    <main className="min-h-screen bg-brand-50/40 px-5 py-12">

      <div className="mx-auto max-w-md rounded-3xl border border-brand-100 bg-white p-7 shadow-sm">

        <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-brand-700 font-bold text-white">
          M
        </div>

        <h1 className="mt-6 text-2xl font-semibold text-slate-950">
          Reset your password
        </h1>

        <p className="mt-2 text-sm leading-6 text-slate-500">
          Verify your email before setting a new password.
        </p>

        {step === "email" && (
          <form
            onSubmit={start}
            className="mt-7 space-y-4"
          >
            <label className="block text-sm font-medium text-slate-700">
              Email
              <input
                type="email"
                required
                value={email}
                onChange={event =>
                  setEmail(
                    event.target.value,
                  )
                }
                className="mt-2 w-full rounded-xl border border-brand-100 px-3 py-3 outline-none focus:border-brand-400"
              />
            </label>

            <button
              disabled={busy}
              className="w-full rounded-xl bg-brand-700 px-4 py-3 text-sm font-semibold text-white disabled:opacity-50"
            >
              {busy
                ? "Sending..."
                : "Send verification code"}
            </button>
          </form>
        )}

        {step === "verify" && (
          <form
            onSubmit={verify}
            className="mt-7 space-y-4"
          >
            <label className="block text-sm font-medium text-slate-700">
              Six-digit code
              <input
                inputMode="numeric"
                maxLength={6}
                required
                value={code}
                onChange={event =>
                  setCode(
                    event.target.value.replace(
                      /\D/g,
                      "",
                    ),
                  )
                }
                className="mt-2 w-full rounded-xl border border-brand-100 px-3 py-3 tracking-[0.35em] outline-none focus:border-brand-400"
              />
            </label>

            <label className="block text-sm font-medium text-slate-700">
              New password
              <input
                type="password"
                minLength={8}
                required
                value={password}
                onChange={event =>
                  setPassword(
                    event.target.value,
                  )
                }
                className="mt-2 w-full rounded-xl border border-brand-100 px-3 py-3 outline-none focus:border-brand-400"
              />
            </label>

            <button
              disabled={busy}
              className="w-full rounded-xl bg-brand-700 px-4 py-3 text-sm font-semibold text-white disabled:opacity-50"
            >
              Reset password
            </button>

            <button
              type="button"
              onClick={resend}
              disabled={busy}
              className="w-full px-4 py-2 text-sm font-medium text-brand-700 disabled:opacity-50"
            >
              Resend code
            </button>
          </form>
        )}

        {step === "done" && (
          <a
            href="/login"
            className="mt-7 block rounded-xl bg-brand-700 px-4 py-3 text-center text-sm font-semibold text-white"
          >
            Sign in
          </a>
        )}

        {message && (
          <p className="mt-5 rounded-xl bg-brand-50 px-4 py-3 text-sm text-brand-800">
            {message}
          </p>
        )}

      </div>

    </main>
  );
}
