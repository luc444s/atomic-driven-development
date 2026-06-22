import { create } from "zustand";

import type { UserProfile } from "./api";

const TOKEN_KEY = "systutor.access_token";

function readStoredToken() {
  if (typeof window === "undefined") {
    return null;
  }

  return window.localStorage.getItem(TOKEN_KEY);
}

type AuthState = {
  token: string | null;
  user: UserProfile | null;
  setSession: (token: string, user: UserProfile) => void;
  setUser: (user: UserProfile | null) => void;
  logout: () => void;
};

export const useAuthStore = create<AuthState>((set) => ({
  token: readStoredToken(),
  user: null,
  setSession: (token, user) => {
    if (typeof window !== "undefined") {
      window.localStorage.setItem(TOKEN_KEY, token);
    }

    set({ token, user });
  },
  setUser: (user) => set({ user }),
  logout: () => {
    if (typeof window !== "undefined") {
      window.localStorage.removeItem(TOKEN_KEY);
    }

    set({ token: null, user: null });
  },
}));
