import { create } from "zustand";
import { UserProfile } from "../services/api";

interface AppState {
  isLoggedIn: boolean;
  user: UserProfile | null;
  setUser: (user: UserProfile | null) => void;
  setIsLoggedIn: (v: boolean) => void;
}

export const useStore = create<AppState>((set) => ({
  isLoggedIn: false, user: null,
  setUser: (user) => set({ user, isLoggedIn: !!user }),
  setIsLoggedIn: (v) => set({ isLoggedIn: v }),
}));
