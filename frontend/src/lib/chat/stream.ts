import type {
  ChatAction,
} from "@/types/api";


export type ChatStreamEvent =
  | {
      type: "status";
      message: string;
    }
  | {
      type: "text_delta";
      delta: string;
    }
  | {
      type: "actions";
      actions: ChatAction[];
    }
  | {
      type: "done";
      conversation_id: string;
    }
  | {
      type: "error";
      message: string;
    };


type StreamOptions = {
  message: string;
  conversationId?: string | null;
  signal?: AbortSignal;

  onEvent: (
    event: ChatStreamEvent,
  ) => void;
};


export async function streamChat({
  message,
  conversationId,
  signal,
  onEvent,
}: StreamOptions): Promise<void> {

  const response = await fetch(
    "/api/chat/stream",
    {
      method: "POST",

      headers: {
        "Content-Type":
          "application/json",

        Accept:
          "application/x-ndjson",
      },

      body: JSON.stringify({
        message,

        conversation_id:
          conversationId || null,
      }),

      cache: "no-store",

      signal,
    },
  );

  if (!response.ok) {
    const detail =
      await response.text();

    throw new Error(
      detail ||
      `Chat request failed with ${response.status}`,
    );
  }

  if (!response.body) {
    throw new Error(
      "Streaming response body is unavailable.",
    );
  }

  const reader =
    response.body
      .pipeThrough(
        new TextDecoderStream(),
      )
      .getReader();

  let buffer = "";

  while (true) {
    const {
      value,
      done,
    } = await reader.read();

    if (done) {
      break;
    }

    buffer += value;

    const lines =
      buffer.split("\n");

    buffer =
      lines.pop() ?? "";

    for (const line of lines) {
      const clean =
        line.trim();

      if (!clean) {
        continue;
      }

      onEvent(
        JSON.parse(
          clean,
        ) as ChatStreamEvent,
      );
    }
  }

  if (buffer.trim()) {
    onEvent(
      JSON.parse(
        buffer,
      ) as ChatStreamEvent,
    );
  }
}
