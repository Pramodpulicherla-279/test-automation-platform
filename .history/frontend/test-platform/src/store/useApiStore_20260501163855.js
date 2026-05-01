import { create } from "zustand";

export const useApiStore = create((set) => ({
  collections: [],

  // ✅ ADD COLLECTION
  addCollection: (name) =>
    set((state) => ({
      collections: [...state.collections, { name, requests: [] }]
    })),

  // ✅ DELETE COLLECTION
  deleteCollection: (index) =>
    set((state) => ({
      collections: state.collections.filter((_, i) => i !== index)
    })),

  // ✅ SAVE REQUEST
  saveRequest: (collectionIndex, request) =>
    set((state) => {
      const updated = [...state.collections];
      updated[collectionIndex].requests.push(request);
      return { collections: updated };
    }),

  history: [],

  addHistory: (req) =>
    set((state) => ({
      history: [req, ...state.history]
    }))
}));