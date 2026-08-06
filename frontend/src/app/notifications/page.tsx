"use client"

import { useEffect, useState } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { api } from "@/lib/api"
import type { Notification, PaginatedResponse } from "@/types"
import { CheckCheck, Bell } from "lucide-react"

export default function NotificationsPage() {
  const [data, setData] = useState<PaginatedResponse<Notification> | null>(null)
  const [loading, setLoading] = useState(true)
  const [unread, setUnread] = useState(0)

  const loadData = async () => {
    setLoading(true)
    try {
      const [notifs, count] = await Promise.all([
        api.notifications.list({ page_size: 50 }),
        api.notifications.unreadCount(),
      ])
      setData(notifs)
      setUnread(count.count)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const handleMarkAllRead = async () => {
    await api.notifications.markAllRead()
    loadData()
  }

  const handleMarkRead = async (id: string) => {
    await api.notifications.markRead(id)
    loadData()
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-2">
        <h1 className="text-3xl font-bold">通知中心</h1>
        {unread > 0 && (
          <Button variant="ghost" size="sm" onClick={handleMarkAllRead}>
            <CheckCheck className="h-4 w-4 mr-1" />
            全部已读
          </Button>
        )}
      </div>
      <p className="text-muted-foreground mb-8">
        <Badge variant={unread > 0 ? "default" : "secondary"} className="mr-2">
          {unread} 未读
        </Badge>
        系统通知与论文更新
      </p>

      {loading ? (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-20 rounded-xl" />
          ))}
        </div>
      ) : data && data.items.length > 0 ? (
        <div className="space-y-3">
          {data.items.map((n) => (
            <Card
              key={n.id}
              className={`cursor-pointer transition-colors ${n.is_read ? "opacity-70" : "border-primary/30"}`}
              onClick={() => !n.is_read && handleMarkRead(n.id)}
            >
              <CardContent className="py-4">
                <div className="flex items-start gap-3">
                  <Bell className={`h-4 w-4 mt-0.5 ${n.is_read ? "text-muted-foreground" : "text-primary"}`} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium">{n.title}</p>
                    {n.content && (
                      <p className="text-sm text-muted-foreground mt-1 line-clamp-2">{n.content}</p>
                    )}
                    <p className="text-xs text-muted-foreground mt-2">
                      {new Date(n.created_at).toLocaleString("zh-CN")}
                    </p>
                  </div>
                  {!n.is_read && <Badge variant="default" className="text-xs">新</Badge>}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            暂无通知，新论文发布时将自动推送
          </CardContent>
        </Card>
      )}
    </div>
  )
}
