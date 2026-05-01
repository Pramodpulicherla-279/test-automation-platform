import { create } from "zustand";

export const useApiStore = create((set, get) => ({
  collections: [],
  history: [],
  auth: { type: "none", token: "", key: "", value: "" },
  throttle: "no-limit",

  addCollection: (name) =>
    set((s) => ({
      collections: [...s.collections, { name, requests: [] }]
    })),

  saveRequest: (collectionIndex, req) =>
    set((s) => {
      const updated = [...s.collections];
      updated[collectionIndex].requests.push(req);
      return { collections: updated };
    }),

  deleteRequest: (cIndex, rIndex) =>
    set((s) => {
      const updated = [...s.collections];
      updated[cIndex].requests.splice(rIndex, 1);
      return { collections: updated };
    }),

  addHistory: (entry) =>
    set((s) => ({ history: [entry, ...s.history] })),

  setAuth: (auth) => set({ auth }),
  setThrottle: (throttle) => set({ throttle })
}));