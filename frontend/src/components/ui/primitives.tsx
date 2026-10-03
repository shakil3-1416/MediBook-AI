"use client";

import clsx from "clsx";
import Link from "next/link";
import {
  useId,
  type ButtonHTMLAttributes,
  type InputHTMLAttributes,
  type ReactNode,
  type SelectHTMLAttributes,
  type TextareaHTMLAttributes,
} from "react";

/* Shared building blocks for the redesigned screens (faded green and white). */

export type Tone = "green" | "amber" | "red" | "blue" | "neutral";

const toneClasses: Record<Tone, string> = {
  green: "bg-brand-50 text-brand-800 ring-brand-200",
  amber: "bg-amber-50 text-amber-800 ring-amber-200",
  red: "bg-red-50 text-red-800 ring-red-200",
  blue: "bg-sky-50 text-sky-800 ring-sky-200",
  neutral: "bg-slate-100 text-slate-700 ring-slate-200",
};

export function Badge({ tone = "neutral", children }: { tone?: Tone; children: ReactNode }) {
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset",
        toneClasses[tone],
      )}
    >
      {children}
    </span>
  );
}

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";

const buttonBase =
  "inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-700 disabled:cursor-not-allowed disabled:opacity-60";

const buttonVariants: Record<ButtonVariant, string> = {
  primary: "bg-brand-600 text-white hover:bg-brand-700",
  secondary: "border border-[#869489] bg-white text-slate-800 hover:bg-slate-50",
  ghost: "text-slate-700 hover:bg-slate-100 hover:text-slate-900",
  danger: "bg-red-700 text-white hover:bg-red-800",
};

const buttonSizes = {
  sm: "h-8 px-3 text-sm",
  md: "h-10 px-4 text-sm",
} as const;

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  size?: keyof typeof buttonSizes;
  loading?: boolean;
};

function Spinner() {
  return (
    <span
      aria-hidden="true"
      className="size-4 animate-spin rounded-full border-2 border-current border-r-transparent"
    />
  );
}

export function Button({
  variant = "primary",
  size = "md",
  loading = false,
  className,
  children,
  disabled,
  type = "button",
  ...rest
}: ButtonProps) {
  return (
    <button
      type={type}
      className={clsx(buttonBase, buttonVariants[variant], buttonSizes[size], className)}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...rest}
    >
      {loading ? <Spinner /> : null}
      {children}
    </button>
  );
}

export function ButtonLink({
  href,
  variant = "secondary",
  size = "md",
  className,
  children,
}: {
  href: string;
  variant?: ButtonVariant;
  size?: keyof typeof buttonSizes;
  className?: string;
  children: ReactNode;
}) {
  return (
    <Link href={href} className={clsx(buttonBase, buttonVariants[variant], buttonSizes[size], className)}>
      {children}
    </Link>
  );
}

export function Card({ className, children }: { className?: string; children: ReactNode }) {
  return (
    <section
      className={clsx(
        "rounded-2xl border border-slate-200/80 bg-white shadow-[0_1px_2px_rgba(16,40,28,0.04),0_12px_32px_-16px_rgba(16,40,28,0.14)]",
        className,
      )}
    >
      {children}
    </section>
  );
}

export function CardHeader({
  title,
  description,
  action,
}: {
  title: ReactNode;
  description?: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-start justify-between gap-3 border-b border-slate-200 px-5 py-4">
      <div className="min-w-0">
        <h2 className="text-base font-semibold text-slate-900">{title}</h2>
        {description ? <p className="mt-0.5 text-sm text-slate-600">{description}</p> : null}
      </div>
      {action}
    </div>
  );
}

export function StatCard({
  label,
  value,
  hint,
  tone = "neutral",
}: {
  label: string;
  value: ReactNode;
  hint?: ReactNode;
  tone?: "neutral" | "warning";
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white px-5 py-4 shadow-[0_1px_2px_rgba(15,40,28,0.05)]">
      <p className="text-sm font-medium text-slate-600">{label}</p>
      <p className="mt-2 text-2xl font-semibold tracking-tight text-slate-900 tabular-nums">{value}</p>
      {hint ? (
        <p className={clsx("mt-1 text-xs", tone === "warning" ? "font-medium text-amber-800" : "text-slate-600")}>
          {hint}
        </p>
      ) : null}
    </div>
  );
}

