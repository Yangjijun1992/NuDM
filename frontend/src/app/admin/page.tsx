"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { api } from "@/lib/api"
import type { AdminStats, CrawlTask, DataSource, AISummaryAdmin, Topic, PaperListItem, PaginatedResponse } from "@/types"

export default function AdminPage() {
  const [stats, setStats] = useState<AdminStats | null>(null)
  const [dataSources, setDataSources] = useState<DataSource[]>([])
  const [crawlTasks, setCrawlTasks] = useState<CrawlTask[]>([])
  const [papers, setPapers] = useState<PaginatedResponse<PaperListItem> | null>(null)
  const [aiSummaries, setAiSummaries] = useState<AISummaryAdmin[]>([])
  const [topics, setTopics] = useState<Topic[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const [s, ds, ct, ais, ts] = await Promise.all([
          api.admin.stats(),
          api.admin.dataSources(),
          api.admin.crawlTasks(),
          api.admin.aiSummaries({ quality_flag: "unreviewed" }),
          api.topics.list(),
        ])
        setStats(s)
        setDataSources(ds)
        setCrawlTasks(ct)
        setAiSummaries(ais)
        setTopics(ts)
      } catch (e) {
        console.error("Admin load error:", e)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const loadPapers = async () => {
    try {
      const p = await api.get<PaginatedResponse<PaperListItem>>("/admin/papers?page_size=20")
      setPapers(p)
    } catch (e) {
      console.error(e)
    }
  }

  const statusVariant = (status: string) => {
    switch (status) {
      case "success": return "default"
      case "running": return "secondary"
      case "failed": return "destructive"
      default: return "outline"
    }
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-2">后台管理</h1>
      {stats && (
        <div className="flex gap-4 mb-8 text-sm text-muted-foreground">
          <Badge variant="secondary">论文: {stats.paper_count}</Badge>
          <Badge variant="secondary">用户: {stats.user_count}</Badge>
          <Badge variant="secondary">数据源: {stats.source_count}</Badge>
        </div>
      )}

      <Tabs defaultValue="datasources">
        <TabsList className="mb-6 flex flex-wrap">
          <TabsTrigger value="datasources">数据源</TabsTrigger>
          <TabsTrigger value="tasks">抓取任务</TabsTrigger>
          <TabsTrigger value="papers" onClick={loadPapers}>论文管理</TabsTrigger>
          <TabsTrigger value="summaries">AI 摘要审核</TabsTrigger>
          <TabsTrigger value="topics">专题管理</TabsTrigger>
        </TabsList>

        <TabsContent value="datasources">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>数据源管理</CardTitle>
              <div className="flex gap-2">
                <Button size="sm" variant="outline" onClick={() => api.admin.triggerArxivCrawl().then(() => alert("arXiv 抓取已触发"))}>
                  触发 arXiv 抓取
                </Button>
                <Button size="sm" variant="outline" onClick={() => api.admin.triggerInspireCrawl().then(() => alert("INSPIRE 抓取已触发"))}>
                  触发 INSPIRE 抓取
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {dataSources.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>名称</TableHead>
                      <TableHead>类型</TableHead>
                      <TableHead>API 地址</TableHead>
                      <TableHead>频率限制</TableHead>
                      <TableHead>状态</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {dataSources.map((ds) => (
                      <TableRow key={ds.id}>
                        <TableCell className="font-medium">{ds.name}</TableCell>
                        <TableCell>{ds.api_type}</TableCell>
                        <TableCell className="text-xs text-muted-foreground">{ds.base_url}</TableCell>
                        <TableCell>{ds.rate_limit}/min</TableCell>
                        <TableCell>
                          <Badge variant={ds.is_active ? "default" : "secondary"}>
                            {ds.is_active ? "启用" : "停用"}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="py-8 text-center text-muted-foreground">暂无数据源</div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="tasks">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>抓取任务监控</CardTitle>
              <div className="flex gap-2">
                <Button size="sm" variant="outline" onClick={() => api.admin.triggerFullCrawl().then(() => alert("全量抓取已触发"))}>
                  触发全量抓取
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {crawlTasks.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>关键词</TableHead>
                      <TableHead>状态</TableHead>
                      <TableHead>抓取数</TableHead>
                      <TableHead>新增数</TableHead>
                      <TableHead>时间</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {crawlTasks.map((t) => (
                      <TableRow key={t.id}>
                        <TableCell className="text-xs">{t.keyword}</TableCell>
                        <TableCell>
                          <Badge variant={statusVariant(t.status)}>{t.status}</Badge>
                        </TableCell>
                        <TableCell>{t.papers_fetched}</TableCell>
                        <TableCell>{t.papers_new}</TableCell>
                        <TableCell className="text-xs text-muted-foreground">
                          {t.started_at ? new Date(t.started_at).toLocaleString("zh-CN") : "-"}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="py-8 text-center text-muted-foreground">
                  暂无抓取任务记录，点击上方按钮手动触发
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="papers">
          <Card>
            <CardHeader>
              <CardTitle>论文管理</CardTitle>
            </CardHeader>
            <CardContent>
              {papers && papers.items.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>标题</TableHead>
                      <TableHead>arXiv ID</TableHead>
                      <TableHead>发布日</TableHead>
                      <TableHead>隐藏</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {papers.items.map((p) => (
                      <TableRow key={p.id}>
                        <TableCell className="max-w-xs truncate text-sm">{p.title}</TableCell>
                        <TableCell className="text-xs">{p.arxiv_id}</TableCell>
                        <TableCell className="text-xs">{p.publish_date}</TableCell>
                        <TableCell>
                          <Badge variant={p.is_hidden ? "destructive" : "secondary"}>
                            {p.is_hidden ? "已隐藏" : "可见"}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="py-8 text-center text-muted-foreground">暂无论文数据</div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="summaries">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>AI 摘要审核</CardTitle>
              <div className="flex gap-2">
                <Button size="sm" variant="outline" onClick={() => api.admin.triggerSummarize(5).then((r) => alert(r.message))}>
                  生成摘要 (5篇)
                </Button>
                <Button size="sm" variant="outline" onClick={() =>
                  api.admin.triggerRegenerate(5).then((r) => alert(r.message))
                }>
                  重新生成 (5篇)
                </Button>
                <Button size="sm" variant="outline" onClick={() => api.admin.triggerClassify(10).then((r) => alert(r.message))}>
                  触发分类 (10篇)
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {aiSummaries.length > 0 ? (
                <div className="space-y-3">
                  {aiSummaries.map((s) => (
                    <Card key={s.id} className="p-4">
                      <div className="flex items-center justify-between mb-2">
                        <Badge variant={s.quality_flag === "approved" ? "default" : s.quality_flag === "rejected" ? "destructive" : "secondary"}>
                          {s.quality_flag}
                        </Badge>
                        <span className="text-xs text-muted-foreground">{s.model}</span>
                      </div>
                      {s.summary_cn && (
                        <p className="text-sm line-clamp-3 mb-2">{s.summary_cn}</p>
                      )}
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => api.admin.updateAISummary(s.id, { quality_flag: "approved" }).then(() => alert("已通过"))}
                        >
                          通过
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => api.admin.updateAISummary(s.id, { quality_flag: "rejected" }).then(() => alert("已驳回"))}
                        >
                          驳回
                        </Button>
                      </div>
                    </Card>
                  ))}
                </div>
              ) : (
                <div className="py-8 text-center text-muted-foreground">
                  暂无待审核摘要
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="topics">
          <Card>
            <CardHeader>
              <CardTitle>专题管理</CardTitle>
            </CardHeader>
            <CardContent>
              {topics.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>名称</TableHead>
                      <TableHead>Slug</TableHead>
                      <TableHead>论文数</TableHead>
                      <TableHead>状态</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {topics.map((t) => (
                      <TableRow key={t.id}>
                        <TableCell className="font-medium">{t.name}</TableCell>
                        <TableCell className="text-xs text-muted-foreground">{t.slug}</TableCell>
                        <TableCell>{t.paper_count}</TableCell>
                        <TableCell>
                          <Badge variant={t.is_active ? "default" : "secondary"}>
                            {t.is_active ? "活跃" : "停用"}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="py-8 text-center text-muted-foreground">暂无专题</div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
