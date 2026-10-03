"use client";

import {
  CalendarClock,
  Check,
  Clock3,
  RotateCcw,
  X,
} from "lucide-react";

import type {
  ChatAction,
} from "@/types/api";


type Props = {
  actions: ChatAction[];

  disabled?: boolean;

  onAction:
    (action: ChatAction) => void;
};


function iconFor(
  action: ChatAction
) {
  switch (
    action.type
  ) {
    case "book_slot":
      return (
        <Clock3
          size={15}
        />
      );

    case "confirm":
      return (
        <Check
          size={15}
        />
      );

    case "cancel":
      return (
        <X
          size={15}
        />
      );

    case "reschedule":
      return (
        <RotateCcw
          size={15}
        />
      );

    default:
      return (
        <CalendarClock
          size={15}
        />
      );
  }
}


export function ChatActions({
  actions,
  disabled,
  onAction,
}: Props) {
  if (!actions.length) {
    return null;
  }

  return (
    <div className="mt-3 flex flex-wrap gap-2">
      {actions.map(
        (action) => {
          const classes =
            action.variant ===
            "danger"
              ? "border-red-200 bg-red-50 text-red-700 hover:bg-red-100"
              : action.variant ===
                  "primary"
                ? "border-brand-600 bg-brand-600 text-white hover:bg-brand-700"
                : "border-slate-200 bg-white text-slate-700 hover:bg-slate-50";

          return (
            <button
              key={action.id}
              type="button"
              disabled={
                disabled
              }
              onClick={() =>
                onAction(
                  action
                )
              }
              className={[
                "inline-flex items-center gap-2 rounded-xl border px-3.5 py-2 text-sm font-semibold transition",
                classes,
                disabled
                  ? "cursor-not-allowed opacity-50"
                  : "",
              ].join(" ")}
            >
              {iconFor(
                action
              )}

              {
                action.label
              }
            </button>
          );
        }
      )}
    </div>
  );
}
