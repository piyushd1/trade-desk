"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { riskApi } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Loader2, Shield, AlertTriangle } from "lucide-react";
import { toast } from "sonner";

export default function RiskManagementPage() {
  const queryClient = useQueryClient();

  // Fetch risk config
  const { data: configData, isLoading } = useQuery({
    queryKey: ["risk-config"],
    queryFn: () => riskApi.getConfig(),
  });

  // Fetch kill switch status
  const { data: killSwitchData } = useQuery({
    queryKey: ["kill-switch-status"],
    queryFn: () => riskApi.getKillSwitchStatus(),
    refetchInterval: 10000,
  });

  // Toggle kill switch mutation
  const toggleKillSwitch = useMutation({
    mutationFn: ({ enabled, reason }: { enabled: boolean; reason?: string }) =>
      riskApi.toggleKillSwitch(enabled, reason),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["kill-switch-status"] });
      queryClient.invalidateQueries({ queryKey: ["risk-config"] });
      queryClient.invalidateQueries({ queryKey: ["risk-status"] });
      toast.success(data.message || "Kill switch updated");
    },
    onError: () => {
      toast.error("Failed to toggle kill switch");
    },
  });

  const config = configData?.config;
  const tradingEnabled = killSwitchData?.trading_enabled ?? true;

  const handleKillSwitchToggle = (enabled: boolean) => {
    const reason = enabled 
      ? "Trading enabled via dashboard" 
      : "Emergency stop via dashboard";
    
    if (!enabled) {
      if (!confirm("Are you sure you want to disable all trading? This will stop all active strategies.")) {
        return;
      }
    }
    
    toggleKillSwitch.mutate({ enabled, reason });
  };

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Risk Management</h1>
        <p className="text-muted-foreground">
          Configure risk limits and emergency controls
        </p>
      </div>

      {/* Kill Switch */}
      <Card className="border-2 border-red-200">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Emergency Kill Switch
          </CardTitle>
          <CardDescription>
            Immediately halt all trading activity across all strategies
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="kill-switch" className="text-base font-semibold">
                Trading Status
              </Label>
              <p className="text-sm text-muted-foreground">
                {tradingEnabled 
                  ? "All trading is currently enabled" 
                  : "All trading is currently disabled"}
              </p>
            </div>
            <Switch
              id="kill-switch"
              checked={tradingEnabled}
              onCheckedChange={handleKillSwitchToggle}
              disabled={toggleKillSwitch.isPending}
            />
          </div>
          
          {!tradingEnabled && (
            <div className="flex items-center gap-2 rounded-lg bg-red-50 p-4 text-red-800">
              <AlertTriangle className="h-5 w-5" />
              <p className="text-sm font-medium">
                Trading is currently disabled. Enable to resume operations.
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Position Limits */}
      <Card>
        <CardHeader>
          <CardTitle>Position Limits</CardTitle>
          <CardDescription>Maximum position size and count limits</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <Label className="text-sm font-medium text-muted-foreground">
                Max Position Value
              </Label>
              <p className="text-2xl font-bold">
                ₹{config?.max_position_value?.toLocaleString()}
              </p>
            </div>
            <div className="space-y-2">
              <Label className="text-sm font-medium text-muted-foreground">
                Max Positions
              </Label>
              <p className="text-2xl font-bold">{config?.max_positions}</p>
            </div>
            <div className="space-y-2">
              <Label className="text-sm font-medium text-muted-foreground">
                Max Position %
              </Label>
              <p className="text-2xl font-bold">{config?.max_position_pct}%</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Order Limits */}
      <Card>
        <CardHeader>
          <CardTitle>Order Limits</CardTitle>
          <CardDescription>Order value and frequency limits</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <Label className="text-sm font-medium text-muted-foreground">
                Max Order Value
              </Label>
              <p className="text-2xl font-bold">
                ₹{config?.max_order_value?.toLocaleString()}
              </p>
            </div>
            <div className="space-y-2">
              <Label className="text-sm font-medium text-muted-foreground">
                Max Orders/Day
              </Label>
              <p className="text-2xl font-bold">{config?.max_orders_per_day}</p>
            </div>
            <div className="space-y-2">
              <Label className="text-sm font-medium text-muted-foreground">
                OPS Limit
              </Label>
              <p className="text-2xl font-bold">{config?.ops_limit} orders/sec</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Loss Limits */}
      <Card>
        <CardHeader>
          <CardTitle>Loss Limits</CardTitle>
          <CardDescription>Daily, weekly, and monthly loss limits</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <Label className="text-sm font-medium text-muted-foreground">
                Max Daily Loss
              </Label>
              <p className="text-2xl font-bold">
                ₹{config?.max_daily_loss?.toLocaleString()}
              </p>
            </div>
            <div className="space-y-2">
              <Label className="text-sm font-medium text-muted-foreground">
                Max Weekly Loss
              </Label>
              <p className="text-2xl font-bold">
                ₹{config?.max_weekly_loss?.toLocaleString()}
              </p>
            </div>
            <div className="space-y-2">
              <Label className="text-sm font-medium text-muted-foreground">
                Max Monthly Loss
              </Label>
              <p className="text-2xl font-bold">
                ₹{config?.max_monthly_loss?.toLocaleString()}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Stop Loss Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Stop Loss Settings</CardTitle>
          <CardDescription>Default stop loss and target profit percentages</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <Label className="text-sm font-medium text-muted-foreground">
                Default Stop Loss
              </Label>
              <p className="text-2xl font-bold">{config?.default_stop_loss_pct}%</p>
            </div>
            <div className="space-y-2">
              <Label className="text-sm font-medium text-muted-foreground">
                Default Target
              </Label>
              <p className="text-2xl font-bold">{config?.default_target_profit_pct}%</p>
            </div>
            <div className="space-y-2">
              <Label className="text-sm font-medium text-muted-foreground">
                Enforce Stop Loss
              </Label>
              <p className="text-2xl font-bold">
                {config?.enforce_stop_loss ? "Yes" : "No"}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

