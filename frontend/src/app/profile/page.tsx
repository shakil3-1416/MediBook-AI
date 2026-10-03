"use client";

import {
  FormEvent,
  useEffect,
  useState,
} from "react";


type User = {
  id: string;
  email: string;
  full_name: string;
  phone: string;
  role: string;
  gender?: string | null;
  profile_image_url?: string | null;
  email_verified_at?: string | null;
};


export default function ProfilePage() {

  const [
    user,
    setUser,
  ] =
    useState<User | null>(
      null,
    );

  const [
    fullName,
    setFullName,
  ] =
    useState("");

  const [
    phone,
    setPhone,
  ] =
    useState("");

  const [
    gender,
    setGender,
  ] =
    useState("");

  const [
    newEmail,
    setNewEmail,
  ] =
    useState("");

  const [
    emailCode,
    setEmailCode,
  ] =
    useState("");

  const [
    emailChangePending,
    setEmailChangePending,
  ] =
    useState(false);

  const [
    loading,
    setLoading,
  ] =
    useState(true);

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


  async function load() {

    const response =
      await fetch(
        "/api/auth/me",
        {
          cache:
            "no-store",
        },
      );

    if (!response.ok) {
      throw new Error(
        "Unable to load profile.",
      );
    }

    const payload =
      await response.json();

    const next: User =
      payload.user
      ??
      payload;

    setUser(
      next,
    );

    setFullName(
      next.full_name
      ??
      "",
    );

    setPhone(
      next.phone
      ??
      "",
    );

    setGender(
      next.gender
      ??
      "",
    );
  }


  useEffect(
    () => {
      queueMicrotask(() => {
        void load()
        .catch(
        error =>
        setMessage(
        error instanceof Error
        ? error.message
        : "Unable to load profile.",
        ),
        )
        .finally(
        () =>
        setLoading(
        false,
        ),
        );
      });
    },
    [],
  );


  async function saveProfile(
    event: FormEvent,
  ) {
    event.preventDefault();

    setBusy(true);
    setMessage("");

    try {
      const response =
        await fetch(
          "/api/auth/profile",
          {
            method:
              "PATCH",

            headers: {
              "Content-Type":
                "application/json",
            },

            body:
              JSON.stringify(
                {
                  full_name:
                    fullName,

                  phone,

                  gender:
                    gender || null,
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
          "Could not update profile.",
        );
      }

      setUser(
        data,
      );

      setMessage(
        "Profile updated.",
      );

    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "Could not update profile.",
      );

    } finally {
      setBusy(false);
    }
  }


  async function uploadPhoto(
    file: File,
  ) {

    setBusy(true);
    setMessage("");

    try {
      const response =
        await fetch(
          "/api/auth/profile-image",
          {
            method:
              "POST",

            headers: {
              "Content-Type":
                file.type,
            },

            body:
              file,
          },
        );

      const data =
        await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail
          ??
          "Could not upload profile picture.",
        );
      }

      await load();

      setMessage(
        "Profile picture updated.",
      );

    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "Could not upload profile picture.",
      );

    } finally {
      setBusy(false);
    }
  }


  async function startEmailChange(
    event: FormEvent,
  ) {
    event.preventDefault();

    setBusy(true);
    setMessage("");

    try {
      const response =
        await fetch(
          "/api/auth/email-change/start",
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
                  new_email:
                    newEmail,
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
          "Could not start email change.",
        );
      }

      setEmailChangePending(
        true,
      );

      setMessage(
        "Verification code sent to the new email address.",
      );

    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "Could not start email change.",
      );

    } finally {
      setBusy(false);
    }
  }


  async function verifyEmailChange(
    event: FormEvent,
  ) {
    event.preventDefault();

    setBusy(true);
    setMessage("");

    try {
      const response =
        await fetch(
          "/api/auth/email-change/verify",
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
                  new_email:
                    newEmail,

                  code:
                    emailCode,
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
          "Email verification failed.",
        );
      }

      setEmailCode("");
      setNewEmail("");
      setEmailChangePending(
        false,
      );

      await load();

      setMessage(
        "Email address updated and verified.",
      );

    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "Email verification failed.",
      );

    } finally {
      setBusy(false);
    }
  }


  if (loading) {
    return (
      <main className="min-h-screen bg-brand-50/30 p-8 text-sm text-slate-500">
        Loading profile...
      </main>
    );
  }


  if (!user) {
    return (
      <main className="min-h-screen bg-brand-50/30 p-8">
        <div className="mx-auto max-w-lg rounded-2xl border border-brand-100 bg-white p-6">
          <p>
            {message
              ||
              "Please sign in again."}
          </p>

          <a
            href="/login"
            className="mt-4 inline-block rounded-xl bg-brand-700 px-4 py-2.5 text-sm font-semibold text-white"
          >
            Sign in
          </a>
        </div>
      </main>
    );
  }


  const initials =
    user.full_name
      .split(
        " ",
      )
      .filter(
        Boolean,
      )
      .slice(
        0,
        2,
      )
      .map(
        part =>
          part[0]?.toUpperCase(),
      )
      .join("");


  return (
    <main className="min-h-screen bg-brand-50/30 px-5 py-8">

      <div className="mx-auto max-w-3xl">

        <button
          type="button"
          onClick={() =>
            window.history.back()
          }
          className="text-sm font-medium text-brand-700"
        >
          ← Back
        </button>

        <div className="mt-5 rounded-3xl border border-brand-100 bg-white p-6 shadow-sm md:p-8">

          <div className="flex flex-col gap-5 sm:flex-row sm:items-center">

            {user.profile_image_url ? (
              <img
                src={
                  user.profile_image_url
                }
                alt=""
                className="h-20 w-20 rounded-3xl object-cover"
              />
            ) : (
              <div className="flex h-20 w-20 items-center justify-center rounded-3xl bg-brand-700 text-xl font-bold text-white">
                {initials || "P"}
              </div>
            )}

            <div>
              <div className="text-xs font-semibold uppercase tracking-wider text-brand-600">
                Patient account
              </div>

              <h1 className="mt-1 text-2xl font-semibold text-slate-950">
                {user.full_name}
              </h1>

              <p className="mt-1 text-sm text-slate-500">
                {user.email}
              </p>
            </div>

          </div>

          <label className="mt-6 block text-sm font-medium text-slate-700">
            Profile picture
            <input
              type="file"
              accept="image/png,image/jpeg,image/webp"
              disabled={busy}
              onChange={event => {
                const file =
                  event.target.files?.[0];

                if (file) {
                  void uploadPhoto(
                    file,
                  );
                }
              }}
              className="mt-2 block w-full text-sm"
            />
          </label>

        </div>


        <form
          onSubmit={saveProfile}
          className="mt-5 rounded-3xl border border-brand-100 bg-white p-6 shadow-sm md:p-8"
        >

          <h2 className="text-lg font-semibold text-slate-950">
            Profile details
          </h2>

          <div className="mt-5 grid gap-4 sm:grid-cols-2">

            <label className="text-sm font-medium text-slate-700">
              Full name
              <input
                required
                value={fullName}
                onChange={event =>
                  setFullName(
                    event.target.value,
                  )
                }
                className="mt-2 w-full rounded-xl border border-brand-100 px-3 py-3 outline-none focus:border-brand-400"
              />
            </label>

            <label className="text-sm font-medium text-slate-700">
              Phone
              <input
                required
                value={phone}
                onChange={event =>
                  setPhone(
                    event.target.value,
                  )
                }
                className="mt-2 w-full rounded-xl border border-brand-100 px-3 py-3 outline-none focus:border-brand-400"
              />
            </label>

            <label className="text-sm font-medium text-slate-700">
              Gender
              <select
                value={gender}
                onChange={event =>
                  setGender(
                    event.target.value,
                  )
                }
                className="mt-2 w-full rounded-xl border border-brand-100 px-3 py-3 outline-none focus:border-brand-400"
              >
                <option value="">
                  Prefer not to say
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
              </select>
            </label>

          </div>

          <button
            disabled={busy}
            className="mt-5 rounded-xl bg-brand-700 px-5 py-3 text-sm font-semibold text-white disabled:opacity-50"
          >
            Save profile
          </button>

        </form>


        <div className="mt-5 rounded-3xl border border-brand-100 bg-white p-6 shadow-sm md:p-8">

          <h2 className="text-lg font-semibold text-slate-950">
            Email
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            Your current verified email is {user.email}.
          </p>

          {!emailChangePending ? (
            <form
              onSubmit={startEmailChange}
              className="mt-5"
            >
              <label className="block text-sm font-medium text-slate-700">
                New email
                <input
                  type="email"
                  required
                  value={newEmail}
                  onChange={event =>
                    setNewEmail(
                      event.target.value,
                    )
                  }
                  className="mt-2 w-full rounded-xl border border-brand-100 px-3 py-3 outline-none focus:border-brand-400"
                />
              </label>

              <button
                disabled={busy}
                className="mt-4 rounded-xl border border-brand-200 px-4 py-2.5 text-sm font-semibold text-brand-700 disabled:opacity-50"
              >
                Verify new email
              </button>
            </form>
          ) : (
            <form
              onSubmit={verifyEmailChange}
              className="mt-5"
            >
              <label className="block text-sm font-medium text-slate-700">
                Six-digit code
                <input
                  required
                  inputMode="numeric"
                  maxLength={6}
                  value={emailCode}
                  onChange={event =>
                    setEmailCode(
                      event.target.value.replace(
                        /\D/g,
                        "",
                      ),
                    )
                  }
                  className="mt-2 w-full rounded-xl border border-brand-100 px-3 py-3 tracking-[0.35em] outline-none focus:border-brand-400"
                />
              </label>

              <button
                disabled={busy}
                className="mt-4 rounded-xl bg-brand-700 px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50"
              >
                Confirm email change
              </button>
            </form>
          )}

        </div>


        <div className="mt-5 rounded-3xl border border-brand-100 bg-white p-6 shadow-sm md:p-8">

          <h2 className="text-lg font-semibold text-slate-950">
            Password
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            Password changes require email verification.
          </p>

          <a
            href="/forgot-password"
            className="mt-4 inline-block rounded-xl border border-brand-200 px-4 py-2.5 text-sm font-semibold text-brand-700"
          >
            Reset password
          </a>

        </div>


        {message && (
          <div className="mt-5 rounded-2xl bg-brand-100 px-4 py-3 text-sm text-brand-900">
            {message}
          </div>
        )}

      </div>

    </main>
  );
}
