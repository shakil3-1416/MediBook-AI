/*
 * Turns an error response into a sentence a person can act on, instead of
 * showing raw JSON such as {"detail": "..."} on screen.
 */
export async function readErrorMessage(
  response: Response,
  fallback: string,
): Promise<string> {
  const text = await response.text().catch(() => "");
  if (text === "") {
    return fallback;
  }
  try {
    const parsed = JSON.parse(text) as {
      detail?: unknown;
      message?: unknown;
    };
    if (typeof parsed.detail === "string") {
      return parsed.detail;
    }
    if (
      parsed.detail &&
      typeof parsed.detail === "object" &&
      typeof (parsed.detail as { message?: unknown }).message === "string"
    ) {
      return (parsed.detail as { message: string }).message;
    }
    if (typeof parsed.message === "string") {
      return parsed.message;
    }
  } catch {
    // Not JSON: fall through to the plain-text rules below.
  }
  const trimmed = text.trim();
  return trimmed.startsWith("<") || trimmed.length > 200 ? fallback : trimmed;
}
