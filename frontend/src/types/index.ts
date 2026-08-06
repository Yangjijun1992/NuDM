export interface Topic {
  id: string
  name: string
  slug: string
  description: string | null
  parent_id: string | null
  sort_order: number
  icon: string | null
  keywords: string[] | null
  paper_count: number
  is_active: boolean
  created_at: string
}

export interface TopicDetail extends Topic {
  experiments: Experiment[]
}

export interface Experiment {
  id: string
  name: string
  full_name: string | null
  description: string | null
  topic_id: string | null
  website: string | null
  is_active: boolean
  created_at: string
}

export interface AuthorBrief {
  id: string
  name: string
  name_normalized: string
  affiliation: string | null
  orcid: string | null
}

export interface AuthorOnPaper extends AuthorBrief {
  order: number
}

export interface AISummaryBrief {
  summary_cn: string | null
  summary_en: string | null
  contribution: string | null
  method: string | null
  result: string | null
  keywords_extracted: string[] | null
}

export interface PaperListItem {
  id: string
  title: string
  title_en: string | null
  abstract: string | null
  doi: string | null
  arxiv_id: string | null
  publish_date: string | null
  citation_count: number
  language: string
  relevance_score: number | null
  hot_score: number | null
  is_hidden?: boolean
  highlights?: Record<string, string[]> | null
  created_at: string
}

export interface PaperDetail {
  id: string
  title: string
  title_en: string | null
  abstract: string | null
  abstract_en: string | null
  doi: string | null
  arxiv_id: string | null
  publish_date: string | null
  citation_count: number
  pdf_url: string | null
  source_url: string | null
  language: string
  relevance_score: number | null
  hot_score: number | null
  created_at: string
  updated_at: string
  authors: AuthorOnPaper[]
  topics: { id: string; name: string; slug: string }[]
  ai_summary: AISummaryBrief | null
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface User {
  id: string
  email: string
  username: string
  avatar_url: string | null
  role: "user" | "admin"
  created_at: string
}

export interface FavoriteItem {
  id: string
  note: string | null
  created_at: string
  paper: {
    id: string
    title: string
    arxiv_id: string | null
    publish_date: string | null
  }
}

export interface Subscription {
  id: string
  type: "topic" | "keyword" | "experiment"
  target_id: string | null
  keyword: string | null
  frequency: "daily" | "weekly" | "instant"
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface SubscriptionCreate {
  type: string
  target_id?: string | null
  keyword?: string | null
  frequency?: string
}

export interface Notification {
  id: string
  type: string
  title: string
  content: string | null
  reference_id: string | null
  reference_type: string | null
  is_read: boolean
  created_at: string
  read_at: string | null
}

export interface AdminStats {
  paper_count: number
  user_count: number
  source_count: number
}

export interface CrawlTask {
  id: string
  source_id: string
  keyword: string
  status: string
  papers_fetched: number
  papers_new: number
  error_message: string | null
  started_at: string | null
  finished_at: string | null
  created_at: string
}

export interface DataSource {
  id: string
  name: string
  base_url: string
  api_type: string
  rate_limit: number
  is_active: boolean
  config: object | null
  created_at: string
}

export interface AISummaryAdmin {
  id: string
  paper_id: string
  summary_cn: string | null
  summary_en: string | null
  contribution: string | null
  method: string | null
  result: string | null
  keywords_extracted: string[] | null
  quality_flag: string
  model: string | null
  tokens_used: number | null
  generated_at: string
  reviewed_by: string | null
  reviewed_at: string | null
}

export interface SearchParams {
  q?: string
  topic?: string
  author?: string
  date_from?: string
  date_to?: string
  page?: number
  page_size?: number
  sort?: "relevance" | "date" | "citations" | "hot"
}
