import type {
  PaginatedResponse,
  PaperListItem,
  PaperDetail,
  Topic,
  TopicDetail,
  Experiment,
  FavoriteItem,
  Subscription,
  SubscriptionCreate,
  Notification,
  SearchParams,
  AdminStats,
  CrawlTask,
  DataSource,
  AISummaryAdmin,
} from "@/types"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null

  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  }
  if (token) {
    headers["Authorization"] = `Bearer ${token}`
  }
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json"
  }

  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  })

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Request failed" }))
    throw new ApiError(error.detail || "Request failed", res.status)
  }

  return res.json()
}

function buildQuery(params: Record<string, string | number | boolean | undefined | null>): string {
  const searchParams = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") {
      searchParams.set(key, String(value))
    }
  }
  const qs = searchParams.toString()
  return qs ? `?${qs}` : ""
}

export const api = {
  get: <T>(endpoint: string) => request<T>(endpoint),
  post: <T>(endpoint: string, data?: unknown) =>
    request<T>(endpoint, { method: "POST", body: JSON.stringify(data) }),
  put: <T>(endpoint: string, data?: unknown) =>
    request<T>(endpoint, { method: "PUT", body: JSON.stringify(data) }),
  patch: <T>(endpoint: string, data?: unknown) =>
    request<T>(endpoint, { method: "PATCH", body: JSON.stringify(data) }),
  delete: <T>(endpoint: string) => request<T>(endpoint, { method: "DELETE" }),

  papers: {
    list: (params?: {
      topic_slug?: string
      page?: number
      page_size?: number
      sort?: string
    }) => api.get<PaginatedResponse<PaperListItem>>(`/papers${buildQuery(params || {})}`),
    detail: (id: string) => api.get<PaperDetail>(`/papers/${id}`),
  },

  topics: {
    list: () => api.get<Topic[]>("/topics"),
    detail: (slug: string) => api.get<TopicDetail>(`/topics/${slug}`),
  },

  experiments: {
    list: (topicSlug?: string) =>
      api.get<Experiment[]>(`/topics/experiments/list${topicSlug ? `?topic_slug=${topicSlug}` : ""}`),
  },

  search: (params: SearchParams) =>
    api.get<PaginatedResponse<PaperListItem>>(`/search${buildQuery(params as Record<string, string | number | boolean | undefined | null>)}`),

  favorites: {
    list: () => api.get<FavoriteItem[]>("/favorites"),
    add: (paperId: string) => api.post<{ message: string; id: string }>(`/favorites/${paperId}`),
    remove: (paperId: string) => api.delete<{ message: string }>(`/favorites/${paperId}`),
  },

  subscriptions: {
    list: () => api.get<Subscription[]>("/subscriptions"),
    create: (data: SubscriptionCreate) => api.post<Subscription>("/subscriptions", data),
    update: (id: string, data: Partial<SubscriptionCreate & { is_active: boolean }>) =>
      api.patch<Subscription>(`/subscriptions/${id}`, data),
    delete: (id: string) => api.delete(`/subscriptions/${id}`),
  },

  notifications: {
    list: (params?: { is_read?: boolean; page?: number; page_size?: number }) =>
      api.get<PaginatedResponse<Notification>>(`/notifications${buildQuery(params || {})}`),
    unreadCount: () => api.get<{ count: number }>("/notifications/unread-count"),
    markRead: (id: string) => api.post(`/notifications/${id}/read`),
    markAllRead: () => api.post("/notifications/read-all"),
  },

  admin: {
    stats: () => api.get<AdminStats>("/admin/stats"),
    crawlTasks: () => api.get<CrawlTask[]>("/admin/crawl-tasks"),
    dataSources: () => api.get<DataSource[]>("/admin/data-sources"),
    createDataSource: (data: Partial<DataSource>) => api.post<DataSource>("/admin/data-sources", data),
    updateDataSource: (id: string, data: Partial<DataSource>) =>
      api.patch<DataSource>(`/admin/data-sources/${id}`, data),
    triggerArxivCrawl: () => api.post<{ task_id: string; message: string }>("/admin/crawl/arxiv"),
    triggerInspireCrawl: () => api.post<{ task_id: string; message: string }>("/admin/crawl/inspire"),
    triggerFullCrawl: () => api.post<{ task_id: string; message: string }>("/admin/crawl/all"),
    triggerSummarize: (limit?: number) =>
      api.post<{ task_id: string; message: string }>(`/admin/ai/summarize?limit=${limit || 20}`),
    triggerRegenerate: (limit?: number) =>
      api.post<{ task_id: string; message: string }>(`/admin/ai/regenerate-summaries?limit=${limit || 20}`),
    triggerClassify: (limit?: number) =>
      api.post<{ task_id: string; message: string }>(`/admin/ai/classify?limit=${limit || 50}`),
    aiSummaries: (params?: { quality_flag?: string }) =>
      api.get<AISummaryAdmin[]>(`/admin/ai-summaries${buildQuery(params || {})}`),
    updateAISummary: (id: string, data: Record<string, unknown>) =>
      api.patch<AISummaryAdmin>(`/admin/ai-summaries/${id}`, data),
  },
}

export { ApiError }
