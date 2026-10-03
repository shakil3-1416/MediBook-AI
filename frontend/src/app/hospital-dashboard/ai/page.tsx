"use client";

import {
  Bot,
  CheckCircle2,
  Send,
  ShieldCheck,
  User,
  XCircle,
} from "lucide-react";

import {
  FormEvent,
  useState,
} from "react";

import {
  useHospitalWorkspace,
} from "@/components/hospital/hospital-workspace-context";


type ToolResult = {
  tool: string;
  available: boolean;
  data: Record<
    string,
    unknown
  >;
  note?: string | null;
};


type Proposal = {
  id: string;
  action_type:
    | "schedule_capacity_change"
    | "schedule_closure";
  payload: Record<
    string,
    unknown
  >;
  impact: Record<
    string,
    unknown
  >;
  status: string;
  execution_supported: boolean;
  execution_result?:
    Record<
      string,
      unknown
    > | null;
};


type CopilotResponse = {
  intent: string;
  answer: string;
  mode:
    | "deterministic"
    | "llm_grounded";
  tools: ToolResult[];
  proposal_required: boolean;
  proposal_id?:
    string | null;
  proposal?:
    Proposal | null;
  warnings: string[];
};


type Message = {
  id: string;
  role:
    | "user"
    | "assistant";
  content: string;
  response?:
    CopilotResponse;
};


function makeId() {
  return (
    `${Date.now()}-${Math.random()}`
  );
}


async function readApiError(
  response: Response,
) {
  const raw =
    await response.text();

  if (!raw) {
    return (
      `Request failed (${response.status}).`
    );
  }

  try {
    const parsed =
      JSON.parse(
        raw,
      ) as {
        detail?: unknown;
      };

    if (
      typeof parsed.detail ===
      "string"
    ) {
      return parsed.detail;
    }

    return raw;
  } catch {
    return raw;
  }
}


