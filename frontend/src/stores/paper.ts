import { create } from "zustand"
import type { PaperListItem } from "@/types"
import { api } from "@/lib/api"

interface PaperState {
  papers: PaperListItem[]
  total: number
  page: number
  pageSize: number
  sort: string
  topicSlug: string | undefined
  loading: boolean
  fetchPapers: (params?: { topic_slug?: string; page?: number; sort?: string }) => Promise<void>
  setPage: (page: number) => void
  setSort: (sort: string) => void
}

export const usePaperStore = create<PaperState>((set, get) => ({
  papers: [],
  total: 0,
  page: 1,
  pageSize: 20,
  sort: "date",
  topicSlug: undefined,
  loading: false,

  fetchPapers: async (params) => {
    set({ loading: true })
    try {
      const res = await api.papers.list({
        topic_slug: params?.topic_slug,
        page: params?.page ?? get().page,
        page_size: get().pageSize,
        sort: params?.sort ?? get().sort,
      })
      set({
        papers: res.items,
        total: res.total,
        page: res.page,
        topicSlug: params?.topic_slug,
        sort: params?.sort ?? get().sort,
      })
    } catch {
      // silent
    } finally {
      set({ loading: false })
    }
  },

  setPage: (page) => set({ page }),
  setSort: (sort) => set({ sort }),
}))
