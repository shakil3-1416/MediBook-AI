"use client";

import AppointmentCalendar from "@/components/medibook-widget/appointment-calendar";
import ChatActionComponents, { type ChatActionLike } from "@/components/medibook-widget/chat-action-components";

import {
  FormEvent,
  useEffect,
  useRef,
  useState,
} from "react";

import { useRouter } from "next/navigation";

type User = {
  id?: string;
  email?: string;
  full_name?: string;
  name?: string;
  profile_image_url?: string | null;
};

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  sequence_no: number;
  edited_at?: string | null;
  actions?: ChatActionLike[];
};

type Conversation = {
  id: string;
  title: string;
};

type Appointment = {
  id?: string;
  confirmation_code?: string;
  status?: string;
  slot_date?: string;
  start_time?: string;
  appointment_date?: string;
  appointment_time?: string;
  doctor_name?: string;
  doctor?: {
    full_name?: string;
  };
};

function visitorId() {
  const key = "medibook_widget_visitor";

  let id = localStorage.getItem(key);

  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(key, id);
  }

  return id;
}



function extractMediBookActions(
  raw: string,
): ChatActionLike[] {
  const actions: ChatActionLike[] = [];

  for (
    const originalLine
    of raw.split(/\r?\n/)
  ) {
    let line =
      originalLine.trim();

    if (!line) {
      continue;
    }

    if (
      line.startsWith(
        "data:",
      )
    ) {
      line =
        line.slice(5).trim();
    }

    if (
      !line
      ||
      line === "[DONE]"
    ) {
      continue;
    }

    try {
      const item =
        JSON.parse(line);

      if (
        item?.type
          ===
          "actions"
        &&
        Array.isArray(
          item.actions,
        )
      ) {
        actions.push(
          ...item.actions,
        );
      }
    } catch {
      continue;
    }
  }

  return actions;
}


function decodeMediBookStream(raw: string): string {
  const source = raw.trim();

  if (!source) {
    return "";
  }

  const pieces: string[] = [];

  // First handle newline-delimited JSON / SSE-style lines.
  for (const originalLine of source.split(/\r?\n/)) {
    let line = originalLine.trim();

    if (!line) {
      continue;
    }

    if (line.startsWith("data:")) {
      line = line.slice(5).trim();
    }

    if (!line || line === "[DONE]") {
      continue;
    }

    try {
      const item = JSON.parse(line);

      if (
        item?.type === "text_delta" &&
        typeof item.delta === "string"
      ) {
        pieces.push(item.delta);
        continue;
      }

      if (
        item?.type === "text" &&
        typeof item.text === "string"
      ) {
        pieces.push(item.text);
        continue;
      }

      if (
        typeof item?.message === "string" &&
        item?.type !== "status"
      ) {
        pieces.push(item.message);
        continue;
      }

      if (
        typeof item?.response === "string"
      ) {
        pieces.push(item.response);
        continue;
      }

      if (
        typeof item?.answer === "string"
      ) {
        pieces.push(item.answer);
        continue;
      }

      if (
        typeof item?.content === "string"
      ) {
        pieces.push(item.content);
      }

    } catch {
      // Fall through to concatenated-object parser below.
    }
  }

  if (pieces.length > 0) {
    return pieces.join("").trim();
  }

  // Handle concatenated JSON objects:
  // {...}{...}{...}
  const objects: string[] = [];

  let start = -1;
  let depth = 0;
  let inString = false;
  let escaped = false;

  for (let i = 0; i < source.length; i += 1) {
    const char = source[i];

    if (inString) {
      if (escaped) {
        escaped = false;
        continue;
      }

      if (char === "\\") {
        escaped = true;
        continue;
      }

      if (char === '"') {
        inString = false;
      }

      continue;
    }

    if (char === '"') {
      inString = true;
      continue;
    }

    if (char === "{") {
      if (depth === 0) {
        start = i;
      }

      depth += 1;
      continue;
    }

    if (char === "}") {
      depth -= 1;

      if (
        depth === 0 &&
        start >= 0
      ) {
        objects.push(
          source.slice(start, i + 1),
        );

        start = -1;
      }
    }
  }

  for (const objectText of objects) {
    try {
      const item = JSON.parse(objectText);

      if (
        item?.type === "text_delta" &&
        typeof item.delta === "string"
      ) {
        pieces.push(item.delta);
        continue;
      }

      if (
        item?.type === "text" &&
        typeof item.text === "string"
      ) {
        pieces.push(item.text);
        continue;
      }

      if (
        typeof item?.message === "string" &&
        item?.type !== "status"
      ) {
        pieces.push(item.message);
        continue;
      }

      if (
        typeof item?.response === "string"
      ) {
        pieces.push(item.response);
        continue;
      }

      if (
        typeof item?.answer === "string"
      ) {
        pieces.push(item.answer);
        continue;
      }

      if (
        typeof item?.content === "string"
      ) {
        pieces.push(item.content);
      }

    } catch {
      // Ignore protocol fragments that cannot be decoded.
    }
  }

  if (pieces.length > 0) {
    return pieces.join("").trim();
  }

  // Normal non-stream JSON response.
  try {
    const parsed = JSON.parse(source);

    if (typeof parsed === "string") {
      return parsed;
    }

    return (
      parsed.message ??
      parsed.response ??
      parsed.answer ??
      parsed.content ??
      source
    );
  } catch {
    return source;
  }
}


