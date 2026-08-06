"use client"

import { use, useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Skeleton } from "@/components/ui/skeleton"
import { PaperCard } from "@/components/paper-card"
import { api } from "@/lib/api"
import { useFavoriteStore } from "@/stores/favorite"
import type { TopicDetail, PaperListItem, PaginatedResponse, Experiment } from "@/types"
import Link from "next/link"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"

interface TrendItem {
  label: string
  count: number
}

export default function TopicDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = use(params)
  const [topic, setTopic] = useState<TopicDetail | null>(null)
  const [papers, setPapers] = useState<PaginatedResponse<PaperListItem> | null>(null)
  const [trends, setTrends] = useState<TrendItem[]>([])
  const [loading, setLoading] = useState(true)
  const { fetchFavorites } = useFavoriteStore()

  useEffect(() => {
    fetchFavorites()
    async function load() {
      try {
        const [topicData, papersData, trendData] = await Promise.all([
          api.topics.detail(slug),
          api.papers.list({ topic_slug: slug, page_size: 50, sort: "date" }),
          api.get<{ slug: string; trends: TrendItem[] }>(`/topics/${slug}/trend`),
        ])
        setTopic(topicData)
        setPapers(papersData)
        setTrends(trendData.trends || [])
      } catch (e) {
        console.error("Failed to load topic:", e)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [slug])

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Skeleton className="h-8 w-48 mb-2" />
        <Skeleton className="h-5 w-96 mb-8" />
        <Skeleton className="h-12 w-64 mb-6" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (!topic) {
    return (
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold">专题未找到</h1>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <Link href="/topics" className="text-sm text-muted-foreground hover:text-foreground mb-2 inline-block">
          ← 返回专题列表
        </Link>
        <h1 className="text-3xl font-bold mb-2">{topic.name}</h1>
        <p className="text-muted-foreground max-w-3xl">{topic.description}</p>
      </div>

      <Tabs defaultValue="papers" className="w-full">
        <TabsList>
          <TabsTrigger value="papers">论文列表 ({topic.paper_count})</TabsTrigger>
          <TabsTrigger value="experiments">
            实验组 ({topic.experiments.length})
          </TabsTrigger>
          <TabsTrigger value="trends">趋势</TabsTrigger>
        </TabsList>

        <TabsContent value="papers" className="mt-6">
          <div className="space-y-4">
            {topic.keywords && topic.keywords.length > 0 && (
              <div className="flex flex-wrap gap-1 mb-4">
                {topic.keywords.map((kw) => (
                  <Badge key={kw} variant="secondary" className="text-xs">{kw}</Badge>
                ))}
              </div>
            )}
            {papers && papers.items.length > 0 ? (
              papers.items.map((paper) => (
                <PaperCard key={paper.id} paper={paper} />
              ))
            ) : (
              <Card>
                <CardContent className="py-8 text-center text-muted-foreground">
                  该专题暂无论文，等待数据抓取...
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        <TabsContent value="experiments" className="mt-6">
          {topic.experiments.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {topic.experiments.map((exp) => (
                <Card key={exp.id}>
                  <CardHeader>
                    <CardTitle className="text-base">{exp.name}</CardTitle>
                    {exp.full_name && exp.full_name !== exp.name && (
                      <CardDescription className="text-xs">{exp.full_name}</CardDescription>
                    )}
                  </CardHeader>
                  <CardContent>
                    {exp.description ? (
                      <p className="text-sm text-muted-foreground line-clamp-2">{exp.description}</p>
                    ) : (
                      <p className="text-sm text-muted-foreground">实验组信息</p>
                    )}
                    {exp.website && (
                      <a
                        href={exp.website}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-primary hover:underline mt-1 inline-block"
                      >
                        访问官网
                      </a>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground">
                暂无相关实验组
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="trends" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">论文发表趋势（按月）</CardTitle>
              <CardDescription>该专题论文随时间变化情况</CardDescription>
            </CardHeader>
            <CardContent>
              {trends.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={trends} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                    <XAxis
                      dataKey="label"
                      className="text-xs"
                      tick={{ fontSize: 11 }}
                      angle={-45}
                      textAnchor="end"
                      height={60}
                    />
                    <YAxis className="text-xs" tick={{ fontSize: 11 }} allowDecimals={false} />
                    <Tooltip
                      contentStyle={{
                        borderRadius: "8px",
                        border: "1px solid var(--border)",
                        background: "var(--background)",
                      }}
                    />
                    <Bar dataKey="count" fill="var(--primary)" radius={[4, 4, 0, 0]} name="论文数" />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="py-12 text-center text-muted-foreground">
                  暂无趋势数据，论文入库后将自动生成
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
