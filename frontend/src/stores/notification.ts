import { create } from "zustand"
import { api } from "@/lib/api"

interface NotificationState {
  unreadCount: number
  fetchUnreadCount: () => Promise<void>
}

export const useNotificationStore = create<NotificationState>((set) => ({
  unreadCount: 0,

  fetchUnreadCount: async () => {
    try {
      const data = await api.notifications.unreadCount()
      set({ unreadCount: data.count })
    } catch {
      // silent
    }
  },
}))
