"use client";

import {
  ArrowUp,
  Bot,
  LoaderCircle,
  Plus,
  Square,
  UserRound,
} from "lucide-react";

import {
  FormEvent,
  useEffect,
  useRef,
  useState,
} from "react";

import {
  useSearchParams,
} from "next/navigation";

import {
  ChatActions,
} from "@/components/chat/chat-actions";

import {
  streamChat,
} from "@/lib/chat/stream";

import type {
  ChatAction,
} from "@/types/api";

import {
  useChatStore,
} from "@/store/chat-store";


const quickActions = [
  "Find me a cardiologist in Dhanmondi",
  "Show Dr. Farhana Ahmed's availability tomorrow",
  "What appointments do I have?",
];


export default function AssistantPage() {

  const searchParams =
    useSearchParams();

  const [input, setInput] =
    useState("");

  const [
    isStreaming,
    setIsStreaming,
  ] = useState(false);

  const [
    streamStatus,
    setStreamStatus,
  ] = useState("");

  const [
    streamedText,
    setStreamedText,
  ] = useState("");

  const [
    streamedActions,
    setStreamedActions,
  ] = useState<
    ChatAction[]
  >([]);

  const [
    errorMessage,
    setErrorMessage,
  ] = useState("");

  const bottomRef =
    useRef<HTMLDivElement | null>(
      null,
    );

  const controllerRef =
    useRef<
      AbortController | null
    >(null);

  const initialActionSent =
    useRef(false);

  const {
    conversationId,
    messages,
    setConversationId,
    addMessage,
    reset,
  } = useChatStore();


  useEffect(() => {
    return () => {
      controllerRef.current
        ?.abort();
    };
  }, []);


  useEffect(() => {

    if (
      initialActionSent.current
    ) {
      return;
    }

    const doctor =
      searchParams.get(
        "doctor",
      );

    const date =
      searchParams.get(
        "date",
      );

    const time =
      searchParams.get(
        "time",
      );

    if (
      doctor &&
      date &&
      time
    ) {
      initialActionSent.current =
        true;

      void submit(
        `Book ${doctor} on ${date} at ${time}`,
      );

      return;
    }

    if (doctor) {
      initialActionSent.current =
        true;

      void submit(
        `Show ${doctor}'s availability tomorrow`,
      );
    }

    // Initial deep-link action only.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);


  useEffect(() => {
    bottomRef.current
      ?.scrollIntoView({
        behavior: "smooth",
      });
  }, [
    messages,
    streamedText,
    streamStatus,
    isStreaming,
  ]);


  async function submit(
    value?: string,
  ) {

    const message =
      (
        value ??
        input
      ).trim();

    if (
      !message ||
      isStreaming
    ) {
      return;
    }

    controllerRef.current
      ?.abort();

    const controller =
      new AbortController();

    controllerRef.current =
      controller;

    setInput("");
    setErrorMessage("");
    setStreamStatus("");
    setStreamedText("");
    setStreamedActions([]);
    setIsStreaming(true);

    addMessage({
      id:
        crypto.randomUUID(),

      role:
        "user",

      content:
        message,
    });

    let assembledText = "";

    let finalActions:
      ChatAction[] = [];

    let completed = false;

    try {

      await streamChat({
        message,

        conversationId,

        signal:
          controller.signal,

        onEvent(event) {

          if (
            event.type ===
            "status"
          ) {
            setStreamStatus(
              event.message,
            );

            return;
          }

          if (
            event.type ===
            "text_delta"
          ) {
            assembledText +=
              event.delta;

            setStreamedText(
              assembledText,
            );

            return;
          }

          if (
            event.type ===
            "actions"
          ) {
            finalActions =
              event.actions;

            setStreamedActions(
              event.actions,
            );

            return;
          }

          if (
            event.type ===
            "done"
          ) {

            completed = true;

            setConversationId(
              event.conversation_id,
            );

            if (
              assembledText.trim()
            ) {
              addMessage({
                id:
                  crypto.randomUUID(),

                role:
                  "assistant",

                content:
                  assembledText,

                actions:
                  finalActions,
              });
            }

            setStreamedText("");
            setStreamedActions([]);
            setStreamStatus("");

            return;
          }

          if (
            event.type ===
            "error"
          ) {
            throw new Error(
              event.message,
            );
          }
        },
      });

      /*
       * Defensive fallback:
       * if the transport closed without a done event,
       * keep the response instead of losing it.
       */
      if (
        !completed &&
        assembledText.trim()
      ) {
        addMessage({
          id:
            crypto.randomUUID(),

          role:
            "assistant",

          content:
            assembledText,

          actions:
            finalActions,
        });

        setStreamedText("");
        setStreamedActions([]);
      }

    } catch (error) {

      if (
        error instanceof DOMException &&
        error.name === "AbortError"
      ) {
        return;
      }

      console.error(
        "MediBook assistant stream failed:",
        error,
      );

      setErrorMessage(
        error instanceof Error
          ? error.message
          : (
              "MediBook could not complete "
              + "that request."
            ),
      );

    } finally {

      if (
        controllerRef.current ===
        controller
      ) {
        controllerRef.current =
          null;
      }

      setIsStreaming(false);
      setStreamStatus("");
    }
  }


  function stopStreaming() {

    controllerRef.current
      ?.abort();

    controllerRef.current =
      null;

    setIsStreaming(false);
    setStreamStatus("");
  }


  function newConversation() {

    controllerRef.current
      ?.abort();

    controllerRef.current =
      null;

    setIsStreaming(false);
    setStreamStatus("");
    setStreamedText("");
    setStreamedActions([]);
    setErrorMessage("");

    reset();
  }


  function onSubmit(
    event: FormEvent,
  ) {
    event.preventDefault();

    void submit();
  }


  const hasStreamingBubble =
    Boolean(
      streamedText ||
      streamStatus ||
      isStreaming,
    );


  return (
    <div className="mx-auto flex h-[calc(100vh-8rem)] max-w-5xl flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white">

      <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">

        <div>
          <h1 className="font-bold">
            MediBook AI
          </h1>

          <p className="mt-0.5 text-xs text-slate-500">
            Connected to real doctors,
            schedules and appointments
          </p>
        </div>

        <button
          onClick={
            newConversation
          }
          className="flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-xs font-semibold transition hover:bg-slate-50"
        >
          <Plus
            size={14}
          />

          New conversation
        </button>
      </div>


      <div className="flex-1 overflow-y-auto bg-slate-50/60 p-5">

        {messages.length === 0 &&
        !hasStreamingBubble ? (

          <div className="mx-auto flex h-full max-w-xl flex-col items-center justify-center text-center">

            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-600 text-white">
              <Bot
                size={25}
              />
            </div>

            <h2 className="mt-5 text-2xl font-bold">
              What can I help you arrange?
            </h2>

            <p className="mt-2 text-sm leading-6 text-slate-500">
              I can find doctors,
              check actual schedules,
              book appointments and
              manage existing bookings.
            </p>

            <div className="mt-6 grid w-full gap-2">

              {quickActions.map(
                (action) => (
                  <button
                    key={action}
                    disabled={
                      isStreaming
                    }
                    onClick={() =>
                      void submit(
                        action,
                      )
                    }
                    className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-left text-sm transition hover:border-emerald-300 hover:bg-emerald-50/30 disabled:opacity-50"
                  >
                    {action}
                  </button>
                ),
              )}

            </div>
          </div>

        ) : (

          <div className="mx-auto max-w-3xl space-y-6">

            {messages.map(
              (message) => (

                <div
                  key={
                    message.id
                  }
                  className={[
                    "flex gap-3",

                    message.role ===
                    "user"
                      ? "justify-end"
                      : "justify-start",
                  ].join(" ")}
                >

                  {message.role ===
                    "assistant" && (

                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-emerald-600 text-white">
                      <Bot
                        size={15}
                      />
                    </div>

                  )}

                  <div
                    className={[
                      "max-w-[80%] whitespace-pre-wrap rounded-2xl px-4 py-3 text-sm leading-6",

                      message.role ===
                      "user"
                        ? "rounded-br-md bg-slate-950 text-white"
                        : "rounded-bl-md border border-slate-200 bg-white text-slate-700",
                    ].join(" ")}
                  >

                    {
                      message.content
                    }

                    {message.role ===
                      "assistant" &&
                      message.actions &&
                      message.actions.length >
                        0 && (

                      <ChatActions
                        actions={
                          message.actions
                        }

                        disabled={
                          isStreaming
                        }

                        onAction={(
                          action:
                            ChatAction,
                        ) =>
                          void submit(
                            action.message,
                          )
                        }
                      />

                    )}

                  </div>

                  {message.role ===
                    "user" && (

                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-slate-200">
                      <UserRound
                        size={15}
                      />
                    </div>

                  )}

                </div>
              ),
            )}


            {hasStreamingBubble && (

              <div className="flex gap-3">

                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-emerald-600 text-white">
                  <Bot
                    size={15}
                  />
                </div>

                <div className="max-w-[80%] rounded-2xl rounded-bl-md border border-slate-200 bg-white px-4 py-3 text-sm leading-6 text-slate-700">

                  {streamStatus &&
                    !streamedText && (

                    <div className="flex items-center gap-2 text-slate-500">

                      <LoaderCircle
                        size={15}
                        className="animate-spin"
                      />

                      {
                        streamStatus
                      }

                    </div>

                  )}


                  {streamedText && (

                    <div className="whitespace-pre-wrap">
                      {
                        streamedText
                      }

                      {isStreaming && (
                        <span className="ml-1 inline-block h-4 w-1 animate-pulse rounded bg-emerald-500 align-middle" />
                      )}
                    </div>

                  )}


                  {streamedActions.length >
                    0 && (

                    <ChatActions
                      actions={
                        streamedActions
                      }

                      disabled={
                        isStreaming
                      }

                      onAction={(
                        action:
                          ChatAction,
                      ) =>
                        void submit(
                          action.message,
                        )
                      }
                    />

                  )}

                </div>
              </div>

            )}


            <div
              ref={bottomRef}
            />

          </div>
        )}

      </div>


      {errorMessage && (

        <div className="border-t border-red-100 bg-red-50 px-5 py-3 text-sm text-red-700">
          {
            errorMessage
          }

          <span className="ml-1">
            Your booking data was not changed.
          </span>
        </div>

      )}


      <form
        onSubmit={
          onSubmit
        }
        className="border-t border-slate-200 bg-white p-4"
      >

        <div className="mx-auto flex max-w-3xl items-end gap-2 rounded-2xl border border-slate-200 bg-slate-50 p-2 focus-within:border-emerald-400">

          <textarea
            value={
              input
            }

            onChange={(
              event,
            ) =>
              setInput(
                event.target.value,
              )
            }

            onKeyDown={(
              event,
            ) => {

              if (
                event.key ===
                  "Enter" &&
                !event.shiftKey
              ) {
                event.preventDefault();

                void submit();
              }
            }}

            disabled={
              isStreaming
            }

            rows={1}

            placeholder={
              isStreaming
                ? "MediBook is working…"
                : "Ask MediBook…"
            }

            className="max-h-32 min-h-10 flex-1 resize-none bg-transparent px-3 py-2 text-sm outline-none disabled:opacity-60"
          />


          {isStreaming ? (

            <button
              type="button"
              onClick={
                stopStreaming
              }
              title="Stop"
              className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-950 text-white"
            >
              <Square
                size={15}
                fill="currentColor"
              />
            </button>

          ) : (

            <button
              type="submit"

              disabled={
                !input.trim()
              }

              className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-600 text-white disabled:opacity-40"
            >
              <ArrowUp
                size={17}
              />
            </button>

          )}

        </div>
      </form>

    </div>
  );
}
