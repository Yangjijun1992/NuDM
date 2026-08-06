import type { ReactNode } from "react"
import { Button } from "@/components/ui/button"

interface EmptyStateProps {
  icon?: ReactNode
  title: string
  description?: string
  action?: {
    label: string
    href?: string
    onClick?: () => void
  }
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      {icon && <div className="mb-4 text-muted-foreground/50">{icon}</div>}
      <p className="text-base font-medium text-muted-foreground mb-1">{title}</p>
      {description && (
        <p className="text-sm text-muted-foreground/60 max-w-sm mb-4">{description}</p>
      )}
      {action && (
        action.href ? (
          <a href={action.href}>
            <Button variant="outline" size="sm">{action.label}</Button>
          </a>
        ) : (
          <Button variant="outline" size="sm" onClick={action.onClick}>
            {action.label}
          </Button>
        )
      )}
    </div>
  )
}
