import { create } from "zustand";

export const useApiStore = create((set, get) => ({
  tabs: [
    {
      id: 1,
      name: "New Tab",
      request: {
        method: "GET",
        url: "",
        headers: [{ key: "", value: "" }],
        params: [{ key: "", value: "" }],
        body: "",
        auth: { type: "none", token: "" },
      },
      response: null,
      status: null,
      time: null,
    },
  ],

  activeTabId: 1,

  /* ===== TAB SYSTEM ===== */

  addTab: () =>
    set((state) => {
      const newTab = {
        id: Date.now(),
        name: "New Tab",
        request: {
          method: "GET",
          url: "",
          headers: [{ key: "", value: "" }],
          params: [{ key: "", value: "" }],
          body: "",
          auth: { type: "none", token: "" },
        },
        response: null,
        status: null,
        time: null,
      };

      return {
        tabs: [...state.tabs, newTab],
        activeTabId: newTab.id,
      };
    }),

  setActiveTab: (id) => set({ activeTabId: id }),

  updateRequest: (data) =>
    set((state) => ({
      tabs: state.tabs.map((t) =>
        t.id === state.activeTabId
          ? { ...t, request: { ...t.request, ...data } }
          : t
      ),
    })),

  setResponse: (res, status, time) =>
    set((state) => ({
      tabs: state.tabs.map((t) =>
        t.id === state.activeTabId
          ? { ...t, response: res, status, time }
          : t
      ),
    })),
}));