import { Badge } from "@/components/ui/badge";
import { Shield } from "lucide-react";
import { MetricsCard } from "./MetricsCard";

interface TradingStatusCardProps {
  /** Whether trading is enabled */
  enabled?: boolean;
  /** Loading state */
  loading?: boolean;
  /** Additional message */
  message?: string;
}

/**
 * Trading status card component
 * Shows current trading status with visual indicators
 * 
 * @example
 * ```tsx
 * <TradingStatusCard enabled={true} />
 * <TradingStatusCard enabled={false} message="Kill switch activated" />
 * ```
 */
export function TradingStatusCard({ 
  enabled = false, 
  loading = false, 
  message 
}: TradingStatusCardProps) {
  const statusText = enabled ? "ENABLED" : "DISABLED";
  const defaultMessage = enabled ? "All systems operational" : "Kill switch activated";
  
  return (
    <MetricsCard
      title="Trading Status"
      value={
        <div className="flex items-center gap-2">
          <Badge variant={enabled ? "default" : "destructive"}>
            {statusText}
          </Badge>
        </div>
      }
      description={message || defaultMessage}
      icon={Shield}
      loading={loading}
    />
  );
}
