import Link from "next/link"

export function Footer() {
  return (
    <footer className="border-t py-8 mt-16">
      <div className="container mx-auto px-4">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="text-sm text-muted-foreground">
            <span className="font-medium text-foreground">NuDM</span>
            {" "}— 粒子物理论文追踪平台
          </div>
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <Link href="/topics" className="hover:text-foreground transition-colors">
              专题
            </Link>
            <Link href="/search" className="hover:text-foreground transition-colors">
              搜索
            </Link>
            <span>© {new Date().getFullYear()} NuDM</span>
          </div>
        </div>
        <p className="text-xs text-muted-foreground/60 text-center mt-4">
          数据来源: arXiv, INSPIRE-HEP | AI 解读由 LLM 生成，仅供参考
        </p>
      </div>
    </footer>
  )
}