function cleanStoredMessage(
  content: string,
): string {
  if (
    content.includes('"type":"text_delta"') ||
    content.includes('"type": "text_delta"') ||
    content.includes('"type":"status"') ||
    content.includes('"type": "status"')
  ) {
    return decodeMediBookStream(content);
  }

  return content;
}



function extractBackendConversationId(
  raw: string,
): string | null {
  const source = raw.trim();

  if (!source) {
    return null;
  }

  // NDJSON / SSE lines.
  for (const originalLine of source.split(/\r?\n/)) {
    let line = originalLine.trim();

    if (line.startsWith("data:")) {
      line = line.slice(5).trim();
    }

    if (!line || line === "[DONE]") {
      continue;
    }

    try {
      const item = JSON.parse(line);

      if (
        typeof item?.conversation_id === "string" &&
        item.conversation_id
      ) {
        return item.conversation_id;
      }
    } catch {
      // Continue with concatenated JSON parsing.
    }
  }

  // Concatenated JSON objects:
  // {...}{...}{...}
  let start = -1;
  let depth = 0;
  let inString = false;
  let escaped = false;

  for (let i = 0; i < source.length; i += 1) {
    const char = source[i];

    if (inString) {
      if (escaped) {
        escaped = false;
        continue;
      }

      if (char === "\\") {
        escaped = true;
        continue;
      }

      if (char === '"') {
        inString = false;
      }

      continue;
    }

    if (char === '"') {
      inString = true;
      continue;
    }

    if (char === "{") {
      if (depth === 0) {
        start = i;
      }

      depth += 1;
      continue;
    }

    if (char === "}") {
      depth -= 1;

      if (
        depth === 0 &&
        start >= 0
      ) {
        const objectText =
          source.slice(
            start,
            i + 1,
          );

        try {
          const item =
            JSON.parse(
              objectText,
            );

          if (
            typeof item?.conversation_id === "string" &&
            item.conversation_id
          ) {
            return item.conversation_id;
          }
        } catch {
          // Ignore malformed protocol fragments.
        }

        start = -1;
      }
    }
  }

  return null;
}


function backendConversationStorageKey(
  widgetConversationId: string,
): string {
  return `medibook_backend_conversation:${widgetConversationId}`;
}


