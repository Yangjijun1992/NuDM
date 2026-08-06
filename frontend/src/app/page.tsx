"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { api } from "@/lib/api"
import { TopicCard } from "@/components/topic-card"
import { PaperCard } from "@/components/paper-card"
import { Skeleton } from "@/components/ui/skeleton"
import { useFavoriteStore } from "@/stores/favorite"
import type { Topic, PaperListItem } from "@/types"

export default function HomePage() {
  const [topics, setTopics] = useState<Topic[]>([])
  const [papers, setPapers] = useState<PaperListItem[]>([])
  const [loading, setLoading] = useState(true)
  const { fetchFavorites } = useFavoriteStore()

  useEffect(() => {
    fetchFavorites()
    async function load() {
      try {
        const [topicsData, papersData] = await Promise.all([
          api.topics.list(),
          api.papers.list({ page_size: 8, sort: "date" }),
        ])
        setTopics(topicsData)
        setPapers(papersData.items)
      } catch (e) {
        console.error("Failed to load homepage data:", e)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  return (
    <div className="container mx-auto px-4 py-12">
      <section className="text-center mb-16">
        <h1 className="text-4xl font-bold tracking-tight mb-4">
          粒子物理论文追踪平台
        </h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-8">
          聚焦暗物质与中微子前沿，自动追踪最新论文，AI 结构化解读
        </p>
        <div className="flex items-center justify-center gap-4">
          <Link href="/topics">
            <Button size="lg">浏览专题</Button>
          </Link>
          <Link href="/search">
            <Button variant="outline" size="lg">
              搜索论文
            </Button>
          </Link>
        </div>
      </section>

      <section className="mb-16">
        <h2 className="text-2xl font-semibold mb-6">研究专题</h2>
        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {Array.from({ length: 8 }).map((_, i) => (
              <Skeleton key={i} className="h-40 rounded-xl" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {topics.map((topic) => (
              <TopicCard key={topic.id} topic={topic} />
            ))}
          </div>
        )}
      </section>

      <section>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-semibold">最新论文</h2>
          <Link href="/search">
            <Button variant="ghost" size="sm">
              查看全部 →
            </Button>
          </Link>
        </div>
        {loading ? (
          <div className="space-y-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-32 rounded-xl" />
            ))}
          </div>
        ) : papers.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            暂无论文数据，请等待数据抓取完成后查看
          </div>
        ) : (
          <div className="space-y-4">
            {papers.map((paper) => (
              <PaperCard key={paper.id} paper={paper} />
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
