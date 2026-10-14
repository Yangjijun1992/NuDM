"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Button } from "@/components/ui/button"
import { useAuthStore } from "@/stores/auth"
import { cn } from "@/lib/utils"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"

const navItems = [
  { href: "/", label: "首页" },
  { href: "/topics", label: "专题" },
  { href: "/search", label: "搜索" },
]

export function Header() {
  const pathname = usePathname()
  const { user, logout } = useAuthStore()

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center">
        <Link href="/" className="mr-6 flex items-center space-x-2">
          <span className="font-bold text-lg">NuDM</span>
        </Link>
        <nav className="flex items-center space-x-1 text-sm font-medium">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "px-3 py-2 rounded-md transition-colors hover:text-foreground",
                pathname === item.href
                  ? "text-foreground bg-accent"
                  : "text-muted-foreground"
              )}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="ml-auto flex items-center space-x-2">
          {user ? (
            <>
              <Link href="/favorites" prefetch={false}>
                <Button variant="ghost" size="sm">收藏</Button>
              </Link>
              <Link href="/subscriptions" prefetch={false}>
                <Button variant="ghost" size="sm">订阅</Button>
              </Link>
              <Link href="/notifications" prefetch={false}>
                <Button variant="ghost" size="sm">通知</Button>
              </Link>
              <DropdownMenu>
                <DropdownMenuTrigger
                  render={
                    <Button variant="ghost" size="sm" className="gap-2">
                      <Avatar className="h-6 w-6">
                        <AvatarFallback className="text-xs">
                          {user.username[0].toUpperCase()}
                        </AvatarFallback>
                      </Avatar>
                      {user.username}
                    </Button>
                  }
                />
                <DropdownMenuContent align="end">
                  <DropdownMenuItem render={<Link href="/profile" prefetch={false}>个人中心</Link>} />
                  {user.role === "admin" && (
                    <DropdownMenuItem render={<Link href="/admin" prefetch={false}>后台管理</Link>} />
                  )}
                  <DropdownMenuItem onClick={logout}>退出登录</DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </>
          ) : (
            <Link href="/auth" prefetch={false}>
              <Button variant="default" size="sm">登录</Button>
            </Link>
          )}
        </div>
      </div>
    </header>
  )
}
