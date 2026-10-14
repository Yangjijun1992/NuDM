"use client"

import type { PaperListItem } from "@/types"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { useFavoriteStore } from "@/stores/favorite"
import Link from "next/link"
import { Bookmark, ExternalLink } from "lucide-react"

interface PaperCardProps {
  paper: PaperListItem
}

export function PaperCard({ paper }: PaperCardProps) {
  const { isFavorited, toggleFavorite } = useFavoriteStore()
  const favorited = isFavorited(paper.id)

  const abstract = paper.abstract
    ? paper.abstract.length > 300
      ? paper.abstract.slice(0, 300) + "..."
      : paper.abstract
    : null

  const titleHtml = paper.highlights?.title?.[0] || paper.title
  const abstractHighlight = paper.highlights?.abstract?.[0] || paper.highlights?.abstract_en?.[0]

  const handleFavorite = (e: React.MouseEvent) => {
    e.preventDefault()
    toggleFavorite(paper.id)
  }

  return (
    <Card className="group transition-shadow hover:shadow-md">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <Link href={`/papers/${paper.id}`} prefetch={false} className="flex-1 min-w-0">
            <CardTitle
              className="text-base font-medium leading-snug transition-colors group-hover:text-primary truncate"
              dangerouslySetInnerHTML={{ __html: titleHtml }}
            />
          </Link>
          <button
            onClick={handleFavorite}
            className="flex-shrink-0 rounded p-1 transition-colors hover:bg-accent"
            title={favorited ? "取消收藏" : "收藏"}
          >
            <Bookmark
              className={`h-4 w-4 ${favorited ? "fill-primary text-primary" : "text-muted-foreground"}`}
            />
          </button>
        </div>
        {paper.title_en && paper.title_en !== paper.title && (
          <CardDescription className="text-xs">{paper.title_en}</CardDescription>
        )}
      </CardHeader>
      <CardContent className="space-y-3">
        {(abstractHighlight || abstract) && (
          <p
            className="text-sm leading-relaxed text-muted-foreground"
            dangerouslySetInnerHTML={{ __html: abstractHighlight || abstract || "" }}
          />
        )}
        <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
          {paper.arxiv_id && (
            <a
              href={`https://arxiv.org/abs/${paper.arxiv_id}`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 rounded bg-muted px-2 py-0.5 transition-colors hover:bg-muted/80"
            >
              arXiv:{paper.arxiv_id}
              <ExternalLink className="h-3 w-3" />
            </a>
          )}
          {paper.publish_date && (
            <span className="rounded bg-muted px-2 py-0.5">
              {new Date(paper.publish_date).toLocaleDateString("zh-CN")}
            </span>
          )}
          {paper.citation_count > 0 && (
            <span className="rounded bg-muted px-2 py-0.5">引用 {paper.citation_count}</span>
          )}
          {paper.relevance_score != null && (
            <Badge variant="secondary" className="text-xs">
              相关度 {Math.round(paper.relevance_score * 100)}%
            </Badge>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
