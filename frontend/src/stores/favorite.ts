import { create } from "zustand"
import { api } from "@/lib/api"

interface FavoriteState {
  favoriteIds: Set<string>
  loading: boolean
  fetchFavorites: () => Promise<void>
  toggleFavorite: (paperId: string) => Promise<void>
  isFavorited: (paperId: string) => boolean
}

export const useFavoriteStore = create<FavoriteState>((set, get) => ({
  favoriteIds: new Set(),
  loading: false,

  fetchFavorites: async () => {
    set({ loading: true })
    try {
      const favs = await api.favorites.list()
      set({ favoriteIds: new Set(favs.map((f) => f.paper.id)) })
    } catch {
      // silent
    } finally {
      set({ loading: false })
    }
  },

  toggleFavorite: async (paperId) => {
    const ids = new Set(get().favoriteIds)
    if (ids.has(paperId)) {
      await api.favorites.remove(paperId)
      ids.delete(paperId)
    } else {
      await api.favorites.add(paperId)
      ids.add(paperId)
    }
    set({ favoriteIds: ids })
  },

  isFavorited: (paperId) => get().favoriteIds.has(paperId),
}))
