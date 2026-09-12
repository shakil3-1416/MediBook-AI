import { NextRequest, NextResponse } from "next/server";

export async function GET(
  request: NextRequest,
  context: { params: Promise<{ hospitalSlug: string }> },
) {
  const { hospitalSlug } = await context.params;
  const origin = request.nextUrl.origin;
  const slug = encodeURIComponent(hospitalSlug);
  const embedUrl = `${origin}/embed/${slug}`;
  const id = `medibook-${slug}`;

  const script = `(() => {
  if (document.getElementById(${JSON.stringify(id)})) return;

  const root = document.createElement("div");
  root.id = ${JSON.stringify(id)};
  root.setAttribute("data-medibook-installer", "true");

  const frame = document.createElement("iframe");
  frame.src = ${JSON.stringify(embedUrl)};
  frame.title = "MediBook appointment assistant";
  frame.loading = "lazy";
  frame.style.cssText = "position:fixed;right:20px;bottom:86px;width:min(420px,calc(100vw - 24px));height:min(720px,calc(100vh - 116px));border:1px solid rgba(67,31,122,.14);border-radius:22px;background:#fff;box-shadow:0 24px 70px rgba(39,25,68,.22);z-index:2147483647;display:none";

  const button = document.createElement("button");
  button.type = "button";
  button.textContent = "Book appointment";
  button.setAttribute("aria-expanded", "false");
  button.setAttribute("aria-label", "Open MediBook appointment assistant");
  button.style.cssText = "position:fixed;right:20px;bottom:20px;z-index:2147483647;border:0;border-radius:999px;padding:14px 20px;background:linear-gradient(135deg,#7430df,#8d4cf6);color:#fff;font:650 14px Inter,system-ui,sans-serif;cursor:pointer;box-shadow:0 14px 36px rgba(80,34,152,.28)";

  let open = false;

  button.addEventListener("click", () => {
    open = !open;
    frame.style.display = open ? "block" : "none";
    button.textContent = open ? "Close MediBook" : "Book appointment";
    button.setAttribute("aria-expanded", open ? "true" : "false");
  });

  root.appendChild(frame);
  root.appendChild(button);
  document.body.appendChild(root);
})();`;

  return new NextResponse(script, {
    headers: {
      "Content-Type": "application/javascript; charset=utf-8",
      "Cache-Control": "public, max-age=300",
      "X-Content-Type-Options": "nosniff",
    },
  });
}
