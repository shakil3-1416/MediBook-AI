"use client";

export async function hospitalOpsRequest<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const response =
    await fetch(
      path,
      {
        ...init,
        cache:
          "no-store",
        headers: {
          ...(init?.body
            ? {
                "Content-Type":
                  "application/json",
              }
            : {}),
          ...(init?.headers ?? {}),
        },
      },
    );

  const text =
    await response.text();

  if (!response.ok) {
    let message =
      text ||
      `Request failed (${response.status}).`;

    try {
      const parsed =
        JSON.parse(
          text,
        );

      if (
        parsed &&
        typeof parsed.detail ===
          "string"
      ) {
        message =
          parsed.detail;
      }
    } catch {}

    throw new Error(
      message,
    );
  }

  if (!text) {
    return undefined as T;
  }

  return JSON.parse(
    text,
  ) as T;
}


export function normalizeCollection(
  value: unknown,
): Record<string, unknown>[] {
  if (Array.isArray(value)) {
    return value.filter(
      (
        item,
      ): item is Record<
        string,
        unknown
      > =>
        Boolean(
          item &&
          typeof item ===
            "object" &&
          !Array.isArray(item),
        ),
    );
  }

  if (
    value &&
    typeof value ===
      "object"
  ) {
    const record =
      value as Record<
        string,
        unknown
      >;

    for (const key of [
      "items",
      "results",
      "data",
      "doctors",
      "staff",
      "entries",
      "audit",
    ]) {
      if (
        Array.isArray(
          record[key],
        )
      ) {
        return normalizeCollection(
          record[key],
        );
      }
    }
  }

  return [];
}


export function displayValue(
  value: unknown,
): string {
  if (
    value === null ||
    value === undefined
  ) {
    return "—";
  }

  if (
    typeof value ===
      "boolean"
  ) {
    return value
      ? "Yes"
      : "No";
  }

  if (
    typeof value ===
      "object"
  ) {
    try {
      return JSON.stringify(
        value,
      );
    } catch {
      return "—";
    }
  }

  return String(
    value,
  );
}
