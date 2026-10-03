"use client";

import Link from "next/link";

import {
  CalendarDays,
  ChevronDown,
  LogOut,
  UserRound,
} from "lucide-react";

import {
  useEffect,
  useRef,
  useState,
} from "react";

import {
  usePathname,
  useRouter,
} from "next/navigation";


type CurrentUser = {
  id: string;
  email: string;
  full_name: string;
  phone: string;
  role: string;
};


export function SiteHeader() {

  const router =
    useRouter();

  const pathname =
    usePathname();

  const menuRef =
    useRef<HTMLDivElement | null>(
      null,
    );

  const [
    user,
    setUser,
  ] = useState<CurrentUser | null>(
    null,
  );

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    menuOpen,
    setMenuOpen,
  ] = useState(false);

  const [
    signingOut,
    setSigningOut,
  ] = useState(false);


  useEffect(() => {

    let active = true;

    async function loadUser() {

      try {

        const response =
          await fetch(
            "/api/auth/me",
            {
              cache: "no-store",
            },
          );

        if (!active) {
          return;
        }

        if (!response.ok) {
          setUser(null);
          return;
        }

        const data =
          await response.json();

        setUser(data);

      } catch {

        if (active) {
          setUser(null);
        }

      } finally {

        if (active) {
          setLoading(false);
        }
      }
    }

    void loadUser();

    return () => {
      active = false;
    };

  }, [
    pathname,
  ]);


  useEffect(() => {

    function closeMenu(
      event: MouseEvent,
    ) {

      if (
        menuRef.current &&
        !menuRef.current.contains(
          event.target as Node,
        )
      ) {
        setMenuOpen(false);
      }
    }

    document.addEventListener(
      "mousedown",
      closeMenu,
    );

    return () => {
      document.removeEventListener(
        "mousedown",
        closeMenu,
      );
    };

  }, []);


  async function logout() {

    setSigningOut(true);

    try {

      await fetch(
        "/api/auth/logout",
        {
          method: "POST",
        },
      );

      setUser(null);
      setMenuOpen(false);

      router.replace(
        "/login",
      );

      router.refresh();

    } finally {

      setSigningOut(false);
    }
  }


  const initials =
    user?.full_name
      ?.split(" ")
      .filter(Boolean)
      .slice(0, 2)
      .map(
        part =>
          part[0]?.toUpperCase(),
      )
      .join("") || "U";


  return (
    <header className="sticky top-0 z-50 border-b border-slate-200 bg-white/95 backdrop-blur">

      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6">

        <Link
          href="/"
          className="flex items-center gap-3"
        >

          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600 font-bold text-white">
            M
          </div>

          <div>
            <div className="text-base font-bold tracking-tight text-slate-950">
              MediBook
            </div>

            <div className="hidden text-[11px] text-slate-500 sm:block">
              Doctor appointments made simple
            </div>
          </div>

        </Link>


        <div className="flex items-center gap-2">

          {!loading &&
          !user && (

            <>
              <Link
                href="/login"
                className="rounded-xl px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-100"
              >
                Sign in
              </Link>

              <Link
                href="/signup"
                className="rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-700"
              >
                Create account
              </Link>
            </>

          )}


          {!loading &&
          user && (

            <>
              <Link
                href="/appointments"
                title="My appointments"
                aria-label="My appointments"
                className={[
                  "flex h-10 w-10 items-center justify-center rounded-xl border transition",

                  pathname.startsWith(
                    "/appointments",
                  )
                    ? "border-brand-200 bg-brand-50 text-brand-700"
                    : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50",
                ].join(" ")}
              >
                <CalendarDays
                  size={19}
                />
              </Link>


              <div
                ref={menuRef}
                className="relative"
              >

                <button
                  type="button"
                  onClick={() =>
                    setMenuOpen(
                      current =>
                        !current,
                    )
                  }
                  aria-expanded={
                    menuOpen
                  }
                  className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white p-1.5 pr-2 transition hover:bg-slate-50"
                >

                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-950 text-xs font-bold text-white">
                    {initials}
                  </div>

                  <div className="hidden max-w-36 text-left md:block">

                    <div className="truncate text-xs font-bold text-slate-900">
                      {user.full_name}
                    </div>

                    <div className="truncate text-[10px] text-slate-500">
                      Patient account
                    </div>

                  </div>

                  <ChevronDown
                    size={14}
                    className={[
                      "text-slate-400 transition",

                      menuOpen
                        ? "rotate-180"
                        : "",
                    ].join(" ")}
                  />

                </button>


                {menuOpen && (

                  <div className="absolute right-0 mt-2 w-72 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl">

                    <div className="border-b border-slate-100 p-4">

                      <div className="flex items-center gap-3">

                        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-brand-50 text-brand-700">
                          <UserRound
                            size={20}
                          />
                        </div>

                        <div className="min-w-0">

                          <div className="truncate text-sm font-bold text-slate-950">
                            {user.full_name}
                          </div>

                          <div className="truncate text-xs text-slate-500">
                            {user.email}
                          </div>

                        </div>

                      </div>

                    </div>


                    <div className="p-2">

                      <Link
                        href="/profile"
                        onClick={() =>
                          setMenuOpen(false)
                        }
                        className="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
                      >
                        <UserRound size={17} />
                        My profile
                      </Link>

                      <Link
                        href="/appointments"
                        onClick={() =>
                          setMenuOpen(
                            false,
                          )
                        }
                        className="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
                      >
                        <CalendarDays
                          size={17}
                        />

                        My appointments
                      </Link>


                      <button
                        type="button"
                        disabled={
                          signingOut
                        }
                        onClick={
                          logout
                        }
                        className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm font-medium text-red-600 transition hover:bg-red-50 disabled:opacity-50"
                      >
                        <LogOut
                          size={17}
                        />

                        {signingOut
                          ? "Signing out…"
                          : "Sign out"}
                      </button>

                    </div>

                  </div>

                )}

              </div>
            </>

          )}


          {loading && (

            <div className="h-10 w-24 animate-pulse rounded-xl bg-slate-100" />

          )}

        </div>

      </div>

    </header>
  );
}
