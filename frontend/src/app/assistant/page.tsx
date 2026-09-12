import {
  Suspense,
} from "react";

import AssistantClient from "./assistant-client";


function AssistantLoading() {
  return (
    <div className="flex min-h-[70vh] flex-col overflow-hidden rounded-3xl border border-slate-200 bg-white">
      <div className="border-b border-slate-100 px-5 py-4">
        <div className="h-5 w-36 animate-pulse rounded bg-slate-200" />

        <div className="mt-2 h-3 w-52 animate-pulse rounded bg-slate-100" />
      </div>

      <div className="flex flex-1 flex-col justify-end gap-4 p-5">
        <div className="h-16 w-2/3 animate-pulse rounded-2xl bg-slate-100" />

        <div className="ml-auto h-12 w-1/2 animate-pulse rounded-2xl bg-slate-100" />

        <div className="h-14 w-3/5 animate-pulse rounded-2xl bg-slate-100" />
      </div>

      <div className="border-t border-slate-100 p-4">
        <div className="h-12 animate-pulse rounded-2xl bg-slate-100" />
      </div>
    </div>
  );
}


export default function AssistantPage() {
  return (
    <Suspense
      fallback={
        <AssistantLoading />
      }
    >
      <AssistantClient />
    </Suspense>
  );
}
