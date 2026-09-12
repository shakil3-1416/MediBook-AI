import {
  Suspense,
  type ReactNode,
} from "react";


function SignupLoading() {
  return (
    <main
      className="
        flex
        min-h-screen
        min-h-dvh
        items-center
        justify-center
        bg-[var(--mb-bg)]
        px-6
      "
    >
      <div
        role="status"
        aria-live="polite"
        className="
          flex
          items-center
          gap-3
          rounded-2xl
          border
          border-[var(--mb-border)]
          bg-white
          px-5
          py-4
          text-sm
          font-medium
          text-[var(--mb-text-secondary)]
          shadow-[var(--mb-shadow-sm)]
        "
      >
        <span
          aria-hidden="true"
          className="
            h-2.5
            w-2.5
            animate-pulse
            rounded-full
            bg-[var(--mb-primary)]
          "
        />

        Preparing secure signup…
      </div>
    </main>
  );
}


export default function SignupLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <Suspense
      fallback={
        <SignupLoading />
      }
    >
      {children}
    </Suspense>
  );
}