export function Alert({
  tone = "error",
  title,
  children,
}: {
  tone?: "error" | "success" | "info";
  title?: string;
  children: ReactNode;
}) {
  const styles = {
    error: "border-red-200 bg-red-50 text-red-900",
    success: "border-brand-200 bg-brand-50 text-brand-900",
    info: "border-sky-200 bg-sky-50 text-sky-900",
  }[tone];
  return (
    <div role={tone === "error" ? "alert" : "status"} className={clsx("rounded-lg border px-4 py-3 text-sm", styles)}>
      {title ? <p className="font-semibold">{title}</p> : null}
      <div className={title ? "mt-1" : undefined}>{children}</div>
    </div>
  );
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 px-6 py-12 text-center">
      <p className="text-sm font-semibold text-slate-900">{title}</p>
      {description ? <p className="max-w-sm text-sm text-slate-600">{description}</p> : null}
      {action ? <div className="mt-2">{action}</div> : null}
    </div>
  );
}

export function SkeletonBlock({ className }: { className?: string }) {
  return <div aria-hidden="true" className={clsx("animate-pulse rounded-md bg-slate-200/70", className)} />;
}

const controlClass =
  "block w-full rounded-lg border border-[#869489] bg-white px-3 py-2 text-sm text-slate-900 shadow-sm placeholder:text-slate-500 focus:border-brand-600 focus:outline-2 focus:outline-offset-0 focus:outline-brand-600/30 disabled:bg-slate-50";

type FieldMeta = { label: string; hint?: string; error?: string | null };

function FieldShell({ id, label, hint, error, children }: FieldMeta & { id: string; children: ReactNode }) {
  return (
    <div className="space-y-1.5">
      <label htmlFor={id} className="block text-sm font-medium text-slate-800">
        {label}
      </label>
      {children}
      {error ? (
        <p id={`${id}-error`} className="text-xs font-medium text-red-700">
          {error}
        </p>
      ) : hint ? (
        <p id={`${id}-hint`} className="text-xs text-slate-600">
          {hint}
        </p>
      ) : null}
    </div>
  );
}

function describedBy(id: string, hint?: string, error?: string | null) {
  if (error) return `${id}-error`;
  if (hint) return `${id}-hint`;
  return undefined;
}

export function InputField({
  label,
  hint,
  error,
  className,
  ...rest
}: FieldMeta & InputHTMLAttributes<HTMLInputElement>) {
  const id = useId();
  return (
    <FieldShell id={id} label={label} hint={hint} error={error}>
      <input
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy(id, hint, error)}
        className={clsx(controlClass, className)}
        {...rest}
      />
    </FieldShell>
  );
}

export function SelectField({
  label,
  hint,
  error,
  className,
  children,
  ...rest
}: FieldMeta & SelectHTMLAttributes<HTMLSelectElement>) {
  const id = useId();
  return (
    <FieldShell id={id} label={label} hint={hint} error={error}>
      <select
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy(id, hint, error)}
        className={clsx(controlClass, "pr-8", className)}
        {...rest}
      >
        {children}
      </select>
    </FieldShell>
  );
}

export function TextareaField({
  label,
  hint,
  error,
  className,
  ...rest
}: FieldMeta & TextareaHTMLAttributes<HTMLTextAreaElement>) {
  const id = useId();
  return (
    <FieldShell id={id} label={label} hint={hint} error={error}>
      <textarea
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy(id, hint, error)}
        className={clsx(controlClass, className)}
        {...rest}
      />
    </FieldShell>
  );
}

export function CheckboxField({
  label,
  hint,
  ...rest
}: { label: string; hint?: string } & InputHTMLAttributes<HTMLInputElement>) {
  const id = useId();
  return (
    <div className="flex items-start gap-3">
      <input
        id={id}
        type="checkbox"
        className="mt-0.5 size-4 rounded border-[#869489] accent-brand-600 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-700"
        {...rest}
      />
      <div>
        <label htmlFor={id} className="text-sm font-medium text-slate-800">
          {label}
        </label>
        {hint ? <p className="text-xs text-slate-600">{hint}</p> : null}
      </div>
    </div>
  );
}
