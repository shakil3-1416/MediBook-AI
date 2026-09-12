"use client";

import {
  QueryClient,
  QueryClientProvider,
} from "@tanstack/react-query";

import {
  ReactNode,
  useState,
} from "react";


export function AppProvider({
  children,
}: {
  children: ReactNode;
}) {
  const [client] =
    useState(
      () =>
        new QueryClient({
          defaultOptions: {
            queries: {
              staleTime: 30_000,
              retry: 2,
              refetchOnWindowFocus: false,
            },

            mutations: {
              retry: 0,
            },
          },
        })
    );

  return (
    <QueryClientProvider
      client={client}
    >
      {children}
    </QueryClientProvider>
  );
}
