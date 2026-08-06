import { create } from "zustand"
import type { Topic } from "@/types"
import { api } from "@/lib/api"

interface TopicState {
  topics: Topic[]
  loading: boolean
  fetchTopics: () => Promise<void>
}

export const useTopicStore = create<TopicState>((set, get) => ({
  topics: [],
  loading: false,

  fetchTopics: async () => {
    if (get().topics.length > 0) return
    set({ loading: true })
    try {
      const topics = await api.topics.list()
      set({ topics })
    } catch {
      // silent
    } finally {
      set({ loading: false })
    }
  },
}))
