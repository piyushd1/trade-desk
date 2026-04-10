"use client";

import { useQuery } from "@tanstack/react-query";
import { portfolioApi, type Holding, type Position } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertTriangle, TrendingUp, TrendingDown, Minus, Wallet } from "lucide-react";
import { useAuth } from "@/lib/hooks/use-auth";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { cn } from "@/lib/utils";

// ─────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────

function fmt(n: number | undefined | null, decimals = 2): string {
  if (n == null || isNaN(n)) return "—";
  return n.toLocaleString("en-IN", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

function fmtRupee(n: number | undefined | null): string {
  if (n == null || isNaN(n)) return "—";
  return `₹${fmt(n)}`;
}

function fmtPct(n: number | undefined | null): string {
  if (n == null || isNaN(n)) return "—";
  return `${n >= 0 ? "+" : ""}${fmt(n)}%`;
}

function PnLBadge({ value }: { value: number | undefined | null }) {
  if (value == null || isNaN(value)) return <span className="text-muted-foreground">—</span>;
  const positive = value >= 0;
  return (
    <span
      className={cn(
        "font-semibold",
        positive ? "text-green-600" : "text-red-600"
      )}
    >
      {positive ? "+" : ""}
      {fmtRupee(value)}
    </span>
  );
}

function TrendIcon({ value }: { value: number | undefined | null }) {
  if (value == null || isNaN(value))
    return <Minus className="h-4 w-4 text-muted-foreground" />;
  if (value > 0) return <TrendingUp className="h-4 w-4 text-green-600" />;
  if (value < 0) return <TrendingDown className="h-4 w-4 text-red-600" />;
  return <Minus className="h-4 w-4 text-muted-foreground" />;
}

// ─────────────────────────────────────────────
// Margins summary card
// ─────────────────────────────────────────────

function MarginsCard({ userIdentifier }: { userIdentifier: string }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["margins", userIdentifier],
    queryFn: () => portfolioApi.getMargins(userIdentifier),
    refetchInterval: 60_000,
  });

  const equity = data?.data?.equity ?? (data as any)?.equity;
  const available = equity?.available;
  const utilised = equity?.utilised;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-base">
          <Wallet className="h-4 w-4" />
          Available Capital (Equity)
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading && <LoadingSpinner text="Loading margins..." />}
        {isError && (
          <p className="text-sm text-destructive">
            Could not load margins. Make sure your Zerodha session is active.
          </p>
        )}
        {!isLoading && !isError && !equity && (
          <p className="text-sm text-muted-foreground">No margin data returned.</p>
        )}
        {equity && (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <div>
              <p className="text-xs text-muted-foreground">Cash</p>
              <p className="text-lg font-semibold">{fmtRupee(available?.cash)}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Live Balance</p>
              <p className="text-lg font-semibold">{fmtRupee(available?.live_balance)}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Net Available</p>
              <p className="text-lg font-semibold">{fmtRupee(equity?.net)}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Exposure Used</p>
              <p className="text-lg font-semibold text-orange-600">
                {fmtRupee(utilised?.exposure)}
              </p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ─────────────────────────────────────────────
// Holdings table
// ─────────────────────────────────────────────

function HoldingsTable({ holdings }: { holdings: Holding[] }) {
  if (holdings.length === 0) {
    return (
      <p className="py-6 text-center text-sm text-muted-foreground">
        No holdings found. Holdings are long-term (CNC/delivery) positions.
      </p>
    );
  }

  const totalPnl = holdings.reduce((sum, h) => sum + (h.pnl ?? 0), 0);
  const totalValue = holdings.reduce(
    (sum, h) => sum + (h.last_price ?? 0) * (h.quantity ?? 0),
    0
  );

  return (
    <div className="space-y-4">
      {/* Summary row */}
      <div className="flex flex-wrap gap-6 rounded-lg border bg-muted/40 p-4">
        <div>
          <p className="text-xs text-muted-foreground">Holdings</p>
          <p className="text-lg font-semibold">{holdings.length}</p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Current Value</p>
          <p className="text-lg font-semibold">{fmtRupee(totalValue)}</p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Total P&L</p>
          <PnLBadge value={totalPnl} />
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-md border">
        <table className="w-full text-sm">
          <thead className="bg-muted/50">
            <tr>
              <th className="px-4 py-3 text-left font-medium">Symbol</th>
              <th className="px-4 py-3 text-right font-medium">Qty</th>
              <th className="px-4 py-3 text-right font-medium">Avg Price</th>
              <th className="px-4 py-3 text-right font-medium">LTP</th>
              <th className="px-4 py-3 text-right font-medium">P&L</th>
              <th className="px-4 py-3 text-right font-medium">Day Change</th>
              <th className="px-4 py-3 text-center font-medium">Trend</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {holdings.map((h) => (
              <tr key={`${h.exchange}:${h.tradingsymbol}`} className="hover:bg-muted/30">
                <td className="px-4 py-3">
                  <div>
                    <span className="font-medium">{h.tradingsymbol}</span>
                    <span className="ml-2 text-xs text-muted-foreground">{h.exchange}</span>
                  </div>
                </td>
                <td className="px-4 py-3 text-right">{h.quantity}</td>
                <td className="px-4 py-3 text-right">{fmtRupee(h.average_price)}</td>
                <td className="px-4 py-3 text-right font-medium">{fmtRupee(h.last_price)}</td>
                <td className="px-4 py-3 text-right">
                  <PnLBadge value={h.pnl} />
                </td>
                <td className="px-4 py-3 text-right">
                  <span
                    className={cn(
                      "text-xs",
                      (h.day_change ?? 0) >= 0 ? "text-green-600" : "text-red-600"
                    )}
                  >
                    {fmtPct(h.day_change_percentage)}
                  </span>
                </td>
                <td className="px-4 py-3 text-center">
                  <TrendIcon value={h.day_change} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────
// Positions table
// ─────────────────────────────────────────────

function PositionsTable({ positions }: { positions: Position[] }) {
  const active = positions.filter((p) => p.quantity !== 0);

  if (active.length === 0) {
    return (
      <p className="py-6 text-center text-sm text-muted-foreground">
        No open positions today. Day and intraday positions will appear here.
      </p>
    );
  }

  const totalPnl = active.reduce((sum, p) => sum + (p.pnl ?? 0), 0);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-6 rounded-lg border bg-muted/40 p-4">
        <div>
          <p className="text-xs text-muted-foreground">Open Positions</p>
          <p className="text-lg font-semibold">{active.length}</p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Total P&L</p>
          <PnLBadge value={totalPnl} />
        </div>
      </div>

      <div className="overflow-x-auto rounded-md border">
        <table className="w-full text-sm">
          <thead className="bg-muted/50">
            <tr>
              <th className="px-4 py-3 text-left font-medium">Symbol</th>
              <th className="px-4 py-3 text-center font-medium">Product</th>
              <th className="px-4 py-3 text-right font-medium">Qty</th>
              <th className="px-4 py-3 text-right font-medium">Avg Price</th>
              <th className="px-4 py-3 text-right font-medium">LTP</th>
              <th className="px-4 py-3 text-right font-medium">P&L</th>
              <th className="px-4 py-3 text-right font-medium">M2M</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {active.map((p, idx) => (
              <tr key={`${p.exchange}:${p.tradingsymbol}-${idx}`} className="hover:bg-muted/30">
                <td className="px-4 py-3">
                  <div>
                    <span className="font-medium">{p.tradingsymbol}</span>
                    <span className="ml-2 text-xs text-muted-foreground">{p.exchange}</span>
                  </div>
                </td>
                <td className="px-4 py-3 text-center">
                  <Badge variant="outline" className="text-xs">
                    {p.product}
                  </Badge>
                </td>
                <td
                  className={cn(
                    "px-4 py-3 text-right font-medium",
                    p.quantity > 0 ? "text-green-700" : "text-red-700"
                  )}
                >
                  {p.quantity > 0 ? "+" : ""}
                  {p.quantity}
                </td>
                <td className="px-4 py-3 text-right">{fmtRupee(p.average_price)}</td>
                <td className="px-4 py-3 text-right font-medium">{fmtRupee(p.last_price)}</td>
                <td className="px-4 py-3 text-right">
                  <PnLBadge value={p.pnl} />
                </td>
                <td className="px-4 py-3 text-right">
                  <PnLBadge value={p.m2m} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────
// Main page
// ─────────────────────────────────────────────

/**
 * Portfolio page — Plan A Decision Dashboard
 *
 * Shows:
 * - Available capital / margins summary
 * - Long-term holdings with P&L
 * - Current day/net positions
 *
 * Requires:
 * - TradeDesk JWT (handled by AuthGuard wrapping all dashboard pages)
 * - Zerodha session active (`user_identifier` in localStorage)
 */
export default function PortfolioPage() {
  const { userIdentifier } = useAuth();

  const {
    data: holdingsData,
    isLoading: holdingsLoading,
    isError: holdingsError,
    error: holdingsErr,
  } = useQuery({
    queryKey: ["holdings", userIdentifier],
    queryFn: () => portfolioApi.getHoldings(userIdentifier!),
    enabled: !!userIdentifier,
    refetchInterval: 60_000,
  });

  const {
    data: positionsData,
    isLoading: positionsLoading,
    isError: positionsError,
  } = useQuery({
    queryKey: ["positions", userIdentifier],
    queryFn: () => portfolioApi.getPositions(userIdentifier!),
    enabled: !!userIdentifier,
    refetchInterval: 30_000,
  });

  // The backend wraps data in { status, data: [...] }
  // For holdings the array is at data.data; for positions it may be at data.data.net
  const holdings: Holding[] = holdingsData?.data ?? [];
  const positionsNet: Position[] = positionsData?.data?.net ?? positionsData?.net ?? [];
  const positionsDay: Position[] = positionsData?.data?.day ?? positionsData?.day ?? [];
  // Merge day + net, deduplicate by tradingsymbol+exchange
  const allPositions: Position[] = [...positionsNet, ...positionsDay].filter(
    (p, idx, arr) =>
      arr.findIndex(
        (q) => q.tradingsymbol === p.tradingsymbol && q.exchange === p.exchange && q.product === p.product
      ) === idx
  );

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Portfolio</h1>
        <p className="text-muted-foreground">
          Your holdings and open positions from Zerodha
        </p>
      </div>

      {/* Zerodha session guard */}
      {!userIdentifier && (
        <Alert>
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            No Zerodha session found. Please connect your Zerodha account in{" "}
            <a href="/dashboard/settings" className="underline">
              Settings
            </a>{" "}
            to see your portfolio.
          </AlertDescription>
        </Alert>
      )}

      {userIdentifier && (
        <>
          {/* Margins */}
          <MarginsCard userIdentifier={userIdentifier} />

          {/* Holdings */}
          <Card>
            <CardHeader>
              <CardTitle>Holdings</CardTitle>
              <CardDescription>
                Long-term delivery (CNC) positions — your equity investments
              </CardDescription>
            </CardHeader>
            <CardContent>
              {holdingsLoading && <LoadingSpinner text="Loading holdings..." />}
              {holdingsError && (
                <Alert variant="destructive">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    {(holdingsErr as any)?.response?.data?.message ??
                      "Failed to load holdings. Check that your Zerodha session is active."}
                  </AlertDescription>
                </Alert>
              )}
              {!holdingsLoading && !holdingsError && (
                <HoldingsTable holdings={holdings} />
              )}
            </CardContent>
          </Card>

          {/* Positions */}
          <Card>
            <CardHeader>
              <CardTitle>Open Positions</CardTitle>
              <CardDescription>
                Current day and carry-forward positions (MIS / NRML / CNC intraday)
              </CardDescription>
            </CardHeader>
            <CardContent>
              {positionsLoading && <LoadingSpinner text="Loading positions..." />}
              {positionsError && (
                <Alert variant="destructive">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    Failed to load positions. Check that your Zerodha session is active.
                  </AlertDescription>
                </Alert>
              )}
              {!positionsLoading && !positionsError && (
                <PositionsTable positions={allPositions} />
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
