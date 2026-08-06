import { create } from "zustand"
import type { User } from "@/types"
import { api } from "@/lib/api"

interface AuthState {
  user: User | null
  token: string | null
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, username: string, password: string) => Promise<void>
  logout: () => void
  fetchUser: () => Promise<void>
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: typeof window !== "undefined" ? localStorage.getItem("token") : null,
  isLoading: false,

  login: async (email, password) => {
    const data = await api.post<{ access_token: string; user: User }>("/auth/login", {
      email,
      password,
    })
    localStorage.setItem("token", data.access_token)
    document.cookie = `token=${data.access_token}; path=/; max-age=${7 * 24 * 60 * 60}; SameSite=Lax`
    set({ token: data.access_token, user: data.user })
  },

  register: async (email, username, password) => {
    await api.post("/auth/register", { email, username, password })
  },

  logout: () => {
    localStorage.removeItem("token")
    document.cookie = "token=; path=/; max-age=0"
    set({ token: null, user: null })
  },

  fetchUser: async () => {
    try {
      set({ isLoading: true })
      const user = await api.get<User>("/users/me")
      set({ user })
    } catch {
      set({ user: null, token: null })
    } finally {
      set({ isLoading: false })
    }
  },
}))
