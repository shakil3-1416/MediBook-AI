"use client";

import {
  Check,
  ChevronDown,
  Search,
  X,
} from "lucide-react";

import {
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";


export type SearchOption = {
  name: string;
  count?: number;
};


export function SearchableCombobox({
  label,
  value,
  options,
  placeholder,
  disabled = false,
  onChange,
}: {
  label: string;
  value: string;
  options: SearchOption[];
  placeholder: string;
  disabled?: boolean;
  onChange: (
    value: string,
  ) => void;
}) {

  const [
    text,
    setText,
  ] = useState(value);

  const [
    open,
    setOpen,
  ] = useState(false);

  const root =
    useRef<HTMLDivElement>(
      null,
    );


  useEffect(
    () => {
      queueMicrotask(() => {
        setText(value);
      });
    },
    [value],
  );


  useEffect(
    () => {
      function onDocumentClick(
        event: MouseEvent,
      ) {
        if (
          root.current &&
          !root.current.contains(
            event.target as Node,
          )
        ) {
          setOpen(false);
        }
      }

      document.addEventListener(
        "mousedown",
        onDocumentClick,
      );

      return () => {
        document.removeEventListener(
          "mousedown",
          onDocumentClick,
        );
      };
    },
    [],
  );


  const suggestions =
    useMemo(
      () => {
        const query =
          text
            .trim()
            .toLowerCase();

        const filtered =
          query
            ? options.filter(
                option =>
                  option.name
                    .toLowerCase()
                    .includes(query),
              )
            : options;

        return filtered.slice(
          0,
          15,
        );
      },
      [
        text,
        options,
      ],
    );


  function choose(
    next: string,
  ) {
    setText(next);
    onChange(next);
    setOpen(false);
  }


  return (
    <div
      ref={root}
      className="relative"
    >

      <label className="mb-1.5 block text-xs font-semibold text-slate-600">
        {label}
      </label>


      <div className="relative">

        <Search
          size={15}
          className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
        />


        <input
          value={text}
          disabled={disabled}
          placeholder={placeholder}
          autoComplete="off"
          onFocus={
            () => {
              if (!disabled) {
                setOpen(true);
              }
            }
          }
          onChange={
            event => {
              const next =
                event.target.value;

              setText(next);
              setOpen(true);

              /*
               * Only clear the selected filter while typing.
               * Server filtering starts after the user chooses
               * an actual suggestion.
               */
              if (
                value &&
                next !== value
              ) {
                onChange("");
              }
            }
          }
          className="w-full rounded-xl border border-slate-200 bg-white py-2.5 pl-9 pr-16 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100 disabled:cursor-not-allowed disabled:bg-slate-50 disabled:text-slate-400"
        />


        <div className="absolute right-2 top-1/2 flex -translate-y-1/2 items-center">

          {text && !disabled && (
            <button
              type="button"
              aria-label={`Clear ${label}`}
              onClick={
                () => choose("")
              }
              className="rounded-md p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
            >
              <X size={14} />
            </button>
          )}

          <ChevronDown
            size={15}
            className="ml-1 text-slate-400"
          />

        </div>

      </div>


      {open &&
      !disabled && (

        <div className="absolute z-50 mt-2 max-h-72 w-full overflow-y-auto rounded-2xl border border-slate-200 bg-white p-1.5 shadow-xl shadow-slate-200/60">

          <button
            type="button"
            onClick={
              () => choose("")
            }
            className="flex w-full items-center justify-between rounded-xl px-3 py-2.5 text-left text-sm text-slate-600 hover:bg-slate-50"
          >
            <span>
              All {label.toLowerCase()}
            </span>
          </button>


          {suggestions.map(
            option => (
              <button
                key={option.name}
                type="button"
                onClick={
                  () =>
                    choose(
                      option.name,
                    )
                }
                className={[
                  "flex w-full items-center justify-between rounded-xl px-3 py-2.5 text-left text-sm transition",

                  value ===
                  option.name
                    ? "bg-emerald-50 font-semibold text-emerald-800"
                    : "text-slate-700 hover:bg-slate-50",
                ].join(" ")}
              >

                <span className="flex min-w-0 items-center gap-2">

                  {value ===
                  option.name ? (
                    <Check
                      size={14}
                      className="shrink-0 text-emerald-600"
                    />
                  ) : (
                    <span className="w-3.5" />
                  )}

                  <span className="truncate">
                    {option.name}
                  </span>

                </span>


                {typeof option.count ===
                "number" && (
                  <span className="ml-3 shrink-0 rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-semibold text-slate-500">
                    {option.count}
                  </span>
                )}

              </button>
            ),
          )}


          {suggestions.length ===
          0 && (
            <div className="px-3 py-5 text-center text-sm text-slate-500">
              No matching suggestions
            </div>
          )}

        </div>

      )}

    </div>
  );
}
