"use client"

import type { Topic } from "@/types"
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import Link from "next/link"

interface TopicCardProps {
  topic: Topic
}

export function TopicCard({ topic }: TopicCardProps) {
  return (
    <Link href={`/topics/${topic.slug}`} prefetch={false}>
      <Card className="h-full transition-all hover:shadow-md hover:-translate-y-0.5 cursor-pointer">
        <CardHeader className="pb-2">
          <div className="flex items-center gap-2">
            {topic.icon && <span className="text-xl">{topic.icon}</span>}
            <CardTitle className="text-lg">{topic.name}</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {topic.description && (
            <CardDescription className="line-clamp-2 text-sm">
              {topic.description}
            </CardDescription>
          )}
          <div className="flex items-center gap-2">
            <Badge variant="secondary" className="text-xs">
              {topic.paper_count} 篇论文
            </Badge>
            {topic.keywords && topic.keywords.length > 0 && (
              <span className="text-xs text-muted-foreground">
                {topic.keywords.slice(0, 3).join(" · ")}
              </span>
            )}
          </div>
        </CardContent>
      </Card>
    </Link>
  )
}
