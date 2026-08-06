"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { useAuthStore } from "@/stores/auth"
import { api } from "@/lib/api"

export default function ProfilePage() {
  const { user, fetchUser } = useAuthStore()
  const [username, setUsername] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState("")

  if (!user) {
    return (
      <div className="container mx-auto px-4 py-8">
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            请先登录
          </CardContent>
        </Card>
      </div>
    )
  }

  const handleSave = async () => {
    setSaving(true)
    setMessage("")
    try {
      const data: Record<string, string> = {}
      if (username && username !== user.username) data.username = username
      if (email && email !== user.email) data.email = email
      if (password) data.password = password

      if (Object.keys(data).length === 0) {
        setMessage("无变更")
        return
      }

      await api.patch("/users/me", data)
      await fetchUser()
      setUsername("")
      setEmail("")
      setPassword("")
      setMessage("保存成功")
    } catch (e: unknown) {
      setMessage(e instanceof Error ? e.message : "保存失败")
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-2xl">
      <h1 className="text-3xl font-bold mb-8">个人中心</h1>

      <Card className="mb-6">
        <CardHeader>
          <div className="flex items-center gap-4">
            <Avatar className="h-16 w-16">
              <AvatarFallback className="text-xl">
                {user.username[0].toUpperCase()}
              </AvatarFallback>
            </Avatar>
            <div>
              <CardTitle>{user.username}</CardTitle>
              <p className="text-sm text-muted-foreground">{user.email}</p>
              <p className="text-xs text-muted-foreground mt-1">
                角色: {user.role === "admin" ? "管理员" : "普通用户"}
                {" · "}注册于 {new Date(user.created_at).toLocaleDateString("zh-CN")}
              </p>
            </div>
          </div>
        </CardHeader>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>修改信息</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="username">用户名</Label>
            <Input
              id="username"
              placeholder={user.username}
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="email">邮箱</Label>
            <Input
              id="email"
              type="email"
              placeholder={user.email}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">新密码（留空则不修改）</Label>
            <Input
              id="password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          {message && (
            <p className={`text-sm ${message.includes("成功") ? "text-green-600" : "text-destructive"}`}>
              {message}
            </p>
          )}
          <Button onClick={handleSave} disabled={saving}>
            {saving ? "保存中..." : "保存修改"}
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