export function MediBookWidget({
  hospitalSlug,
}: {
  hospitalSlug: string;
}) {
  const [appointmentCalendarOpen, setAppointmentCalendarOpen] =
    useState(false);

  const router = useRouter();

  const [visitor, setVisitor] = useState("");
  const [user, setUser] = useState<User | null>(null);

  const [conversations, setConversations] =
    useState<Conversation[]>([]);

  const [conversationId, setConversationId] =
    useState<string | null>(null);

  const [
    backendConversationId,
    setBackendConversationId,
  ] =
    useState<string | null>(null);

  const [messages, setMessages] =
    useState<Message[]>([]);

  const [appointments, setAppointments] =
    useState<Appointment[]>([]);

  const [view, setView] =
    useState<"chat" | "calendar">("chat");

  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);

  const [profileOpen, setProfileOpen] =
    useState(false);

  const [sidebarOpen, setSidebarOpen] =
    useState(false);

  const bottom =
    useRef<HTMLDivElement>(null);

  useEffect(() => {
    const id = visitorId();

    queueMicrotask(() => {
      setVisitor(id);
    });

    loadUser();
    loadConversations(id);
  }, []);

  useEffect(() => {
    bottom.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages]);

  async function loadUser() {
    try {
      const response = await fetch(
        "/api/auth/me",
        {
          cache: "no-store",
        },
      );

      if (!response.ok) {
        setUser(null);
        return;
      }

      const data = await response.json();

      setUser(data.user ?? data ?? null);
    } catch {
      setUser(null);
    }
  }

  function login() {
    router.push(
      `/login?next=${encodeURIComponent(
        `/widget/${hospitalSlug}`,
      )}`,
    );
  }

  async function loadConversations(
    id = visitor,
  ) {
    if (!id) return;

    const response = await fetch(
      `/api/widget/${hospitalSlug}/conversations?visitor_id=${encodeURIComponent(id)}`,
      {
        cache: "no-store",
      },
    );

    if (!response.ok) return;

    const data = await response.json();

    setConversations(
      Array.isArray(data) ? data : [],
    );
  }

  async function newChat() {
    if (!visitor) return null;

    const response = await fetch(
      `/api/widget/${hospitalSlug}/conversations`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          visitor_id: visitor,
        }),
      },
    );

    if (!response.ok) return null;

    const data = await response.json();

    setConversationId(data.id);
    setBackendConversationId(null);

    localStorage.removeItem(
      backendConversationStorageKey(data.id),
    );

    setMessages([]);
    setView("chat");
    setSidebarOpen(false);

    await loadConversations();

    return data.id as string;
  }

  async function openConversation(
    id: string,
  ) {
    const response = await fetch(
      `/api/widget/${hospitalSlug}/conversations/${id}?visitor_id=${encodeURIComponent(visitor)}`,
      {
        cache: "no-store",
      },
    );

    if (!response.ok) return;

    const data = await response.json();

    setConversationId(id);

    const storedBackendConversationId =
      localStorage.getItem(
        backendConversationStorageKey(id),
      );

    setBackendConversationId(
      storedBackendConversationId,
    );

    setMessages(data.messages ?? []);
    setView("chat");
    setSidebarOpen(false);
  }

  async function saveMessage(
    id: string,
    role: "user" | "assistant",
    content: string,
  ) {
    await fetch(
      `/api/widget/${hospitalSlug}/conversations/${id}/messages`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          visitor_id: visitor,
          role,
          content,
        }),
      },
    );
  }

  async function send(
    event: FormEvent,
  ) {
    event.preventDefault();

    const text = input.trim();

    if (!text || busy) return;

    if (!user) {
      login();
      return;
    }

    setBusy(true);
    setInput("");

    let cid = conversationId;

    if (!cid) {
      cid = await newChat();
    }

    if (!cid) {
      setBusy(false);
      return;
    }

    await saveMessage(
      cid,
      "user",
      text,
    );

    setMessages((current) => [
      ...current,
      {
        id: crypto.randomUUID(),
        role: "user",
        content: text,
        sequence_no: current.length + 1,
      },
    ]);

    try {
      const response = await fetch(
        `/api/widget/${hospitalSlug}/chat`,
        {
          method: "POST",
          headers: {
            "Content-Type":
              "application/json",
          },
          body: JSON.stringify({
            message: text,
            conversation_id:
                  backendConversationId ?? undefined,
          }),
        },
      );

      if (response.status === 401) {
        setUser(null);
        login();
        setBusy(false);
        return;
      }

      if (!response.ok) {
        throw new Error(
          `Chat HTTP ${response.status}`,
        );
      }

      const reader =
        response.body?.getReader();

      const decoder =
        new TextDecoder();

      let answer = "";

      if (reader) {
        while (true) {
          const chunk =
            await reader.read();

          if (chunk.done) break;

          answer += decoder.decode(
            chunk.value,
            {
              stream: true,
            },
          );
        }
      } else {
        answer =
          await response.text();
      }

      const backendId =
        extractBackendConversationId(
          answer,
        );

      if (backendId) {
        setBackendConversationId(
          backendId,
        );

        localStorage.setItem(
          backendConversationStorageKey(
            cid,
          ),
          backendId,
        );
      }

      const responseActions =
        extractMediBookActions(
          answer,
        );

      answer =
        decodeMediBookStream(
          answer,
        );

      if (answer) {
        await saveMessage(
          cid,
          "assistant",
          answer,
        );
      }

      await openConversation(cid);

      if (responseActions.length > 0) {
        setMessages((current) => {
          const updated = [...current];

          for (
            let index = updated.length - 1;
            index >= 0;
            index -= 1
          ) {
            if (
              updated[index].role ===
              "assistant"
            ) {
              updated[index] = {
                ...updated[index],
                actions: responseActions,
              };

              break;
            }
          }

          return updated;
        });
      }

      await loadConversations();
    } catch {
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content:
            "I could not reach the hospital appointment service. Please try again.",
          sequence_no:
            current.length + 1,
        },
      ]);
    }

    setBusy(false);
  }

  async function editMessage(
    message: Message,
  ) {
    if (!conversationId) return;

    const value =
      window.prompt(
        "Edit your message",
        message.content,
      );

    if (!value?.trim()) return;

    const response = await fetch(
      `/api/widget/${hospitalSlug}/conversations/${conversationId}/messages/${message.id}`,
      {
        method: "PATCH",
        headers: {
          "Content-Type":
            "application/json",
        },
        body: JSON.stringify({
          visitor_id: visitor,
          content: value.trim(),
        }),
      },
    );

    if (!response.ok) return;

    await openConversation(
      conversationId,
    );

    setInput(value.trim());
  }

  async function openCalendar() {
    if (!user) {
      login();
      return;
    }

    setAppointmentCalendarOpen(
      true,
    );

    setSidebarOpen(
      false,
    );
  }


  async function logout() {
    await fetch(
      "/api/auth/logout",
      {
        method: "POST",
      },
    );

    setUser(null);
    setProfileOpen(false);

    router.push("/login");
    router.refresh();
  }

  const displayName =
    user?.full_name ??
    user?.name ??
    user?.email ??
    "Patient";

  const initial =
    displayName
      .charAt(0)
      .toUpperCase();

  return (
    <div data-medibook-chat className="relative flex h-[100dvh] overflow-hidden bg-white">

      {sidebarOpen && (
        <button
          aria-label="Close sidebar"
          onClick={() =>
            setSidebarOpen(false)
          }
          className="absolute inset-0 z-30 bg-slate-950/20 md:hidden"
        />
      )}

      <aside
        className={`absolute inset-y-0 left-0 z-40 flex w-[285px] flex-col border-r border-brand-100 bg-brand-50/50 transition-transform md:relative md:translate-x-0 ${
          sidebarOpen
            ? "translate-x-0"
            : "-translate-x-full"
        }`}
      >
        <div className="flex h-16 items-center gap-3 px-4">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-700 font-bold text-white">
            M
          </div>

          <div>
            <div className="text-sm font-semibold">
              MediBook
            </div>

            <div className="text-[11px] text-slate-500">
              Hospital assistant
            </div>
          </div>
        </div>

        <div className="px-3">
          <button
            onClick={newChat}
            className="flex w-full items-center gap-3 rounded-xl border border-brand-200 bg-white px-3 py-2.5 text-left text-sm font-medium hover:bg-brand-50"
          >
            <span className="text-lg">
              +
            </span>
            New chat
          </button>

          <button
            onClick={openCalendar}
            className={`mt-2 flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm ${
              view === "calendar"
                ? "bg-brand-100 font-medium text-brand-800"
                : "text-slate-700 hover:bg-brand-50"
            }`}
          >
            <span>▣</span>
            My appointments
          </button>
        </div>

        <div className="mt-6 px-5 text-[11px] font-semibold uppercase tracking-widest text-slate-400">
          Previous chats
        </div>

        <div className="mt-2 min-h-0 flex-1 overflow-y-auto px-2">
          {conversations.map(
            (conversation) => (
              <button
                key={conversation.id}
                onClick={() =>
                  openConversation(
                    conversation.id,
                  )
                }
                className={`mb-1 block w-full truncate rounded-lg px-3 py-2.5 text-left text-sm ${
                  conversation.id ===
                    conversationId &&
                  view === "chat"
                    ? "bg-brand-100 text-brand-900"
                    : "text-slate-600 hover:bg-brand-50"
                }`}
              >
                {conversation.title ||
                  "New conversation"}
              </button>
            ),
          )}
        </div>

        <div className="relative border-t border-brand-100 p-3">
          {user ? (
            <>
              <button
                onClick={() =>
                  setProfileOpen(
                    (open) => !open,
                  )
                }
                className="flex w-full items-center gap-3 rounded-xl p-2 text-left hover:bg-brand-100"
              >
                {user.profile_image_url ? (
                  <img
                    src={user.profile_image_url}
                    alt=""
                    className="h-9 w-9 shrink-0 rounded-full object-cover"
                  />
                ) : (
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-brand-700 text-sm font-semibold text-white">
                    {initial || "P"}
                  </div>
                )}

                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm font-medium">
                    {displayName}
                  </div>

                  <div className="truncate text-[11px] text-slate-500">
                    {user.email}
                  </div>
                </div>

                <span className="text-slate-400">
                  ⋯
                </span>
              </button>

              {profileOpen && (
                <div className="absolute bottom-[68px] left-3 right-3 rounded-2xl border border-brand-100 bg-white p-1 shadow-xl">
                  <button
                    onClick={() =>
                      router.push(
                        `/profile?returnTo=/widget/${hospitalSlug}`,
                      )
                    }
                    className="block w-full rounded-xl px-3 py-2.5 text-left text-sm hover:bg-brand-50"
                  >
                    My profile
                  </button>

                  <button
                    onClick={() => setAppointmentCalendarOpen(true)}
                    className="block w-full rounded-xl px-3 py-2.5 text-left text-sm hover:bg-brand-50"
                  >
                    My appointments
                  </button>

                  <button
                    onClick={logout}
                    className="block w-full rounded-xl px-3 py-2.5 text-left text-sm font-medium text-brand-700 hover:bg-brand-50"
                  >
                    Sign out
                  </button>
                </div>
              )}
            </>
          ) : (
            <button
              onClick={login}
              className="w-full rounded-xl bg-brand-700 px-4 py-3 text-sm font-semibold text-white hover:bg-brand-800"
            >
              Sign in
            </button>
          )}
        </div>
      </aside>

      <main className="flex min-w-0 flex-1 flex-col bg-white">
        <header className="flex h-16 shrink-0 items-center justify-between border-b border-brand-100 px-4 md:px-6">
          <div className="flex items-center gap-3">
            <button
              onClick={() =>
                setSidebarOpen(true)
              }
              className="flex h-9 w-9 items-center justify-center rounded-xl border border-brand-100 md:hidden"
            >
              ☰
            </button>

            <div>
              <div className="text-sm font-semibold">
                MediBook Assistant
              </div>

              <div className="text-[11px] text-slate-500">
                Your hospital appointment assistant
              </div>
            </div>
          </div>

          <div className="rounded-full bg-brand-50 px-3 py-1.5 text-[11px] font-medium text-brand-700">
            {hospitalSlug}
          </div>
        </header>

        {view === "chat" ? (
          <>
            <section className="flex-1 overflow-y-auto">
              <div className="mx-auto flex min-h-full max-w-3xl flex-col px-5">

                {messages.length === 0 ? (
                  <div className="flex flex-1 flex-col items-center justify-center py-14 text-center">

                    <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-700 text-xl font-bold text-white shadow-lg shadow-brand-200">
                      M
                    </div>

                    <h1 className="mt-6 text-3xl font-semibold tracking-tight">
                      What can I help you with today?
                    </h1>

                    <p className="mt-3 max-w-xl text-sm leading-6 text-slate-500">
                      Tell me what you need help with.
                      I’ll guide you through finding the right care
                      and managing your appointment.
                    </p>

                    <div className="mt-8 grid w-full max-w-2xl gap-3 sm:grid-cols-2">
                      <div className="mt-8 flex flex-col items-center">
                        <div className="relative flex h-16 w-16 items-center justify-center">
                          <div className="absolute inset-0 rounded-2xl bg-brand-500/10 blur-xl" />

                          <div className="relative flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-600 to-brand-500 text-lg font-semibold text-white shadow-lg shadow-brand-500/20">
                            M
                          </div>
                        </div>

                        <div className="mt-5 flex items-center gap-2 text-xs font-medium text-slate-400">
                          <span className="relative flex h-2 w-2">
                            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-brand-400 opacity-50" />
                            <span className="relative inline-flex h-2 w-2 rounded-full bg-brand-500" />
                          </span>

                          Connected to this hospital
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-6 py-8">
                    {messages.map(
                      (message) => (
                        <div
                          key={message.id}
                          className={`flex ${
                            message.role ===
                            "user"
                              ? "justify-end"
                              : "justify-start"
                          }`}
                        >
                          <div
                            className={`max-w-[88%] ${
                              message.role ===
                              "assistant"
                                ? "flex gap-3"
                                : ""
                            }`}
                          >
                            {message.role ===
                              "assistant" && (
                              <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-brand-700 text-xs font-bold text-white">
                                M
                              </div>
                            )}

                            <div>
                              <div
                                className={
                                  message.role ===
                                  "user"
                                    ? "rounded-2xl rounded-br-md bg-brand-700 px-4 py-3 text-sm leading-7 text-white"
                                    : "whitespace-pre-wrap break-words px-1 py-1 text-sm leading-7 text-slate-800"
                                }
                              >
                                {
                                  cleanStoredMessage(
                                    message.content,
                                  )
                                }
                              </div>

                              {message.role === "assistant" ? (
                                <ChatActionComponents
                                  actions={message.actions}
                                />
                              ) : null}

                              {message.role ===
                                "user" && (
                                <button
                                  onClick={() =>
                                    editMessage(
                                      message,
                                    )
                                  }
                                  className="mt-1 px-2 text-[11px] text-slate-400 hover:text-brand-700"
                                >
                                  Edit
                                  {message.edited_at
                                    ? " · edited"
                                    : ""}
                                </button>
                              )}
                            </div>
                          </div>
                        </div>
                      ),
                    )}

                    <div ref={bottom} />
                  </div>
                )}
              </div>
            </section>

            <div className="shrink-0 bg-white px-4 pb-5 pt-2">
              <form
                onSubmit={send}
                className="mx-auto max-w-3xl"
              >
                <div className="rounded-[24px] border border-brand-200 bg-white p-2 shadow-[0_8px_35px_rgba(124,58,237,0.10)] focus-within:border-brand-400 focus-within:ring-4 focus-within:ring-brand-100">
                  <textarea
                    value={input}
                    onChange={(event) =>
                      setInput(
                        event.target.value,
                      )
                    }
                    onKeyDown={(event) => {
                      if (
                        event.key ===
                          "Enter" &&
                        !event.shiftKey
                      ) {
                        event.preventDefault();
                        event.currentTarget.form?.requestSubmit();
                      }
                    }}
                    rows={1}
                    placeholder="Message MediBook..."
                    className="max-h-36 min-h-12 w-full resize-none bg-transparent px-3 py-3 text-sm leading-6 outline-none"
                  />

                  <div className="flex items-center justify-between px-2 pb-1">
                    <span className="text-[10px] text-slate-400">
                      Connected to this hospital&apos;s appointment system
                    </span>

                    <button
                      disabled={
                        busy ||
                        !input.trim()
                      }
                      className="flex h-9 w-9 items-center justify-center rounded-full bg-brand-700 font-semibold text-white hover:bg-brand-800 disabled:opacity-30"
                    >
                      {busy ? "…" : "↑"}
                    </button>
                  </div>
                </div>
              </form>
            </div>
          </>
        ) : (
          <section className="flex-1 overflow-y-auto bg-brand-50/30 p-5 md:p-8">
            <div className="mx-auto max-w-5xl">

              <div className="flex flex-wrap items-end justify-between gap-4">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-widest text-brand-600">
                    Appointment calendar
                  </p>

                  <h1 className="mt-2 text-3xl font-semibold tracking-tight">
                    My appointments
                  </h1>

                  <p className="mt-2 text-sm text-slate-500">
                    Review your appointments here. To make changes, tell MediBook in the conversation.
                  </p>
                </div>

                <button
                  onClick={() =>
                    setView("chat")
                  }
                  className="rounded-xl border border-brand-200 bg-white px-4 py-2.5 text-sm font-medium text-brand-700 hover:bg-brand-50"
                >
                  Back to chat
                </button>
              </div>

              <div className="mt-8 space-y-4">
                {appointments.length === 0 ? (
                  <div className="rounded-3xl border border-dashed border-brand-200 bg-white px-6 py-16 text-center">
                    <div className="text-lg font-medium">
                      No appointments yet
                    </div>

                    <p className="mt-2 text-sm text-slate-500">
                      Ask MediBook to find a doctor and book your appointment.
                    </p>

                    <button
                      onClick={() =>
                        setView("chat")
                      }
                      className="mt-5 rounded-xl bg-brand-700 px-4 py-2.5 text-sm font-medium text-white hover:bg-brand-800"
                    >
                      Start chatting
                    </button>
                  </div>
                ) : (
                  appointments.map(
                    (
                      appointment,
                      index,
                    ) => {
                      const doctor =
                        appointment.doctor
                          ?.full_name ??
                        appointment.doctor_name ??
                        "Doctor";

                      const date =
                        appointment.slot_date ??
                        appointment.appointment_date ??
                        "";

                      const time =
                        appointment.start_time ??
                        appointment.appointment_time ??
                        "";

                      const cancelled =
                        appointment.status ===
                        "cancelled";

                      return (
                        <article
                          key={
                            appointment.confirmation_code ??
                            appointment.id ??
                            index
                          }
                          className="rounded-3xl border border-brand-100 bg-white p-6 shadow-sm"
                        >
                          <div className="flex flex-col justify-between gap-5 md:flex-row md:items-center">

                            <div className="flex items-start gap-4">
                              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-100 font-semibold text-brand-700">
                                Dr
                              </div>

                              <div>
                                <h2 className="font-semibold">
                                  {doctor}
                                </h2>

                                <p className="mt-1 text-sm text-slate-500">
                                  {date}
                                  {date && time
                                    ? " · "
                                    : ""}
                                  {time}
                                </p>

                                {appointment.confirmation_code && (
                                  <p className="mt-2 text-xs text-slate-400">
                                    Booking ID:{" "}
                                    {
                                      appointment.confirmation_code
                                    }
                                  </p>
                                )}

                                <span
                                  className={`mt-3 inline-flex rounded-full px-3 py-1 text-xs font-medium ${
                                    cancelled
                                      ? "bg-slate-100 text-slate-500"
                                      : "bg-brand-50 text-brand-700"
                                  }`}
                                >
                                  {appointment.status ??
                                    "confirmed"}
                                </span>
                              </div>
                            </div>


                          </div>
                        </article>
                      );
                    },
                  )
                )}
              </div>
            </div>
          </section>
        )}

      <AppointmentCalendar
        hospitalSlug={hospitalSlug}
        open={appointmentCalendarOpen}
        onClose={() => setAppointmentCalendarOpen(false)}
      />

    </main>
    </div>
  );
}
