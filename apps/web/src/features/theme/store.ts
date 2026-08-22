import { create } from "zustand";

import { injectThemeTokens } from "./apply-tokens";

const STORAGE_KEY = "systutor.theme";

type Theme = "dark" | "light" | "retro";

const THEME_ORDER: Theme[] = ["dark", "light", "retro"];

function getInitialTheme(): Theme {
  if (typeof window === "undefined") return "dark";
  const stored = window.localStorage.getItem(STORAGE_KEY);
  if (stored === "light" || stored === "dark" || stored === "retro") return stored;
  return "dark";
}

function applyTheme(theme: Theme) {
  if (typeof window === "undefined") return;
  const root = document.documentElement;
  root.classList.toggle("dark", theme === "dark");
  root.classList.toggle("retro", theme === "retro");
}

type ThemeState = {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
};

export const useThemeStore = create<ThemeState>((set) => {
  injectThemeTokens();
  const initial = getInitialTheme();
  applyTheme(initial);
  return {
    theme: initial,
    setTheme: (theme) => {
      applyTheme(theme);
      if (typeof window !== "undefined") {
        window.localStorage.setItem(STORAGE_KEY, theme);
      }
      set({ theme });
    },
    toggleTheme: () => {
      set((state) => {
        const idx = THEME_ORDER.indexOf(state.theme);
        const next = THEME_ORDER[(idx + 1) % THEME_ORDER.length];
        applyTheme(next);
        if (typeof window !== "undefined") {
          window.localStorage.setItem(STORAGE_KEY, next);
        }
        return { theme: next };
      });
    },
  };
});
