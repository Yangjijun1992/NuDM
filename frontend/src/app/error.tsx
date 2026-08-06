"use client"

import { Button } from "@/components/ui/button"
import { AlertTriangle } from "lucide-react"

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <html>
      <body>
        <div className="flex flex-col items-center justify-center min-h-screen py-16 text-center">
          <AlertTriangle className="h-12 w-12 text-destructive mb-4" />
          <h1 className="text-xl font-bold mb-2">页面加载出错</h1>
          <p className="text-sm text-muted-foreground mb-4 max-w-md">
            {error.message || "发生了未知错误"}
          </p>
          <Button onClick={reset}>重试</Button>
        </div>
      </body>
    </html>
  )
}
