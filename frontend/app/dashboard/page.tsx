"use client";

import { useQuery } from "@tanstack/react-query";
import { riskApi, healthApi } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, TrendingUp, TrendingDown, Shield, AlertTriangle } from "lucide-react";
import { useAuth } from "@/lib/hooks/use-auth";

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
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Trading Status</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <Badge variant={tradingEnabled ? "default" : "destructive"}>
                {tradingEnabled ? "ENABLED" : "DISABLED"}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              {tradingEnabled ? "All systems operational" : "Kill switch activated"}
            </p>
          </CardContent>
        </Card>

        {/* Today's P&L */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Today's P&L</CardTitle>
            {metrics && metrics.total_pnl >= 0 ? (
              <TrendingUp className="h-4 w-4 text-green-600" />
            ) : (
              <TrendingDown className="h-4 w-4 text-red-600" />
            )}
          </CardHeader>
          <CardContent>
            {riskLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <>
                <div className={cn(
                  "text-2xl font-bold",
                  metrics && metrics.total_pnl >= 0 ? "text-green-600" : "text-red-600"
                )}>
                  ₹{metrics?.total_pnl?.toLocaleString() || "0"}
                </div>
                <p className="text-xs text-muted-foreground">
                  Realized: ₹{metrics?.realized_pnl?.toLocaleString() || "0"}
                </p>
              </>
            )}
          </CardContent>
        </Card>

        {/* Orders Today */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Orders Today</CardTitle>
          </CardHeader>
          <CardContent>
            {riskLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <>
                <div className="text-2xl font-bold">
                  {metrics?.orders_placed || 0}
                </div>
                <p className="text-xs text-muted-foreground">
                  Executed: {metrics?.orders_executed || 0} | 
                  Rejected: {metrics?.orders_rejected || 0}
                </p>
              </>
            )}
          </CardContent>
        </Card>

        {/* Risk Breaches */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Risk Breaches</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            {riskLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <>
                <div className={cn(
                  "text-2xl font-bold",
                  (metrics?.risk_breaches || 0) > 0 ? "text-orange-600" : "text-green-600"
                )}>
                  {metrics?.risk_breaches || 0}
                </div>
                <p className="text-xs text-muted-foreground">
                  {(metrics?.risk_breaches || 0) === 0 ? "All clear" : "Review required"}
                </p>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Risk Limits Overview */}
      <Card>
        <CardHeader>
          <CardTitle>Risk Limits</CardTitle>
          <CardDescription>Current risk configuration and utilization</CardDescription>
        </CardHeader>
        <CardContent>
          {riskLoading ? (
            <Loader2 className="h-6 w-6 animate-spin" />
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Max Position Value</p>
                <p className="text-lg font-semibold">₹{limits?.max_position_value?.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Max Positions</p>
                <p className="text-lg font-semibold">{limits?.max_positions}</p>
                <p className="text-xs text-muted-foreground">Current: {metrics?.current_positions || 0}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Max Daily Loss</p>
                <p className="text-lg font-semibold">₹{limits?.max_daily_loss?.toLocaleString()}</p>
                <p className="text-xs text-muted-foreground">
                  {metrics?.loss_limit_breached ? (
                    <span className="text-red-600 font-medium">BREACHED</span>
                  ) : (
                    <span className="text-green-600">Within limits</span>
                  )}
                </p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Max Order Value</p>
                <p className="text-lg font-semibold">₹{limits?.max_order_value?.toLocaleString()}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Orders Per Day</p>
                <p className="text-lg font-semibold">{limits?.max_orders_per_day}</p>
                <p className="text-xs text-muted-foreground">
                  Used: {metrics?.orders_placed || 0}/{limits?.max_orders_per_day}
                </p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">OPS Limit</p>
                <p className="text-lg font-semibold">{limits?.ops_limit} orders/sec</p>
              </div>
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
            <div>
              <p className="text-sm font-medium text-muted-foreground">Broker</p>
              <p className="text-lg font-semibold capitalize">{session?.broker || "N/A"}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Session Status</p>
              <Badge variant={session?.status === "active" ? "default" : "secondary"}>
                {session?.status || "N/A"}
              </Badge>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Token Expires</p>
              <p className="text-sm">
                {session?.expires_at 
                  ? new Date(session.expires_at).toLocaleString()
                  : "N/A"}
              </p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Auto-Refresh</p>
              <Badge variant={refreshStatus?.running ? "default" : "secondary"}>
                {refreshStatus?.running ? "Active" : "Inactive"}
              </Badge>
              {refreshStatus?.next_run && (
                <p className="text-xs text-muted-foreground mt-1">
                  Next: {new Date(refreshStatus.next_run).toLocaleTimeString()}
                </p>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Recent Breaches */}
      {riskStatus?.recent_breaches && riskStatus.recent_breaches.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recent Risk Breaches</CardTitle>
            <CardDescription>Latest risk limit violations</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {riskStatus.recent_breaches.map((breach: any, idx: number) => (
                <div key={idx} className="flex items-center justify-between border-b pb-2">
                  <div>
                    <p className="text-sm font-medium">{breach.breach_type}</p>
                    <p className="text-xs text-muted-foreground">{breach.action_taken}</p>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {new Date(breach.created_at).toLocaleTimeString()}
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function cn(...inputs: any[]) {
  return inputs.filter(Boolean).join(" ");
}

