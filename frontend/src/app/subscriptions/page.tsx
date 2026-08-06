"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { api } from "@/lib/api"
import type { Subscription, Topic, SubscriptionCreate, Experiment } from "@/types"
import { Trash2, Plus } from "lucide-react"

export default function SubscriptionsPage() {
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([])
  const [topics, setTopics] = useState<Topic[]>([])
  const [experiments, setExperiments] = useState<Experiment[]>([])
  const [loading, setLoading] = useState(true)
  const [open, setOpen] = useState(false)
  const [subType, setSubType] = useState("topic")
  const [subKeyword, setSubKeyword] = useState("")
  const [subTargetId, setSubTargetId] = useState("")
  const [subFreq, setSubFreq] = useState("daily")

  const loadData = async () => {
    setLoading(true)
    try {
      const [subs, tops, exps] = await Promise.all([
        api.subscriptions.list(),
        api.topics.list(),
        api.experiments.list(),
      ])
      setSubscriptions(subs)
      setTopics(tops)
      setExperiments(exps)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleCreate = async () => {
    const data: SubscriptionCreate = {
      type: subType,
      frequency: subFreq,
    }
    if (subType === "keyword") {
      data.keyword = subKeyword
    } else {
      data.target_id = subTargetId
    }

    try {
      await api.subscriptions.create(data)
      setOpen(false)
      loadData()
    } catch (e) {
      console.error(e)
    }
  }

  const handleDelete = async (id: string) => {
    await api.subscriptions.delete(id)
    loadData()
  }

  const handleToggle = async (sub: Subscription) => {
    await api.subscriptions.update(sub.id, { is_active: !sub.is_active })
    loadData()
  }

  const typeLabel = (s: Subscription) => {
    if (s.type === "topic") {
      const t = topics.find((t) => t.id === s.target_id)
      return `专题: ${t?.name || s.target_id}`
    }
    if (s.type === "keyword") return `关键词: ${s.keyword}`
    return `实验组: ${s.target_id}`
  }

  const topicSubs = subscriptions.filter((s) => s.type === "topic")
  const keywordSubs = subscriptions.filter((s) => s.type === "keyword")
  const experimentSubs = subscriptions.filter((s) => s.type === "experiment")

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold mb-2">我的订阅</h1>
          <p className="text-muted-foreground">管理你关注的专题、关键词和实验组</p>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger>
            <Button>
              <Plus className="h-4 w-4 mr-1" />
              新增订阅
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>新增订阅</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div>
                <label className="text-sm font-medium mb-1 block">订阅类型</label>
                <Select value={subType} onValueChange={(v) => setSubType(v ?? "topic")}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="topic">专题</SelectItem>
                    <SelectItem value="keyword">关键词</SelectItem>
                    <SelectItem value="experiment">实验组</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              {subType === "keyword" ? (
                <div>
                  <label className="text-sm font-medium mb-1 block">关键词</label>
                  <Input
                    placeholder="输入关键词..."
                    value={subKeyword}
                    onChange={(e) => setSubKeyword(e.target.value)}
                  />
                </div>
              ) : (
                <div>
                  <label className="text-sm font-medium mb-1 block">
                    {subType === "topic" ? "选择专题" : "选择实验组"}
                  </label>
                  <Select value={subTargetId} onValueChange={(v) => setSubTargetId(v ?? "")}>
                    <SelectTrigger>
                      <SelectValue placeholder="请选择..." />
                    </SelectTrigger>
                    <SelectContent>
                      {(subType === "topic" ? topics : experiments).map((item) => (
                        <SelectItem key={item.id} value={item.id}>{item.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}
              <div>
                <label className="text-sm font-medium mb-1 block">通知频率</label>
                <Select value={subFreq} onValueChange={(v) => setSubFreq(v ?? "daily")}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="daily">每日</SelectItem>
                    <SelectItem value="weekly">每周</SelectItem>
                    <SelectItem value="instant">即时</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <Button className="w-full" onClick={handleCreate}>
                确认订阅
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-40 rounded-xl" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">专题订阅</CardTitle>
                <Badge variant="secondary">{topicSubs.length}</Badge>
              </div>
            </CardHeader>
            <CardContent>
              {topicSubs.length === 0 ? (
                <p className="text-sm text-muted-foreground">暂无专题订阅</p>
              ) : (
                <div className="space-y-2">
                  {topicSubs.map((s) => (
                    <div key={s.id} className="flex items-center justify-between text-sm">
                      <span>{typeLabel(s)}</span>
                      <div className="flex items-center gap-1">
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          onClick={() => handleToggle(s)}
                          className={s.is_active ? "text-primary" : "text-muted-foreground"}
                        >
                          {s.is_active ? "●" : "○"}
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          onClick={() => handleDelete(s.id)}
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">关键词订阅</CardTitle>
                <Badge variant="secondary">{keywordSubs.length}</Badge>
              </div>
            </CardHeader>
            <CardContent>
              {keywordSubs.length === 0 ? (
                <p className="text-sm text-muted-foreground">暂无关键词订阅</p>
              ) : (
                <div className="space-y-2">
                  {keywordSubs.map((s) => (
                    <div key={s.id} className="flex items-center justify-between text-sm">
                      <span>{typeLabel(s)}</span>
                      <div className="flex items-center gap-1">
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          onClick={() => handleToggle(s)}
                        >
                          {s.is_active ? "●" : "○"}
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          onClick={() => handleDelete(s.id)}
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">实验组订阅</CardTitle>
                <Badge variant="secondary">{experimentSubs.length}</Badge>
              </div>
            </CardHeader>
            <CardContent>
              {experimentSubs.length === 0 ? (
                <p className="text-sm text-muted-foreground">暂无实验组订阅</p>
              ) : (
                <div className="space-y-2">
                  {experimentSubs.map((s) => (
                    <div key={s.id} className="flex items-center justify-between text-sm">
                      <span>{typeLabel(s)}</span>
                      <div className="flex items-center gap-1">
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          onClick={() => handleToggle(s)}
                        >
                          {s.is_active ? "●" : "○"}
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          onClick={() => handleDelete(s.id)}
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
