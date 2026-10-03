"use client";

import {
  CalendarDays,
  LogIn,
  Menu,
  MessageSquareText,
  Stethoscope,
  UserRound,
  X,
} from "lucide-react";

import Link from "next/link";
import {
  usePathname,
} from "next/navigation";

import {
  useEffect,
  useState,
} from "react";


type User = {
  id?: string;
  full_name?: string;
  email?: string;
};


const NAVIGATION = [
  {
    href: "/doctors",
    label: "Find doctors",
    icon: Stethoscope,
  },
  {
    href: "/assistant",
    label: "AI Assistant",
    icon: MessageSquareText,
  },
  {
    href: "/appointments",
    label: "Appointments",
    icon: CalendarDays,
  },
];


export function MediBookHeader() {

  const pathname =
    usePathname();

  const [
    user,
    setUser,
  ] =
    useState<User | null>(
      null,
    );

  const [
    authChecked,
    setAuthChecked,
  ] =
    useState(false);

  const [
    mobileOpen,
    setMobileOpen,
  ] =
    useState(false);


  useEffect(
    () => {

      let active = true;


      async function checkAuth() {

        try {

          const response =
            await fetch(
              "/api/auth/me",
              {
                cache:
                  "no-store",
              },
            );


          if (
            response.ok &&
            active
          ) {

            const data =
              await response.json();

            setUser(
              data.user ??
              data,
            );
          }

        } catch {
          // Guest state is valid.
        } finally {

          if (active) {
            setAuthChecked(true);
          }
        }
      }


      void checkAuth();


      return () => {
        active = false;
      };

    },
    [
      pathname,
    ],
  );


  useEffect(
    () => {

      queueMicrotask(() => {
        setMobileOpen(
        false,
        );
      });

    },
    [
      pathname,
    ],
  );


  const hideShell =
    pathname === "/login" ||
    pathname === "/signup";


  if (hideShell) {
    return null;
  }


  return (
    <header className="sticky top-0 z-[80] border-b border-slate-200/80 bg-white/95 backdrop-blur">

      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-5 md:px-8">

        <Link
          href="/"
          className="flex items-center gap-2.5"
        >

          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-slate-950 text-white">

            <Stethoscope
              size={19}
            />

          </div>


          <div>

            <div className="text-lg font-black tracking-tight text-slate-950">
              MediBook
            </div>

            <div className="-mt-1 hidden text-[9px] font-semibold uppercase tracking-[0.18em] text-brand-600 sm:block">
              Healthcare scheduling
            </div>

          </div>

        </Link>


        <nav className="hidden items-center gap-1 lg:flex">

          {NAVIGATION.map(
            item => {

              const Icon =
                item.icon;

              const active =
                pathname ===
                  item.href ||
                pathname.startsWith(
                  `${item.href}/`,
                );


              return (

                <Link
                  key={item.href}
                  href={item.href}
                  className={[
                    "inline-flex items-center gap-2 rounded-xl px-3.5 py-2 text-sm font-semibold transition",

                    active
                      ? "bg-slate-950 text-white"
                      : "text-slate-600 hover:bg-slate-100 hover:text-slate-950",
                  ].join(
                    " ",
                  )}
                >

                  <Icon
                    size={15}
                  />

                  {item.label}

                </Link>

              );
            },
          )}

        </nav>


        <div className="hidden items-center gap-2 lg:flex">

          {!authChecked ? (

            <div className="h-9 w-24 animate-pulse rounded-xl bg-slate-100" />

          ) : user ? (

            <Link
              href="/profile"
              className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
            >

              <UserRound
                size={16}
              />

              {
                user.full_name
                  ?.split(" ")[0] ??
                "Profile"
              }

            </Link>

          ) : (

            <Link
              href="/login"
              className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-700"
            >

              <LogIn
                size={15}
              />

              Sign in

            </Link>

          )}

        </div>


        <button
          type="button"
          aria-label="Open navigation"
          onClick={
            () =>
              setMobileOpen(
                value =>
                  !value,
              )
          }
          className="rounded-xl border border-slate-200 p-2 text-slate-700 lg:hidden"
        >

          {mobileOpen ? (
            <X size={19} />
          ) : (
            <Menu size={19} />
          )}

        </button>

      </div>


      {mobileOpen && (

        <div className="border-t border-slate-100 bg-white px-5 py-4 lg:hidden">

          <div className="mx-auto max-w-7xl space-y-1">

            {NAVIGATION.map(
              item => {

                const Icon =
                  item.icon;

                const active =
                  pathname ===
                    item.href ||
                  pathname.startsWith(
                    `${item.href}/`,
                  );


                return (

                  <Link
                    key={item.href}
                    href={item.href}
                    className={[
                      "flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-semibold",

                      active
                        ? "bg-slate-950 text-white"
                        : "text-slate-700 hover:bg-slate-50",
                    ].join(
                      " ",
                    )}
                  >

                    <Icon
                      size={17}
                    />

                    {item.label}

                  </Link>

                );
              },
            )}


            <div className="my-3 border-t border-slate-100" />


            {user ? (

              <Link
                href="/profile"
                className="flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50"
              >

                <UserRound
                  size={17}
                />

                My profile

              </Link>

            ) : (

              <Link
                href="/login"
                className="flex items-center justify-center gap-2 rounded-xl bg-brand-600 px-3 py-3 text-sm font-semibold text-white"
              >

                <LogIn
                  size={17}
                />

                Sign in to MediBook

              </Link>

            )}

          </div>

        </div>

      )}

    </header>
  );
}
