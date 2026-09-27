"use client";

import { createContext, useContext, useState, useSyncExternalStore, type ReactNode } from "react";

type ConfigContextType = {
  analyzeToken: string;
  autofixToken: string;
  setAnalyzeToken: (val: string) => void;
  setAutofixToken: (val: string) => void;
  isConfigOpen: boolean;
  openConfig: () => void;
  closeConfig: () => void;
};

const ConfigContext = createContext<ConfigContextType>({
  analyzeToken: "",
  autofixToken: "",
  setAnalyzeToken: () => {},
  setAutofixToken: () => {},
  isConfigOpen: false,
  openConfig: () => {},
  closeConfig: () => {},
});

const STORAGE_ANALYZE_TOKEN = "testmind_analyze_token";
const STORAGE_AUTOFIX_TOKEN = "testmind_autofix_token";

function subscribe(callback: () => void) {
  window.addEventListener("storage", callback);
  return () => window.removeEventListener("storage", callback);
}

function getAnalyzeSnapshot(): string {
  if (typeof window === "undefined") return "";
  return localStorage.getItem(STORAGE_ANALYZE_TOKEN) ?? "";
}

function getAutofixSnapshot(): string {
  if (typeof window === "undefined") return "";
  return localStorage.getItem(STORAGE_AUTOFIX_TOKEN) ?? "";
}

function getServerSnapshot(): string {
  return "";
}

export function ConfigProvider({ children }: { children: ReactNode }) {
  const analyzeToken = useSyncExternalStore(subscribe, getAnalyzeSnapshot, getServerSnapshot);
  const autofixToken = useSyncExternalStore(subscribe, getAutofixSnapshot, getServerSnapshot);
  const [isConfigOpen, setIsConfigOpen] = useState(false);

  const setAnalyzeToken = (val: string) => {
    try {
      localStorage.setItem(STORAGE_ANALYZE_TOKEN, val);
      window.dispatchEvent(new Event("storage"));
    } catch {
      // Ignore storage errors in private browsing
    }
  };

  const setAutofixToken = (val: string) => {
    try {
      localStorage.setItem(STORAGE_AUTOFIX_TOKEN, val);
      window.dispatchEvent(new Event("storage"));
    } catch {
      // Ignore storage errors in private browsing
    }
  };

  const openConfig = () => setIsConfigOpen(true);
  const closeConfig = () => setIsConfigOpen(false);

  return (
    <ConfigContext.Provider
      value={{
        analyzeToken,
        autofixToken,
        setAnalyzeToken,
        setAutofixToken,
        isConfigOpen,
        openConfig,
        closeConfig,
      }}
    >
      {children}
    </ConfigContext.Provider>
  );
}

export function useConfig() {
  return useContext(ConfigContext);
}
