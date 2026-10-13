"use client"

import { useState } from "react"
import { useForm, type UseFormRegisterReturn } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Eye, EyeOff } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useAuthStore } from "@/stores/auth"
import { useRouter } from "next/navigation"

const loginSchema = z.object({
  email: z.string().email("请输入有效的邮箱地址"),
  password: z.string().min(6, "密码至少 6 位"),
})

const registerSchema = z.object({
  email: z.string().email("请输入有效的邮箱地址"),
  username: z.string().min(2, "用户名至少 2 个字符"),
  password: z.string().min(6, "密码至少 6 位"),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "两次密码不一致",
  path: ["confirmPassword"],
})

type LoginForm = z.infer<typeof loginSchema>
type RegisterForm = z.infer<typeof registerSchema>

interface PasswordFieldProps {
  id: string
  label: string
  placeholder: string
  show: boolean
  onToggle: () => void
  registerProps: UseFormRegisterReturn
}

function PasswordField({
  id,
  label,
  placeholder,
  show,
  onToggle,
  registerProps,
}: PasswordFieldProps) {
  return (
    <div className="space-y-3">
      <Label htmlFor={id}>{label}</Label>
      <div className="relative">
        <Input
          id={id}
          size="lg"
          type={show ? "text" : "password"}
          placeholder={placeholder}
          className="pr-11"
          {...registerProps}
        />
        <button
          type="button"
          aria-label={show ? "隐藏密码" : "显示密码"}
          onClick={onToggle}
          className="absolute inset-y-0 right-0 flex w-11 items-center justify-center text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-3 focus-visible:ring-ring/50 rounded-r-lg"
        >
          {show ? <EyeOff className="size-5" /> : <Eye className="size-5" />}
        </button>
      </div>
    </div>
  )
}

export default function AuthPage() {
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)
  const [showLoginPassword, setShowLoginPassword] = useState(false)
  const [showRegPassword, setShowRegPassword] = useState(false)
  const [showRegConfirm, setShowRegConfirm] = useState(false)
  const { login, register } = useAuthStore()
  const router = useRouter()

  const loginForm = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  })

  const registerForm = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
    defaultValues: { email: "", username: "", password: "", confirmPassword: "" },
  })

  const handleLogin = async (data: LoginForm) => {
    try {
      setError("")
      setLoading(true)
      await login(data.email, data.password)
      router.push("/")
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "登录失败")
    } finally {
      setLoading(false)
    }
  }

  const handleRegister = async (data: RegisterForm) => {
    try {
      setError("")
      setLoading(true)
      await register(data.email, data.username, data.password)
      setError("注册成功，请切换到登录")
      registerForm.reset()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "注册失败")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container mx-auto px-4 py-16 flex justify-center">
      <Card className="w-full max-w-lg">
        <CardHeader>
          <CardTitle className="text-center">NuDM 登录</CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="login">
            <TabsList className="w-full mb-8">
              <TabsTrigger value="login" className="flex-1">登录</TabsTrigger>
              <TabsTrigger value="register" className="flex-1">注册</TabsTrigger>
            </TabsList>

            <TabsContent value="login">
              <form onSubmit={loginForm.handleSubmit(handleLogin)} className="space-y-5">
                <div className="space-y-3">
                  <Label htmlFor="login-email">邮箱</Label>
                  <Input
                    id="login-email"
                    size="lg"
                    type="email"
                    placeholder="your@email.com"
                    {...loginForm.register("email")}
                  />
                  {loginForm.formState.errors.email && (
                    <p className="text-xs text-destructive">{loginForm.formState.errors.email.message}</p>
                  )}
                </div>
                <div className="space-y-3">
                  <PasswordField
                    id="login-password"
                    label="密码"
                    placeholder="••••••••"
                    show={showLoginPassword}
                    onToggle={() => setShowLoginPassword((v) => !v)}
                    registerProps={loginForm.register("password")}
                  />
                  {loginForm.formState.errors.password && (
                    <p className="text-xs text-destructive">{loginForm.formState.errors.password.message}</p>
                  )}
                </div>
                {error && <p className="text-sm text-destructive">{error}</p>}
                <Button type="submit" size="lg" className="w-full" disabled={loading}>
                  {loading ? "登录中..." : "登录"}
                </Button>
              </form>
            </TabsContent>

            <TabsContent value="register">
              <form onSubmit={registerForm.handleSubmit(handleRegister)} className="space-y-5">
                <div className="space-y-3">
                  <Label htmlFor="reg-email">邮箱</Label>
                  <Input
                    id="reg-email"
                    size="lg"
                    type="email"
                    placeholder="your@email.com"
                    {...registerForm.register("email")}
                  />
                  {registerForm.formState.errors.email && (
                    <p className="text-xs text-destructive">{registerForm.formState.errors.email.message}</p>
                  )}
                </div>
                <div className="space-y-3">
                  <Label htmlFor="reg-username">用户名</Label>
                  <Input
                    id="reg-username"
                    size="lg"
                    placeholder="用户名"
                    {...registerForm.register("username")}
                  />
                  {registerForm.formState.errors.username && (
                    <p className="text-xs text-destructive">{registerForm.formState.errors.username.message}</p>
                  )}
                </div>
                <div className="space-y-3">
                  <PasswordField
                    id="reg-password"
                    label="密码"
                    placeholder="至少6位密码"
                    show={showRegPassword}
                    onToggle={() => setShowRegPassword((v) => !v)}
                    registerProps={registerForm.register("password")}
                  />
                  {registerForm.formState.errors.password && (
                    <p className="text-xs text-destructive">{registerForm.formState.errors.password.message}</p>
                  )}
                </div>
                <div className="space-y-3">
                  <PasswordField
                    id="reg-confirm"
                    label="确认密码"
                    placeholder="再次输入密码"
                    show={showRegConfirm}
                    onToggle={() => setShowRegConfirm((v) => !v)}
                    registerProps={registerForm.register("confirmPassword")}
                  />
                  {registerForm.formState.errors.confirmPassword && (
                    <p className="text-xs text-destructive">{registerForm.formState.errors.confirmPassword.message}</p>
                  )}
                </div>
                {error && <p className="text-sm text-destructive">{error}</p>}
                <Button type="submit" size="lg" className="w-full" disabled={loading}>
                  {loading ? "注册中..." : "注册"}
                </Button>
              </form>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  )
}
