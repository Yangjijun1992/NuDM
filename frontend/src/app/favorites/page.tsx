"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { api } from "@/lib/api"
import type { FavoriteItem } from "@/types"
import { Bookmark, ExternalLink, Trash2 } from "lucide-react"

export default function FavoritesPage() {
  const [favorites, setFavorites] = useState<FavoriteItem[]>([])
  const [loading, setLoading] = useState(true)

  const loadFavorites = async () => {
    setLoading(true)
    try {
      const data = await api.favorites.list()
      setFavorites(data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadFavorites()
  }, [])

  const handleRemove = async (paperId: string) => {
    await api.favorites.remove(paperId)
    setFavorites((prev) => prev.filter((f) => f.paper.id !== paperId))
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-2">我的收藏</h1>
      <p className="text-muted-foreground mb-8">你收藏的论文将显示在这里</p>

      {loading ? (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-24 rounded-xl" />
          ))}
        </div>
      ) : favorites.length > 0 ? (
        <div className="space-y-3">
          {favorites.map((fav) => (
            <Card key={fav.id}>
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between gap-2">
                  <CardTitle className="text-base font-medium leading-snug">
                    {fav.paper.title}
                  </CardTitle>
                  <Button
                    variant="ghost"
                    size="icon-sm"
                    onClick={() => handleRemove(fav.paper.id)}
                    className="flex-shrink-0 text-muted-foreground hover:text-destructive"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-3 text-xs text-muted-foreground">
                  {fav.paper.arxiv_id && (
                    <a
                      href={`https://arxiv.org/abs/${fav.paper.arxiv_id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 rounded bg-muted px-2 py-0.5 hover:bg-muted/80"
                    >
                      arXiv:{fav.paper.arxiv_id}
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  )}
                  {fav.paper.publish_date && (
                    <span>{new Date(fav.paper.publish_date).toLocaleDateString("zh-CN")}</span>
                  )}
                  <span>收藏于 {new Date(fav.created_at).toLocaleDateString("zh-CN")}</span>
                </div>
                {fav.note && (
                  <p className="text-sm text-muted-foreground mt-2">{fav.note}</p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            <Bookmark className="mx-auto h-8 w-8 mb-3 opacity-50" />
            <p className="mb-4">暂无收藏论文</p>
            <Button variant="outline" onClick={() => window.location.href = "/search"}>
              去浏览论文
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