export default function HospitalCopilotPage() {
  const {
    activeWorkspace,
  } =
    useHospitalWorkspace();

  const canPropose =
    activeWorkspace?.role ===
      "hospital_admin";

  const [
    message,
    setMessage,
  ] =
    useState("");

  const [
    messages,
    setMessages,
  ] =
    useState<Message[]>([
      {
        id:
          "welcome",

        role:
          "assistant",

        content:
          "Ask about appointments, doctors, capacity, schedules, integrations, staff, or recent hospital changes. Facts come only from hospital-scoped deterministic tools.",
      },
    ]);

  const [
    busy,
    setBusy,
  ] =
    useState(false);

  const [
    proposal,
    setProposal,
  ] =
    useState<
      Proposal | null
    >(null);

  const [
    proposalError,
    setProposalError,
  ] =
    useState<
      string | null
    >(null);


  async function submit(
    event: FormEvent,
  ) {
    event.preventDefault();

    const text =
      message.trim();

    if (
      !text ||
      busy
    ) {
      return;
    }

    setMessages(
      (
        current,
      ) => [
        ...current,
        {
          id:
            makeId(),

          role:
            "user",

          content:
            text,
        },
      ],
    );

    setMessage("");
    setBusy(true);

    try {
      const response =
        await fetch(
          "/api/dashboard/hospital-copilot",
          {
            method:
              "POST",

            headers: {
              "Content-Type":
                "application/json",
            },

            body:
              JSON.stringify(
                {
                  message:
                    text,
                },
              ),
          },
        );

      if (!response.ok) {
        throw new Error(
          await readApiError(
            response
          ),
        );
      }

      const payload =
        (await response.json()) as CopilotResponse;

      setMessages(
        (
          current,
        ) => [
          ...current,
          {
            id:
              makeId(),

            role:
              "assistant",

            content:
              payload.answer,

            response:
              payload,
          },
        ],
      );
    } catch (err) {
      setMessages(
        (
          current,
        ) => [
          ...current,
          {
            id:
              makeId(),

            role:
              "assistant",

            content:
              err instanceof Error
                ? err.message
                : (
                    "The Copilot request failed."
                  ),
          },
        ],
      );
    } finally {
      setBusy(false);
    }
  }


  async function createCapacityProposal() {
    const ruleId =
      window.prompt(
        "Schedule rule ID",
      );

    if (!ruleId) {
      return;
    }

    const capacityText =
      window.prompt(
        "New capacity",
      );

    if (!capacityText) {
      return;
    }

    const newCapacity =
      Number(
        capacityText
      );

    if (
      !Number.isInteger(
        newCapacity
      )
      ||
      newCapacity < 1
    ) {
      setProposalError(
        "Capacity must be a positive integer.",
      );

      return;
    }

    await createProposal(
      {
        action_type:
          "schedule_capacity_change",

        payload: {
          schedule_rule_id:
            ruleId,

          new_capacity:
            newCapacity,
        },
      },
    );
  }


  async function createClosureProposal() {
    const hospitalDoctorId =
      window.prompt(
        "Hospital doctor mapping ID",
      );

    if (!hospitalDoctorId) {
      return;
    }

    const date =
      window.prompt(
        "Closure date (YYYY-MM-DD)",
      );

    if (!date) {
      return;
    }

    const reason =
      window.prompt(
        "Reason for closure",
      );

    if (!reason) {
      return;
    }

    await createProposal(
      {
        action_type:
          "schedule_closure",

        payload: {
          hospital_doctor_id:
            hospitalDoctorId,

          date,

          reason,
        },
      },
    );
  }


  async function createProposal(
    body: {
      action_type:
        Proposal[
          "action_type"
        ];
      payload:
        Record<
          string,
          unknown
        >;
    },
  ) {
    if (!canPropose) {
      setProposalError(
        "Only hospital administrators can create operational proposals.",
      );

      return;
    }

    setBusy(true);
    setProposalError(null);

    try {
      const response =
        await fetch(
          "/api/dashboard/hospital-copilot?action=proposal",
          {
            method:
              "POST",

            headers: {
              "Content-Type":
                "application/json",
            },

            body:
              JSON.stringify(
                body
              ),
          },
        );

      if (!response.ok) {
        throw new Error(
          await readApiError(
            response
          ),
        );
      }

      const value =
        (await response.json()) as Proposal;

      setProposal(
        value
      );

    } catch (err) {
      setProposalError(
        err instanceof Error
          ? err.message
          : (
              "Could not create proposal."
            ),
      );

    } finally {
      setBusy(false);
    }
  }


  async function executeProposal() {
    if (!proposal) {
      return;
    }

    setBusy(true);
    setProposalError(null);

    try {
      const response =
        await fetch(
          `/api/dashboard/hospital-copilot?action=proposal-execute&proposalId=${encodeURIComponent(
            proposal.id,
          )}`,
          {
            method:
              "POST",
          },
        );

      if (!response.ok) {
        throw new Error(
          await readApiError(
            response
          ),
        );
      }

      const value =
        (await response.json()) as Proposal;

      setProposal(
        value
      );

    } catch (err) {
      setProposalError(
        err instanceof Error
          ? err.message
          : (
              "Could not execute proposal."
            ),
      );

    } finally {
      setBusy(false);
    }
  }


  async function decideProposal(
    confirm: boolean,
  ) {
    if (!proposal) {
      return;
    }

    setBusy(true);
    setProposalError(null);

    try {
      const response =
        await fetch(
          `/api/dashboard/hospital-copilot?action=proposal-confirm&proposalId=${encodeURIComponent(
            proposal.id,
          )}`,
          {
            method:
              "POST",

            headers: {
              "Content-Type":
                "application/json",
            },

            body:
              JSON.stringify(
                {
                  confirm,
                },
              ),
          },
        );

      if (!response.ok) {
        throw new Error(
          await readApiError(
            response
          ),
        );
      }

      const value =
        (await response.json()) as Proposal;

      setProposal(
        value
      );

    } catch (err) {
      setProposalError(
        err instanceof Error
          ? err.message
          : (
              "Could not update proposal."
            ),
      );

    } finally {
      setBusy(false);
    }
  }


  return (
    <main className="flex min-h-[calc(100vh-4rem)] flex-col">
      <div className="border-b border-slate-200 bg-white px-5 py-5 md:px-8">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-sm font-semibold text-brand-600">
              <Bot
                size={17}
              />

              Hospital AI
            </div>

            <h1 className="mt-1 text-2xl font-semibold tracking-tight text-slate-950">
              Operations Copilot
            </h1>

            <p className="mt-1 text-sm text-slate-500">
              {
                activeWorkspace?.name
              }
            </p>
          </div>

          <div className="hidden items-center gap-2 rounded-full bg-brand-50 px-3 py-1.5 text-xs font-semibold text-brand-700 sm:flex">
            <ShieldCheck
              size={14}
            />

            Grounded tools
          </div>
        </div>

        {canPropose ? (
          <div className="mx-auto mt-4 flex max-w-5xl flex-wrap gap-2">
            <button
              type="button"
              onClick={
                () =>
                  void createCapacityProposal()
              }
              className="rounded-xl border border-brand-200 bg-brand-50 px-3 py-2 text-xs font-semibold text-brand-700"
            >
              Propose capacity change
            </button>

            <button
              type="button"
              onClick={
                () =>
                  void createClosureProposal()
              }
              className="rounded-xl border border-brand-200 bg-brand-50 px-3 py-2 text-xs font-semibold text-brand-700"
            >
              Propose schedule closure
            </button>
          </div>
        ) : null}
      </div>

      {proposalError ? (
        <div className="mx-auto mt-5 w-full max-w-5xl px-4 md:px-8">
          <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
            {
              proposalError
            }
          </div>
        </div>
      ) : null}

      {proposal ? (
        <div className="mx-auto mt-5 w-full max-w-5xl px-4 md:px-8">
          <div className="rounded-2xl border border-brand-200 bg-brand-50/60 p-5">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <div className="text-xs font-semibold uppercase tracking-wide text-brand-700">
                  Operational proposal
                </div>

                <h2 className="mt-1 text-lg font-semibold text-slate-950">
                  {
                    proposal.action_type
                  }
                </h2>

                <p className="mt-1 text-xs text-slate-500">
                  Status:{" "}
                  {
                    proposal.status
                  }
                </p>
              </div>

              <span className={[
                "rounded-full px-2.5 py-1 text-xs font-semibold",
                proposal.execution_supported
                  ? "bg-brand-100 text-brand-700"
                  : "bg-amber-100 text-amber-800",
              ].join(
                " ",
              )}>
                {
                  proposal.execution_supported
                    ? "Executable"
                    : "Execution gated"
                }
              </span>
            </div>

            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <div>
                <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Proposed change
                </div>

                <pre className="mt-2 overflow-x-auto rounded-xl bg-white p-3 text-xs text-slate-700">
                  {
                    JSON.stringify(
                      proposal.payload,
                      null,
                      2,
                    )
                  }
                </pre>
              </div>

              <div>
                <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Impact preview
                </div>

                <pre className="mt-2 overflow-x-auto rounded-xl bg-white p-3 text-xs text-slate-700">
                  {
                    JSON.stringify(
                      proposal.impact,
                      null,
                      2,
                    )
                  }
                </pre>
              </div>
            </div>

            {proposal.status ===
            "pending" ? (
              <div className="mt-4 flex flex-wrap gap-2">
                <button
                  type="button"
                  disabled={
                    busy
                  }
                  onClick={
                    () =>
                      void decideProposal(
                        true
                      )
                  }
                  className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
                >
                  <CheckCircle2
                    size={16}
                  />

                  Confirm proposal
                </button>

                <button
                  type="button"
                  disabled={
                    busy
                  }
                  onClick={
                    () =>
                      void decideProposal(
                        false
                      )
                  }
                  className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 disabled:opacity-50"
                >
                  <XCircle
                    size={16}
                  />

                  Cancel
                </button>
              </div>
            ) : null}

            {proposal.status ===
            "confirmed" &&
            proposal.execution_supported ? (
              <div className="mt-4">
                <button
                  type="button"
                  disabled={
                    busy
                  }
                  onClick={
                    () =>
                      void executeProposal()
                  }
                  className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
                >
                  Execute confirmed change
                </button>
              </div>
            ) : null}

            {!proposal.execution_supported ? (
              <p className="mt-4 text-xs leading-5 text-amber-800">
                Confirmation is recorded, but no schedule mutation is executed until the existing Schedule Engine apply contract is wired. Copilot will not bypass that safety boundary.
              </p>
            ) : null}
          </div>
        </div>
      ) : null}

      <div className="flex-1 overflow-y-auto px-4 py-8 md:px-8">
        <div className="mx-auto max-w-5xl space-y-6">
          {
            messages.map(
              (
                item,
              ) => (
                <div
                  key={
                    item.id
                  }
                  className={[
                    "flex gap-3",
                    item.role ===
                    "user"
                      ? "justify-end"
                      : "justify-start",
                  ].join(
                    " ",
                  )}
                >
                  {item.role ===
                  "assistant" ? (
                    <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-100 text-brand-700">
                      <Bot
                        size={16}
                      />
                    </div>
                  ) : null}

                  <div
                    className={[
                      "max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-6",
                      item.role ===
                      "user"
                        ? "bg-brand-600 text-white"
                        : "border border-slate-200 bg-white text-slate-800 shadow-sm",
                    ].join(
                      " ",
                    )}
                  >
                    <div className="whitespace-pre-wrap">
                      {
                        item.content
                      }
                    </div>

                    {item.response ? (
                      <div className="mt-3 border-t border-slate-100 pt-3">
                        <div className="flex flex-wrap gap-2">
                          <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-semibold text-slate-600">
                            {
                              item.response.intent
                            }
                          </span>

                          <span className="rounded-full bg-brand-50 px-2.5 py-1 text-[11px] font-semibold text-brand-700">
                            {
                              item.response.mode
                            }
                          </span>

                          {
                            item.response.tools.map(
                              (
                                tool,
                              ) => (
                                <span
                                  key={
                                    tool.tool
                                  }
                                  className={[
                                    "rounded-full px-2.5 py-1 text-[11px] font-semibold",
                                    tool.available
                                      ? "bg-brand-50 text-brand-700"
                                      : "bg-amber-50 text-amber-700",
                                  ].join(
                                    " ",
                                  )}
                                >
                                  {
                                    tool.tool
                                  }
                                </span>
                              ),
                            )
                          }
                        </div>
                      </div>
                    ) : null}
                  </div>

                  {item.role ===
                  "user" ? (
                    <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-200 text-slate-700">
                      <User
                        size={16}
                      />
                    </div>
                  ) : null}
                </div>
              ),
            )
          }

          {busy ? (
            <div className="flex gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-100 text-brand-700">
                <Bot
                  size={16}
                />
              </div>

              <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-500 shadow-sm">
                Checking hospital data...
              </div>
            </div>
          ) : null}
        </div>
      </div>

      <div className="sticky bottom-0 border-t border-slate-200 bg-white/95 px-4 py-4 backdrop-blur md:px-8">
        <form
          onSubmit={
            submit
          }
          className="mx-auto flex max-w-5xl items-end gap-3 rounded-2xl border border-slate-200 bg-white p-2 shadow-sm focus-within:border-brand-300 focus-within:ring-4 focus-within:ring-brand-50"
        >
          <textarea
            rows={1}
            value={
              message
            }
            onChange={
              (
                event,
              ) =>
                setMessage(
                  event.target.value,
                )
            }
            onKeyDown={
              (
                event,
              ) => {
                if (
                  event.key ===
                    "Enter"
                  &&
                  !event.shiftKey
                ) {
                  event.preventDefault();

                  event.currentTarget
                    .form
                    ?.requestSubmit();
                }
              }
            }
            placeholder="Ask about hospital operations..."
            className="max-h-40 min-h-11 flex-1 resize-none border-0 bg-transparent px-3 py-2.5 text-sm outline-none"
          />

          <button
            type="submit"
            disabled={
              busy
              ||
              !message.trim()
            }
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-600 text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-40"
          >
            <Send
              size={17}
            />
          </button>
        </form>

        <p className="mx-auto mt-2 max-w-5xl text-center text-[11px] text-slate-500">
          AI interprets language. Deterministic hospital tools provide facts. Operational changes require an explicit proposal, human confirmation, and deterministic Schedule Engine execution.
        </p>
      </div>
    </main>
  );
}
