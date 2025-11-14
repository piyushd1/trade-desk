"use client";

import { useQuery } from "@tanstack/react-query";
import { riskApi, healthApi } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle } from "lucide-react";
import { useAuth } from "@/lib/hooks/use-auth";
import { cn } from "@/lib/utils";

// Import new components
import { TradingStatusCard } from "@/components/features/dashboard/TradingStatusCard";
import { PnLCard } from "@/components/features/dashboard/PnLCard";
import { MetricsCard } from "@/components/features/dashboard/MetricsCard";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";

/**
 * Dashboard page - Main trading overview
 * 
 * Displays:
 * - Trading status
 * - Today's P&L
 * - Order metrics
 * - Risk breaches
 * - Risk limits overview
 * - Session information
 */
export default function DashboardPage() {
  const { userIdentifier, session, refreshStatus } = useAuth();

  // Fetch risk status
  const { data: riskStatus, isLoading: riskLoading } = useQuery({
    queryKey: ["risk-status", 1],
    queryFn: () => riskApi.getStatus(1),
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  // Fetch health
  const { data: health } = useQuery({
    queryKey: ["health"],
    queryFn: healthApi.check,
    refetchInterval: 60000,
  });

  const metrics = riskStatus?.daily_metrics;
  const limits = riskStatus?.limits;
  const tradingEnabled = riskStatus?.trading_enabled;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground">
          Welcome back, {userIdentifier || "Trader"}
        </p>
      </div>

      {/* Status Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {/* Trading Status */}
        <TradingStatusCard 
          enabled={tradingEnabled} 
          loading={riskLoading}
        />

        {/* Today's P&L */}
        <PnLCard
          totalPnL={metrics?.total_pnl}
          realizedPnL={metrics?.realized_pnl}
          loading={riskLoading}
        />

        {/* Orders Today */}
        <MetricsCard
          title="Orders Today"
          value={metrics?.orders_placed || 0}
          description={
            `Executed: ${metrics?.orders_executed || 0} | Rejected: ${metrics?.orders_rejected || 0}`
          }
          loading={riskLoading}
        />

        {/* Risk Breaches */}
        <MetricsCard
          title="Risk Breaches"
          value={
            <div className={cn(
              "text-2xl font-bold",
              (metrics?.risk_breaches || 0) > 0 ? "text-orange-600" : "text-green-600"
            )}>
              {metrics?.risk_breaches || 0}
            </div>
          }
          description={(metrics?.risk_breaches || 0) === 0 ? "All clear" : "Review required"}
          icon={AlertTriangle}
          loading={riskLoading}
        />
      </div>

      {/* Risk Limits Overview */}
      <Card>
        <CardHeader>
          <CardTitle>Risk Limits</CardTitle>
          <CardDescription>Current risk configuration and utilization</CardDescription>
        </CardHeader>
        <CardContent>
          {riskLoading ? (
            <LoadingSpinner text="Loading risk limits..." />
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              <RiskLimitItem
                label="Max Position Value"
                value={`₹${limits?.max_position_value?.toLocaleString()}`}
              />
              <RiskLimitItem
                label="Max Positions"
                value={limits?.max_positions}
                description={`Current: ${metrics?.current_positions || 0}`}
              />
              <RiskLimitItem
                label="Max Daily Loss"
                value={`₹${limits?.max_daily_loss?.toLocaleString()}`}
                description={
                  metrics?.loss_limit_breached ? (
                    <span className="text-red-600 font-medium">BREACHED</span>
                  ) : (
                    <span className="text-green-600">Within limits</span>
                  )
                }
              />
              <RiskLimitItem
                label="Max Order Value"
                value={`₹${limits?.max_order_value?.toLocaleString()}`}
              />
              <RiskLimitItem
                label="Orders Per Day"
                value={limits?.max_orders_per_day}
                description={`Used: ${metrics?.orders_placed || 0}/${limits?.max_orders_per_day}`}
              />
              <RiskLimitItem
                label="OPS Limit"
                value={`${limits?.ops_limit} orders/sec`}
              />
            </div>
          )}
        </CardContent>
      </Card>

      {/* Session Info */}
      <Card>
        <CardHeader>
          <CardTitle>Session Information</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <SessionInfoItem
              label="Broker"
              value={session?.broker || "N/A"}
              capitalize
            />
            <SessionInfoItem
              label="Session Status"
              value={
                session ? (
                  <Badge variant={session.status === "active" ? "default" : "secondary"}>
                    {session.status}
                  </Badge>
                ) : (
                  "N/A"
                )
              }
            />
            <SessionInfoItem
              label="Session Expires"
              value={
                session?.expires_at
                  ? new Date(session.expires_at).toLocaleString()
                  : "N/A"
              }
            />
            <SessionInfoItem
              label="Auto Refresh"
              value={
                refreshStatus?.is_running ? (
                  <Badge variant="default">Active</Badge>
                ) : (
                  <Badge variant="secondary">Inactive</Badge>
                )
              }
            />
            {refreshStatus?.last_refresh_at && (
              <SessionInfoItem
                label="Last Refresh"
                value={new Date(refreshStatus.last_refresh_at).toLocaleTimeString()}
              />
            )}
            {refreshStatus?.next_refresh_at && (
              <SessionInfoItem
                label="Next Refresh"
                value={new Date(refreshStatus.next_refresh_at).toLocaleTimeString()}
              />
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Helper components
function RiskLimitItem({ 
  label, 
  value, 
  description 
}: { 
  label: string; 
  value: React.ReactNode; 
  description?: React.ReactNode;
}) {
  return (
    <div>
      <p className="text-sm font-medium text-muted-foreground">{label}</p>
      <p className="text-lg font-semibold">{value}</p>
      {description && (
        <p className="text-xs text-muted-foreground">{description}</p>
      )}
    </div>
  );
}

function SessionInfoItem({ 
  label, 
  value, 
  capitalize 
}: { 
  label: string; 
  value: React.ReactNode; 
  capitalize?: boolean;
}) {
  return (
    <div>
      <p className="text-sm font-medium text-muted-foreground">{label}</p>
      <p className={cn("text-lg font-semibold", capitalize && "capitalize")}>
        {value}
      </p>
    </div>
  );
}