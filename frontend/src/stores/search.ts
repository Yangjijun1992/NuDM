import { create } from "zustand"

interface SearchState {
  query: string
  history: string[]
  setQuery: (q: string) => void
  addHistory: (q: string) => void
  clearHistory: () => void
}

const STORAGE_KEY = "nudm_search_history"

function loadHistory(): string[] {
  if (typeof window === "undefined") return []
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]")
  } catch {
    return []
  }
}

function saveHistory(history: string[]) {
  if (typeof window === "undefined") return
  localStorage.setItem(STORAGE_KEY, JSON.stringify(history.slice(0, 20)))
}

export const useSearchStore = create<SearchState>((set, get) => ({
  query: "",
  history: loadHistory(),

  setQuery: (q) => set({ query: q }),
  addHistory: (q) => {
    if (!q.trim()) return
    const next = [q, ...get().history.filter((h) => h !== q)].slice(0, 20)
    saveHistory(next)
    set({ history: next })
  },
  clearHistory: () => {
    saveHistory([])
    set({ history: [] })
  },
}))
