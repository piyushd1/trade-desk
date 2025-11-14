import { TrendingUp, TrendingDown } from "lucide-react";
import { MetricsCard } from "./MetricsCard";
import { cn } from "@/lib/utils";

interface PnLCardProps {
  /** Total P&L value */
  totalPnL?: number;
  /** Realized P&L value */
  realizedPnL?: number;
  /** Loading state */
  loading?: boolean;
  /** Currency symbol */
  currency?: string;
}

/**
 * P&L (Profit & Loss) card component
 * Displays P&L with color coding and trend icons
 * 
 * @example
 * ```tsx
 * <PnLCard totalPnL={12345} realizedPnL={10000} />
 * <PnLCard totalPnL={-5000} realizedPnL={-3000} />
 * ```
 */
export function PnLCard({ 
  totalPnL = 0, 
  realizedPnL = 0, 
  loading = false,
  currency = "₹" 
}: PnLCardProps) {
  const isProfit = totalPnL >= 0;
  const Icon = isProfit ? TrendingUp : TrendingDown;
  const colorClass = isProfit ? "text-green-600" : "text-red-600";
  
  const formatValue = (value: number) => {
    return `${currency}${Math.abs(value).toLocaleString()}`;
  };

  return (
    <MetricsCard
      title="Today's P&L"
      value={
        <div className={cn("text-2xl font-bold", colorClass)}>
          {isProfit ? '+' : '-'}{formatValue(totalPnL)}
        </div>
      }
      description={`Realized: ${formatValue(realizedPnL)}`}
      icon={Icon}
      iconClassName={colorClass}
      loading={loading}
    />
  );
}
