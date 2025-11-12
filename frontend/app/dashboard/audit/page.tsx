"use client";

import { useQuery } from "@tanstack/react-query";
import { auditApi } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, FileText } from "lucide-react";
import { format } from "date-fns";

export default function AuditLogsPage() {
  const { data: logsData, isLoading } = useQuery({
    queryKey: ["audit-logs"],
    queryFn: () => auditApi.getLogs(undefined, undefined, undefined, 50, 0),
  });

  const { data: eventsData } = useQuery({
    queryKey: ["system-events"],
    queryFn: () => auditApi.getSystemEvents(undefined, undefined, undefined, 50, 0),
  });

  const logs = logsData?.logs || [];
  const events = eventsData?.events || [];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Audit Logs</h1>
        <p className="text-muted-foreground">
          SEBI-compliant audit trail of all operations
        </p>
      </div>

      {/* Audit Logs */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            User Actions
          </CardTitle>
          <CardDescription>
            Complete audit trail of user actions and API calls
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin" />
            </div>
          ) : logs.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">
              No audit logs yet
            </p>
          ) : (
            <div className="space-y-2">
              {logs.map((log: any) => (
                <div
                  key={log.id}
                  className="flex items-center justify-between border-b pb-3 last:border-0"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline">{log.action}</Badge>
                      {log.entity_type && (
                        <span className="text-xs text-muted-foreground">
                          {log.entity_type}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {log.username || "System"} • {log.ip_address || "N/A"}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium">
                      {format(new Date(log.created_at), "MMM dd, HH:mm:ss")}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* System Events */}
      <Card>
        <CardHeader>
          <CardTitle>System Events</CardTitle>
          <CardDescription>
            System-level events, errors, and warnings
          </CardDescription>
        </CardHeader>
        <CardContent>
          {events.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">
              No system events
            </p>
          ) : (
            <div className="space-y-2">
              {events.map((event: any) => (
                <div
                  key={event.id}
                  className="flex items-center justify-between border-b pb-3 last:border-0"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <Badge
                        variant={
                          event.severity === "error" || event.severity === "critical"
                            ? "destructive"
                            : event.severity === "warning"
                            ? "secondary"
                            : "outline"
                        }
                      >
                        {event.severity}
                      </Badge>
                      <span className="text-sm font-medium">{event.event_type}</span>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {event.component && `[${event.component}] `}
                      {event.message}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm">
                      {format(new Date(event.created_at), "MMM dd, HH:mm:ss")}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

