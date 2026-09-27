"use client";

import { createContext, useContext, useSyncExternalStore, type ReactNode } from "react";

type DemoModeContextType = {
  demoMode: boolean;
  toggleDemoMode: () => void;
  setDemoMode: (val: boolean) => void;
};

const DemoModeContext = createContext<DemoModeContextType>({
  demoMode: false,
  toggleDemoMode: () => {},
  setDemoMode: () => {},
});

const STORAGE_KEY = "testmind_demo_mode";

function subscribe(callback: () => void) {
  window.addEventListener("storage", callback);
  return () => window.removeEventListener("storage", callback);
}

function getSnapshot(): boolean {
  if (typeof window === "undefined") {
    return false;
  }
  return localStorage.getItem(STORAGE_KEY) === "true";
}

function getServerSnapshot(): boolean {
  return false;
}

export function DemoModeProvider({ children }: { children: ReactNode }) {
  const demoMode = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);

  const setDemoMode = (val: boolean) => {
    try {
      localStorage.setItem(STORAGE_KEY, String(val));
      window.dispatchEvent(new Event("storage"));
    } catch {
      // Ignore storage errors in private browsing
    }
  };

  const toggleDemoMode = () => {
    setDemoMode(!demoMode);
  };

  return (
    <DemoModeContext.Provider value={{ demoMode, toggleDemoMode, setDemoMode }}>
      {children}
    </DemoModeContext.Provider>
  );
}

export function useDemoMode() {
  return useContext(DemoModeContext);
}
