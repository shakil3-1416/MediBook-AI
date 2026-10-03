"use client";

import { useEffect, useRef, useState } from "react";

const numberFormat = new Intl.NumberFormat("en");

function reducedMotion() {
  return typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

/* Counts up to the value; screen readers get the final number only. */
export function AnimatedNumber({ value, className }: { value: number; className?: string }) {
  const [shown, setShown] = useState(0);
  const fromRef = useRef(0);
  useEffect(() => {
    const from = fromRef.current;
    const duration = reducedMotion() ? 0 : 700;
    const start = performance.now();
    let frame = 0;
    function tick(now: number) {
      const progress = duration === 0 ? 1 : Math.min(1, (now - start) / duration);
      setShown(Math.round(from + (value - from) * (1 - Math.pow(1 - progress, 3))));
      if (progress < 1) {
        frame = requestAnimationFrame(tick);
      } else {
        fromRef.current = value;
      }
    }
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [value]);
  return (
    <span className={className}>
      <span aria-hidden="true">{numberFormat.format(shown)}</span>
      <span className="sr-only">{numberFormat.format(value)}</span>
    </span>
  );
}

function GrowBar({ percent, className }: { percent: number; className: string }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (reducedMotion() || ref.current === null) return;
    ref.current.animate([{ transform: "scaleX(0)" }, { transform: "scaleX(1)" }], {
      duration: 800,
      easing: "cubic-bezier(0.2, 0.8, 0.2, 1)",
    });
  }, [percent]);
  return <div ref={ref} className={`h-full origin-left rounded-full ${className}`} style={{ width: `${Math.max(percent, percent > 0 ? 2 : 0)}%` }} />;
}

export function BarList({ items, unit, empty }: { items: { label: string; value: number }[]; unit: string; empty: string }) {
  const max = Math.max(1, ...items.map((item) => item.value));
  if (items.every((item) => item.value === 0)) {
    return <p className="py-6 text-center text-sm text-slate-600">{empty}</p>;
  }
  return (
    <ul className="space-y-4">
      {items.map((item) => (
        <li key={item.label}>
          <div className="mb-1.5 flex items-baseline justify-between gap-3 text-sm">
            <span className="truncate font-medium text-slate-800">{item.label}</span>
            <span className="shrink-0 tabular-nums text-slate-600">
              {numberFormat.format(item.value)} {unit}
            </span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-slate-100">
            <GrowBar percent={(item.value / max) * 100} className="bg-gradient-to-r from-brand-400 to-brand-600" />
          </div>
        </li>
      ))}
    </ul>
  );
}

export function Donut({ segments, centerLabel, centerValue }: {
  segments: { label: string; value: number; color: string; swatch: string }[];
  centerLabel: string;
  centerValue: number;
}) {
  const total = segments.reduce((sum, segment) => sum + segment.value, 0);
  const radius = 42;
  const circumference = 2 * Math.PI * radius;
  const arcs = segments.map((segment, index) => {
    const share = (value: number) => (total === 0 ? 0 : (value / total) * circumference);
    const start = segments.slice(0, index).reduce((sum, previous) => sum + share(previous.value), 0);
    return { ...segment, length: share(segment.value), start };
  });
  return (
    <div className="flex items-center gap-6">
      <div className="relative size-32 shrink-0">
        <svg viewBox="0 0 100 100" className="size-32 -rotate-90" aria-hidden="true">
          <circle cx="50" cy="50" r={radius} fill="none" stroke="currentColor" strokeWidth="12" className="text-slate-100" />
          {arcs.map((arc) => (
            <circle
              key={arc.label}
              cx="50"
              cy="50"
              r={radius}
              fill="none"
              stroke={arc.color}
              strokeWidth="12"
              strokeDasharray={`${arc.length} ${circumference - arc.length}`}
              strokeDashoffset={-arc.start}
              className="transition-[stroke-dasharray] duration-700"
            />
          ))}
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-semibold tabular-nums text-slate-900">{numberFormat.format(centerValue)}</span>
          <span className="text-xs text-slate-600">{centerLabel}</span>
        </div>
      </div>
      <ul className="space-y-2 text-sm">
        {segments.map((segment) => (
          <li key={segment.label} className="flex items-center gap-2">
            <span aria-hidden="true" className={`size-2.5 rounded-full ${segment.swatch}`} />
            <span className="text-slate-700">{segment.label}</span>
            <span className="ml-auto pl-4 font-semibold tabular-nums text-slate-900">{numberFormat.format(segment.value)}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
