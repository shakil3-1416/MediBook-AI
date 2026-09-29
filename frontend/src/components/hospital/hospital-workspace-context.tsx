"use client";

import {
  createContext,
  ReactNode,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";

import {
  useRouter,
} from "next/navigation";


export type HospitalWorkspace = {
  id: string;
  slug: string;
  name: string;
  status: string;
  timezone: string;
  role: string;
};


type ContextValue = {
  workspaces: HospitalWorkspace[];
  activeWorkspace:
    HospitalWorkspace | null;
  loading: boolean;
  switching: boolean;
  error: string | null;
  reload: () => Promise<void>;
  selectWorkspace:
    (
      slug: string,
    ) => Promise<void>;
};


type WorkspaceResponse = {
  workspaces:
    HospitalWorkspace[];
  active:
    HospitalWorkspace | null;
};


const HospitalWorkspaceContext =
  createContext<
    ContextValue | null
  >(
    null,
  );


export function HospitalWorkspaceProvider({
  children,
}: {
  children: ReactNode;
}) {
  const router =
    useRouter();

  const [
    workspaces,
    setWorkspaces,
  ] =
    useState<
      HospitalWorkspace[]
    >([]);

  const [
    activeWorkspace,
    setActiveWorkspace,
  ] =
    useState<
      HospitalWorkspace | null
    >(null);

  const [
    loading,
    setLoading,
  ] =
    useState(true);

  const [
    switching,
    setSwitching,
  ] =
    useState(false);

  const [
    error,
    setError,
  ] =
    useState<
      string | null
    >(null);


  const reload =
    useCallback(
      async () => {
        setLoading(true);
        setError(null);

        try {
          const response =
            await fetch(
              "/api/dashboard/hospital-workspaces",
              {
                cache:
                  "no-store",
              },
            );

          if (
            response.status ===
            401
          ) {
            router.replace(
              "/hospital-login",
            );

            return;
          }

          if (!response.ok) {
            const body =
              await response.text();

            throw new Error(
              body ||
              `Workspace request failed (${response.status}).`,
            );
          }

          const payload =
            (
              await response.json()
            ) as WorkspaceResponse;

          setWorkspaces(
            payload.workspaces,
          );

          setActiveWorkspace(
            payload.active,
          );
        } catch (err) {
          setError(
            err instanceof Error
              ? err.message
              : "Could not load hospital workspace.",
          );
        } finally {
          setLoading(false);
        }
      },
      [
        router,
      ],
    );


  useEffect(
    () => {
      queueMicrotask(
        () => {
          void reload();
        },
      );
    },
    [
      reload,
    ],
  );


  async function selectWorkspace(
    slug: string,
  ) {
    if (
      slug ===
      activeWorkspace?.slug
    ) {
      return;
    }

    if (
      !workspaces.some(
        (workspace) =>
          workspace.slug ===
          slug,
      )
    ) {
      return;
    }

    setSwitching(true);
    setError(null);

    try {
      const response =
        await fetch(
          "/api/dashboard/hospital-workspaces",
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
                  hospital:
                    slug,
                },
              ),
          },
        );

      if (
        response.status ===
        401
      ) {
        router.replace(
          "/hospital-login",
        );

        return;
      }

      if (!response.ok) {
        const body =
          await response.text();

        throw new Error(
          body ||
          `Workspace switch failed (${response.status}).`,
        );
      }

      const payload =
        (
          await response.json()
        ) as {
          active:
            HospitalWorkspace;
        };

      setActiveWorkspace(
        payload.active,
      );

      router.refresh();

      window.location.reload();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not switch hospital workspace.",
      );

      setSwitching(false);
    }
  }


  return (
    <HospitalWorkspaceContext.Provider
      value={{
        workspaces,
        activeWorkspace,
        loading,
        switching,
        error,
        reload,
        selectWorkspace,
      }}
    >
      {children}
    </HospitalWorkspaceContext.Provider>
  );
}


export function useHospitalWorkspace() {
  const context =
    useContext(
      HospitalWorkspaceContext,
    );

  if (!context) {
    throw new Error(
      "useHospitalWorkspace must be used inside HospitalWorkspaceProvider.",
    );
  }

  return context;
}
