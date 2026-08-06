"use client"

import { use, useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Separator } from "@/components/ui/separator"
import { api, ApiError } from "@/lib/api"
import { useFavoriteStore } from "@/stores/favorite"
import type { PaperDetail } from "@/types"
import Link from "next/link"
import { ExternalLink, Bookmark, Calendar, Quote, FileText } from "lucide-react"

export default function PaperDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const [paper, setPaper] = useState<PaperDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const { isFavorited: checkFavorited, toggleFavorite, fetchFavorites } = useFavoriteStore()

  useEffect(() => {
    fetchFavorites()
    async function load() {
      try {
        const data = await api.papers.detail(id)
        setPaper(data)
      } catch (e) {
        if (e instanceof ApiError && e.status === 404) {
          setError("论文未找到")
        } else {
          setError("加载失败，请稍后重试")
        }
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [id])

  const handleFavorite = async () => {
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null
    if (!token) return
    await toggleFavorite(id)
  }

  const favorited = checkFavorited(id)

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <Skeleton className="h-10 w-2/3 mb-4" />
        <Skeleton className="h-6 w-1/3 mb-8" />
        <Skeleton className="h-40 w-full mb-6" />
        <Skeleton className="h-60 w-full" />
      </div>
    )
  }

  if (error || !paper) {
    return (
      <div className="container mx-auto px-4 py-16 text-center">
        <p className="text-lg text-muted-foreground mb-4">{error || "论文未找到"}</p>
        <Link href="/search">
          <Button variant="outline">返回搜索</Button>
        </Link>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <Link href="/search" className="text-sm text-muted-foreground hover:text-foreground mb-4 inline-block">
        ← 返回列表
      </Link>

      <div className="flex items-start justify-between gap-4 mb-6">
        <div className="flex-1">
          <h1 className="text-2xl font-bold leading-snug">{paper.title}</h1>
          {paper.title_en && paper.title_en !== paper.title && (
            <p className="text-sm text-muted-foreground mt-1">{paper.title_en}</p>
          )}
        </div>
        <Button
          variant={favorited ? "default" : "outline"}
          size="sm"
          onClick={handleFavorite}
          className="flex-shrink-0"
        >
          <Bookmark className={`h-4 w-4 mr-1 ${favorited ? "fill-primary-foreground" : ""}`} />
          {favorited ? "已收藏" : "收藏"}
        </Button>
      </div>

      <div className="flex flex-wrap items-center gap-3 mb-6 text-sm text-muted-foreground">
        {paper.arxiv_id && (
          <a
            href={`https://arxiv.org/abs/${paper.arxiv_id}`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 rounded-full bg-muted px-3 py-1 hover:bg-muted/80 transition-colors"
          >
            <FileText className="h-3.5 w-3.5" />
            arXiv:{paper.arxiv_id}
            <ExternalLink className="h-3 w-3" />
          </a>
        )}
        {paper.publish_date && (
          <span className="inline-flex items-center gap-1">
            <Calendar className="h-3.5 w-3.5" />
            {new Date(paper.publish_date).toLocaleDateString("zh-CN", {
              year: "numeric",
              month: "long",
              day: "numeric",
            })}
          </span>
        )}
        {paper.citation_count > 0 && (
          <span className="inline-flex items-center gap-1">
            <Quote className="h-3.5 w-3.5" />
            引用 {paper.citation_count}
          </span>
        )}
      </div>

      {paper.topics.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-6">
          {paper.topics.map((t) => (
            <Link key={t.id} href={`/topics/${t.slug}`}>
              <Badge variant="secondary" className="cursor-pointer hover:bg-secondary/80">
                {t.name}
              </Badge>
            </Link>
          ))}
        </div>
      )}

      {paper.authors.length > 0 && (
        <Card className="mb-6">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">作者</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm">
              {paper.authors
                .sort((a, b) => a.order - b.order)
                .map((author, i) => (
                  <span key={author.id || i} className="text-muted-foreground">
                    {author.name}
                    {author.affiliation && (
                      <span className="text-xs ml-1 opacity-70">({author.affiliation})</span>
                    )}
                    {i < paper.authors.length - 1 && ", "}
                  </span>
                ))}
            </div>
          </CardContent>
        </Card>
      )}

      <Card className="mb-6">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">摘要</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm leading-relaxed text-muted-foreground">
            {paper.abstract || "暂无摘要"}
          </p>
        </CardContent>
      </Card>

      {paper.ai_summary && (
        <Card className="mb-6 border-primary/30">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <span className="inline-flex items-center rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary">
                AI 解读
              </span>
              结构化摘要
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {paper.ai_summary.summary_cn && (
              <div>
                <h4 className="text-xs font-medium text-muted-foreground mb-1">中文摘要</h4>
                <p className="text-sm">{paper.ai_summary.summary_cn}</p>
              </div>
            )}
            {paper.ai_summary.summary_en && (
              <div>
                <h4 className="text-xs font-medium text-muted-foreground mb-1">English Summary</h4>
                <p className="text-sm">{paper.ai_summary.summary_en}</p>
              </div>
            )}
            {paper.ai_summary.contribution && (
              <div>
                <h4 className="text-xs font-medium text-muted-foreground mb-1">主要贡献</h4>
                <p className="text-sm">{paper.ai_summary.contribution}</p>
              </div>
            )}
            {paper.ai_summary.method && (
              <div>
                <h4 className="text-xs font-medium text-muted-foreground mb-1">方法</h4>
                <p className="text-sm">{paper.ai_summary.method}</p>
              </div>
            )}
            {paper.ai_summary.result && (
              <div>
                <h4 className="text-xs font-medium text-muted-foreground mb-1">结果</h4>
                <p className="text-sm">{paper.ai_summary.result}</p>
              </div>
            )}
            {paper.ai_summary.keywords_extracted && paper.ai_summary.keywords_extracted.length > 0 && (
              <div>
                <h4 className="text-xs font-medium text-muted-foreground mb-1">AI 提取关键词</h4>
                <div className="flex flex-wrap gap-1">
                  {paper.ai_summary.keywords_extracted.map((kw) => (
                    <Badge key={kw} variant="outline" className="text-xs">{kw}</Badge>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {paper.pdf_url && (
        <div className="flex gap-3">
          <a href={paper.pdf_url} target="_blank" rel="noopener noreferrer">
            <Button variant="outline" size="sm">
              <FileText className="h-4 w-4 mr-1" />
              查看 PDF
            </Button>
          </a>
          {paper.source_url && (
            <a href={paper.source_url} target="_blank" rel="noopener noreferrer">
              <Button variant="outline" size="sm">
                <ExternalLink className="h-4 w-4 mr-1" />
                原文链接
              </Button>
            </a>
          )}
        </div>
      )}
    </div>
  )
}
