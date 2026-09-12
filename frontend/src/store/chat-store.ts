import {
  create,
} from "zustand";

import type {
  ChatAction,
} from "@/types/api";


export interface ChatMessage {
  id: string;

  role:
    | "user"
    | "assistant";

  content: string;

  actions?: ChatAction[];
}


interface ChatState {
  conversationId?: string;

  messages: ChatMessage[];

  setConversationId:
    (id?: string) => void;

  addMessage:
    (message: ChatMessage) => void;

  clearActions:
    () => void;

  reset:
    () => void;
}


export const useChatStore =
  create<ChatState>(
    (set) => ({
      conversationId:
        undefined,

      messages: [],

      setConversationId:
        (conversationId) =>
          set({
            conversationId,
          }),

      addMessage:
        (message) =>
          set(
            (state) => ({
              messages: [
                ...state.messages.map(
                  (existing) => ({
                    ...existing,
                    actions:
                      undefined,
                  })
                ),

                message,
              ],
            })
          ),

      clearActions:
        () =>
          set(
            (state) => ({
              messages:
                state.messages.map(
                  (message) => ({
                    ...message,
                    actions:
                      undefined,
                  })
                ),
            })
          ),

      reset:
        () =>
          set({
            conversationId:
              undefined,

            messages: [],
          }),
    })
  );
