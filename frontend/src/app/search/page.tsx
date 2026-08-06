"use client"

import { useEffect, useState } from "react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Separator } from "@/components/ui/separator"
import { Skeleton } from "@/components/ui/skeleton"
import { PaperCard } from "@/components/paper-card"
import { Pagination, PaginationContent, PaginationItem, PaginationLink, PaginationNext, PaginationPrevious } from "@/components/ui/pagination"
import { api } from "@/lib/api"
import { useFavoriteStore } from "@/stores/favorite"
import type { Topic, PaperListItem, PaginatedResponse } from "@/types"

export default function SearchPage() {
  const [query, setQuery] = useState("")
  const [topicSlug, setTopicSlug] = useState("")
  const [sort, setSort] = useState("date")
  const [page, setPage] = useState(1)
  const [topics, setTopics] = useState<Topic[]>([])
  const [result, setResult] = useState<PaginatedResponse<PaperListItem> | null>(null)
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)
  const { fetchFavorites } = useFavoriteStore()

  useEffect(() => {
    api.topics.list().then(setTopics)
    fetchFavorites()
  }, [])

  const handleSearch = async (p?: number, keywordOverride?: string) => {
    const currentPage = p ?? 1
    const searchQuery = keywordOverride ?? query
    setLoading(true)
    setSearched(true)
    try {
      const res = await api.search({
        q: searchQuery || undefined,
        topic: topicSlug || undefined,
        sort: sort as "date" | "relevance" | "citations" | "hot",
        page: currentPage,
        page_size: 20,
      })
      setResult(res)
      setPage(currentPage)
    } catch (e) {
      console.error("Search failed:", e)
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") handleSearch()
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">搜索论文</h1>
        <p className="text-muted-foreground">按关键词、作者、专题搜索论文</p>
      </div>

      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <div className="flex-1">
          <Input
            placeholder="输入关键词、标题或作者..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            className="w-full"
          />
        </div>
        <Select value={topicSlug} onValueChange={(v) => setTopicSlug(v === "all" ? "" : (v ?? ""))}>
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="选择专题" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">全部专题</SelectItem>
            {topics.map((t) => (
              <SelectItem key={t.slug} value={t.slug}>{t.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={sort} onValueChange={(v) => setSort(v ?? "date")}>
          <SelectTrigger className="w-[150px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="date">最新发布</SelectItem>
            <SelectItem value="relevance">相关度</SelectItem>
            <SelectItem value="citations">引用数</SelectItem>
            <SelectItem value="hot">热度</SelectItem>
          </SelectContent>
        </Select>
        <Button onClick={() => handleSearch()} disabled={loading}>
          {loading ? "搜索中..." : "搜索"}
        </Button>
      </div>

      <Separator className="mb-6" />

      <div className="flex items-center gap-2 mb-6">
        <span className="text-sm text-muted-foreground">快速搜索：</span>
        {["dark matter", "WIMP", "neutrino", "axion", "sterile"].map((kw) => (
          <Badge
            key={kw}
            variant="secondary"
            className="cursor-pointer"
            onClick={() => { setQuery(kw); handleSearch(1, kw) }}
          >
            {kw}
          </Badge>
        ))}
      </div>

      {loading ? (
        <div className="space-y-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-32 rounded-xl" />
          ))}
        </div>
      ) : searched && result ? (
        <>
          <p className="text-sm text-muted-foreground mb-4">
            找到 {result.total} 篇论文
          </p>
          {result.items.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              未找到匹配的论文
            </div>
          ) : (
            <>
              <div className="space-y-4">
                {result.items.map((paper) => (
                  <PaperCard key={paper.id} paper={paper} />
                ))}
              </div>
              {result.total_pages > 1 && (
                <Pagination className="mt-8">
                  <PaginationContent>
                    <PaginationItem>
                      <PaginationPrevious
                        onClick={() => page > 1 && handleSearch(page - 1)}
                        className={page <= 1 ? "pointer-events-none opacity-50" : "cursor-pointer"}
                      />
                    </PaginationItem>
                    {Array.from({ length: Math.min(result.total_pages, 5) }).map((_, i) => {
                      const pn = i + 1 + Math.max(0, page - 3)
                      return (
                        <PaginationItem key={pn}>
                          <PaginationLink
                            onClick={() => handleSearch(pn)}
                            isActive={pn === page}
                            className="cursor-pointer"
                          >
                            {pn}
                          </PaginationLink>
                        </PaginationItem>
                      )
                    })}
                    <PaginationItem>
                      <PaginationNext
                        onClick={() => page < result.total_pages && handleSearch(page + 1)}
                        className={page >= result.total_pages ? "pointer-events-none opacity-50" : "cursor-pointer"}
                      />
                    </PaginationItem>
                  </PaginationContent>
                </Pagination>
              )}
            </>
          )}
        </>
      ) : (
        <div className="text-center py-12 text-muted-foreground">
          输入关键词开始搜索
        </div>
      )}
    </div>
  )
}
