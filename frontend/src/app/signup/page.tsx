"use client";

import {
  FormEvent,
  useEffect,
  useState,
} from "react";

import {
  useRouter,
  useSearchParams,
} from "next/navigation";


function maskEmail(
  email: string,
) {
  const [
    local,
    domain,
  ] =
    email.split("@");

  if (
    !local ||
    !domain
  ) {
    return email;
  }

  return (
    local.slice(
      0,
      2,
    )
    +
    "•".repeat(
      Math.max(
        local.length - 2,
        3,
      ),
    )
    +
    "@"
    +
    domain
  );
}


export default function SignupPage() {
  const router =
    useRouter();

  const searchParams =
    useSearchParams();


  const returnTo =
    searchParams.get(
      "returnTo",
    )
    ??
    "/widget/medibook-demo";


  const [
    verifying,
    setVerifying,
  ] =
    useState(
      false,
    );


  const [
    fullName,
    setFullName,
  ] =
    useState(
      "",
    );


  const [
    email,
    setEmail,
  ] =
    useState(
      "",
    );


  const [
    phone,
    setPhone,
  ] =
    useState(
      "",
    );


  const [
    gender,
    setGender,
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
    confirmPassword,
    setConfirmPassword,
  ] =
    useState(
      "",
    );


  const [
    photo,
    setPhoto,
  ] =
    useState<File | null>(
      null,
    );


  const [
    code,
    setCode,
  ] =
    useState(
      "",
    );


  const [
    resend,
    setResend,
  ] =
    useState(
      0,
    );


  const [
    busy,
    setBusy,
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


  useEffect(
    () => {
      if (
        resend <= 0
      ) {
        return;
      }

      const interval =
        window.setInterval(
          () => {
            setResend(
              value =>
                Math.max(
                  value - 1,
                  0,
                ),
            );
          },
          1000,
        );

      return () => {
        window.clearInterval(
          interval,
        );
      };
    },
    [
      resend,
    ],
  );


  async function begin(
    event:
      FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setError(
      null,
    );


    if (
      password !==
      confirmPassword
    ) {
      setError(
        "Passwords do not match.",
      );
      return;
    }


    setBusy(
      true,
    );


    try {
      // Photo is collected now but storage is
      // intentionally a separate implementation.
      // It remains optional and never blocks signup.
      void photo;


      const response =
        await fetch(
          "/api/auth/signup-start",
          {
            method:
              "POST",

            headers: {
              "Content-Type":
                "application/json",
            },

            body:
              JSON.stringify({
                full_name:
                  fullName,

                email,

                phone,

                gender,

                password,

                profile_image_url:
                  null,
              }),
          },
        );


      const data =
        await response.json();


      if (!response.ok) {
        throw new Error(
          data.detail ??
          "Could not create registration.",
        );
      }


      setVerifying(
        true,
      );

      setResend(
        Number(
          data.resend_after_seconds
          ??
          60,
        ),
      );


    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Registration failed.",
      );

    } finally {
      setBusy(
        false,
      );
    }
  }


  async function confirm(
    event:
      FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setError(
      null,
    );


    if (
      !/^\d{6}$/.test(
        code,
      )
    ) {
      setError(
        "Enter the 6-digit verification code.",
      );

      return;
    }


    setBusy(
      true,
    );


    try {
      const response =
        await fetch(
          "/api/auth/signup-verify",
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
                code,
                password,
              }),
          },
        );


      const data =
        await response.json();


      if (!response.ok) {
        throw new Error(
          data.detail ??
          "Verification failed.",
        );
      }


      if (
        data.authenticated
      ) {
        router.replace(
          returnTo.startsWith(
            "/"
          )
            ? returnTo
            : "/widget/medibook-demo",
        );

        router.refresh();

        return;
      }


      router.replace(
        "/login",
      );


    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Verification failed.",
      );

    } finally {
      setBusy(
        false,
      );
    }
  }


  async function resendCode() {
    if (
      resend > 0 ||
      busy
    ) {
      return;
    }

    setBusy(
      true,
    );

    setError(
      null,
    );


    try {
      const response =
        await fetch(
          "/api/auth/signup-resend",
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
              }),
          },
        );


      const data =
        await response.json();


      if (!response.ok) {
        throw new Error(
          data.detail ??
          "Could not resend verification code.",
        );
      }


      setResend(
        Number(
          data.resend_after_seconds
          ??
          60,
        ),
      );


    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Could not resend verification code.",
      );

    } finally {
      setBusy(
        false,
      );
    }
  }


  return (
    <main className="min-h-screen bg-slate-50 px-5 py-10">
      <div className="mx-auto max-w-lg">
        <div className="text-xl font-semibold text-purple-700">
          MediBook
        </div>


        <h1 className="mt-8 text-3xl font-semibold tracking-tight text-slate-950">
          {
            verifying
              ? "Verify your email"
              : "Create your patient account"
          }
        </h1>


        <p className="mt-3 text-sm leading-6 text-slate-500">
          {
            verifying
              ? (
                "We sent a 6-digit verification code to "
                +
                maskEmail(
                  email,
                )
                +
                "."
              )
              : (
                "Create your profile once. MediBook will "
                +
                "use the verified details when you make "
                +
                "appointments."
              )
          }
        </p>


        <section className="mt-8 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          {
            !verifying
              ? (
                <form
                  onSubmit={
                    begin
                  }
                  className="space-y-5"
                >
                  <label className="block">
                    <span className="text-sm font-medium text-slate-700">
                      Full name
                    </span>

                    <input
                      required
                      value={
                        fullName
                      }
                      onChange={
                        e =>
                          setFullName(
                            e.target.value,
                          )
                      }
                      autoComplete="name"
                      className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:ring-2 focus:ring-purple-500"
                    />
                  </label>


                  <label className="block">
                    <span className="text-sm font-medium text-slate-700">
                      Email
                    </span>

                    <input
                      required
                      type="email"
                      value={
                        email
                      }
                      onChange={
                        e =>
                          setEmail(
                            e.target.value,
                          )
                      }
                      autoComplete="email"
                      className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:ring-2 focus:ring-purple-500"
                    />
                  </label>


                  <label className="block">
                    <span className="text-sm font-medium text-slate-700">
                      Mobile number
                    </span>

                    <input
                      required
                      type="tel"
                      value={
                        phone
                      }
                      onChange={
                        e =>
                          setPhone(
                            e.target.value,
                          )
                      }
                      autoComplete="tel"
                      className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:ring-2 focus:ring-purple-500"
                    />
                  </label>


                  <label className="block">
                    <span className="text-sm font-medium text-slate-700">
                      Gender
                    </span>

                    <select
                      required
                      value={
                        gender
                      }
                      onChange={
                        e =>
                          setGender(
                            e.target.value,
                          )
                      }
                      className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-4 py-3 outline-none focus:ring-2 focus:ring-purple-500"
                    >
                      <option value="">
                        Select gender
                      </option>

                      <option value="male">
                        Male
                      </option>

                      <option value="female">
                        Female
                      </option>

                      <option value="other">
                        Other
                      </option>

                      <option value="prefer_not_to_say">
                        Prefer not to say
                      </option>
                    </select>
                  </label>


                  <label className="block">
                    <span className="text-sm font-medium text-slate-700">
                      Profile picture
                    </span>

                    <input
                      type="file"
                      accept="image/jpeg,image/png,image/webp"
                      onChange={
                        e =>
                          setPhoto(
                            e.target.files?.[
                              0
                            ]
                            ??
                            null,
                          )
                      }
                      className="mt-2 block w-full text-sm text-slate-600"
                    />

                    <span className="mt-1 block text-xs text-slate-500">
                      Optional
                    </span>
                  </label>


                  <label className="block">
                    <span className="text-sm font-medium text-slate-700">
                      Password
                    </span>

                    <input
                      required
                      minLength={
                        8
                      }
                      type="password"
                      value={
                        password
                      }
                      onChange={
                        e =>
                          setPassword(
                            e.target.value,
                          )
                      }
                      autoComplete="new-password"
                      className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:ring-2 focus:ring-purple-500"
                    />
                  </label>


                  <label className="block">
                    <span className="text-sm font-medium text-slate-700">
                      Confirm password
                    </span>

                    <input
                      required
                      type="password"
                      value={
                        confirmPassword
                      }
                      onChange={
                        e =>
                          setConfirmPassword(
                            e.target.value,
                          )
                      }
                      autoComplete="new-password"
                      className="mt-2 w-full rounded-xl border border-slate-200 px-4 py-3 outline-none focus:ring-2 focus:ring-purple-500"
                    />
                  </label>


                  {
                    error
                      ? (
                        <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                          {
                            error
                          }
                        </div>
                      )
                      : null
                  }


                  <button
                    disabled={
                      busy
                    }
                    className="w-full rounded-xl bg-purple-600 px-4 py-3 text-sm font-semibold text-white disabled:opacity-50"
                  >
                    {
                      busy
                        ? "Sending verification code..."
                        : "Continue"
                    }
                  </button>
                </form>
              )
              : (
                <form
                  onSubmit={
                    confirm
                  }
                  className="space-y-6"
                >
                  <label className="block">
                    <span className="text-sm font-medium text-slate-700">
                      Verification code
                    </span>

                    <input
                      required
                      autoFocus
                      inputMode="numeric"
                      autoComplete="one-time-code"
                      maxLength={
                        6
                      }
                      value={
                        code
                      }
                      onChange={
                        e =>
                          setCode(
                            e.target.value
                              .replace(
                                /\D/g,
                                "",
                              )
                              .slice(
                                0,
                                6,
                              ),
                          )
                      }
                      placeholder="000000"
                      className="mt-3 w-full rounded-xl border border-slate-200 px-4 py-4 text-center font-mono text-2xl tracking-[0.4em] outline-none focus:ring-2 focus:ring-purple-500"
                    />
                  </label>


                  {
                    error
                      ? (
                        <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                          {
                            error
                          }
                        </div>
                      )
                      : null
                  }


                  <button
                    disabled={
                      busy ||
                      code.length !==
                      6
                    }
                    className="w-full rounded-xl bg-purple-600 px-4 py-3 text-sm font-semibold text-white disabled:opacity-50"
                  >
                    {
                      busy
                        ? "Verifying..."
                        : "Verify email"
                    }
                  </button>


                  <div className="text-center text-sm text-slate-500">
                    {
                      resend > 0
                        ? (
                          <>
                            Resend code in{" "}
                            {
                              resend
                            }
                            s
                          </>
                        )
                        : (
                          <button
                            type="button"
                            onClick={
                              resendCode
                            }
                            className="font-medium text-purple-600"
                          >
                            Resend code
                          </button>
                        )
                    }
                  </div>


                  <button
                    type="button"
                    onClick={
                      () => {
                        setVerifying(
                          false,
                        );

                        setCode(
                          "",
                        );

                        setError(
                          null,
                        );
                      }
                    }
                    className="w-full text-sm text-slate-500"
                  >
                    Change email
                  </button>
                </form>
              )
          }
        </section>
      </div>
    </main>
  );
}
