export default function DoctorsLoading() {
  return (
    <div className="animate-pulse">
      <div className="h-4 w-32 rounded bg-slate-100" />

      <div className="mt-3 h-9 w-64 rounded-lg bg-slate-200" />

      <div className="mt-3 h-4 w-96 max-w-full rounded bg-slate-100" />

      <div className="mt-7 h-20 rounded-2xl border border-slate-100 bg-white" />

      <div className="mt-6 grid gap-4 xl:grid-cols-2">
        {[1, 2, 3, 4].map(
          (item) => (
            <div
              key={item}
              className="h-52 rounded-2xl border border-slate-100 bg-white"
            />
          ),
        )}
      </div>
    </div>
  );
}
