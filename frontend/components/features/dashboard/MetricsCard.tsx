import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface MetricsCardProps {
  /** Card title */
  title: string;
  /** Main metric value */
  value: React.ReactNode;
  /** Optional description or secondary info */
  description?: React.ReactNode;
  /** Optional icon */
  icon?: LucideIcon;
  /** Icon color class */
  iconClassName?: string;
  /** Whether to show loading state */
  loading?: boolean;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Reusable metrics card for displaying KPIs
 * 
 * @example
 * ```tsx
 * <MetricsCard 
 *   title="Today's P&L" 
 *   value="₹12,345" 
 *   description="Realized: ₹10,000"
 *   icon={TrendingUp}
 * />
 * ```
 */
export function MetricsCard({
  title,
  value,
  description,
  icon: Icon,
  iconClassName,
  loading = false,
  className,
}: MetricsCardProps) {
  return (
    <Card className={className}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {Icon && (
          <Icon className={cn("h-4 w-4 text-muted-foreground", iconClassName)} />
        )}
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-2">
            <div className="h-8 w-24 animate-pulse rounded bg-muted" />
            {description && (
              <div className="h-4 w-32 animate-pulse rounded bg-muted" />
            )}
          </div>
        ) : (
          <>
            <div className="text-2xl font-bold">{value}</div>
            {description && (
              <p className="text-xs text-muted-foreground">{description}</p>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
