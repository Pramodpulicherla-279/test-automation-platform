import { create } from "zustand";

const load = (key, fallback) => {
  try {
    return JSON.parse(localStorage.getItem(key)) || fallback;
  } catch {
    return fallback;
  }
};

const save = (key, value) => {
  localStorage.setItem(key, JSON.stringify(value));
};

export const useApiStore = create((set, get) => ({
  collections: load("collections", []),
  history: load("history", []),
  environment: load("environment", {}),

  activeRequest: {
    method: "GET",
    url: "",
    headers: [],
    params: [],
    body: "",
  },

  addCollection: (req) =>
    set((state) => {
      const updated = [...state.collections, { id: Date.now(), ...req }];
      save("collections", updated);
      return { collections: updated };
    }),

  addHistory: (req) =>
    set((state) => {
      const updated = [{ id: Date.now(), ...req }, ...state.history];
      save("history", updated);
      return { history: updated };
    }),

  setActiveRequest: (req) =>
    set({
      activeRequest: {
        ...get().activeRequest,
        ...req,
      },
    }),

  loadRequest: (req) =>
    set({
      activeRequest: req,
    }),

  setEnvironment: (env) => {
    save("environment", env);
    set({ environment: env });
  },

  resolveUrl: (url) => {
    const env = get().environment;
    return url.replace(/\{\{(.*?)\}\}/g, (_, key) => env[key] || "");
  },
}));