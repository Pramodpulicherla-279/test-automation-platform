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

  activeRequest: {
    method: "GET",
    url: "",
    headers: [{ key: "", value: "" }],
    params: [{ key: "", value: "" }],
    body: "",
  },

  /* ===== COLLECTIONS ===== */

  createCollection: (name) =>
    set((state) => {
      const updated = [
        ...state.collections,
        { id: Date.now(), name, requests: [] },
      ];
      save("collections", updated);
      return { collections: updated };
    }),

  addToCollection: (collectionId, req) =>
    set((state) => {
      const updated = state.collections.map((c) =>
        c.id === collectionId
          ? { ...c, requests: [...c.requests, { id: Date.now(), ...req }] }
          : c
      );
      save("collections", updated);
      return { collections: updated };
    }),

  deleteRequest: (collectionId, requestId) =>
    set((state) => {
      const updated = state.collections.map((c) =>
        c.id === collectionId
          ? {
              ...c,
              requests: c.requests.filter((r) => r.id !== requestId),
            }
          : c
      );
      save("collections", updated);
      return { collections: updated };
    }),

  /* ===== REQUEST ===== */

  setActiveRequest: (data) =>
    set({
      activeRequest: {
        ...get().activeRequest,
        ...data,
      },
    }),

  loadRequest: (req) =>
    set({
      activeRequest: {
        method: req.method,
        url: req.url,
        headers: req.headers || [{ key: "", value: "" }],
        params: req.params || [{ key: "", value: "" }],
        body: req.body || "",
      },
    }),

  /* ===== HISTORY ===== */

  addHistory: (req) =>
    set((state) => {
      const updated = [{ id: Date.now(), ...req }, ...state.history];
      save("history", updated);
      return { history: updated };
    }),
}));