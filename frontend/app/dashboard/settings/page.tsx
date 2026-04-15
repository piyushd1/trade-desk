"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/lib/hooks/use-auth";
import { authApi } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Loader2, RefreshCw } from "lucide-react";
import { toast } from "sonner";

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const { session, refreshToken, brokerStatus, userIdentifier, login } = useAuth();

  const [apiKeyInput, setApiKeyInput] = useState("");
  const [apiSecretInput, setApiSecretInput] = useState("");
  const [redirectUrlInput, setRedirectUrlInput] = useState<string>("");

  const credentialsConfigured = brokerStatus?.zerodha?.configured ?? false;

  const updateCredentials = useMutation({
    mutationFn: authApi.updateZerodhaConfig,
    onSuccess: () => {
      toast.success("Zerodha credentials saved");
      queryClient.invalidateQueries({ queryKey: ["broker-status"] });
    },
    onError: (error: unknown) => {
      const message = error instanceof Error ? error.message : "Failed to update Zerodha credentials";
      toast.error(message);
    },
  });

  // True when the *form* has both API key and secret typed in — used to gate
  // the "save new credentials" path. Independent of whether backend already
  // has credentials loaded from .env.
  const formHasNewCredentials = useMemo(() => {
    return apiKeyInput.trim().length > 0 && apiSecretInput.trim().length > 0;
  }, [apiKeyInput, apiSecretInput]);

  // True when the user can initiate OAuth at all — either they typed new
  // credentials, OR the backend is already configured from environment.
  const canConnect = formHasNewCredentials || credentialsConfigured;

  useEffect(() => {
    if (!redirectUrlInput && brokerStatus?.zerodha?.redirect_url) {
      setRedirectUrlInput(brokerStatus.zerodha.redirect_url);
    }
  }, [brokerStatus?.zerodha?.redirect_url, redirectUrlInput]);

  const generateState = useCallback(() => {
    if (userIdentifier) {
      return userIdentifier;
    }

    if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
      return crypto.randomUUID();
    }

    return `user-${Date.now()}`;
  }, [userIdentifier]);

  const handleAuthenticate = useCallback(async () => {
    // If the form has new credentials typed in, save them first (this overrides
    // whatever was loaded from .env at container startup — useful when the user
    // rotates keys without touching the server). If the form is empty AND the
    // backend is already configured from environment, skip the save step and
    // go straight to OAuth.
    if (formHasNewCredentials) {
      const apiKey = apiKeyInput.trim();
      const apiSecret = apiSecretInput.trim();
      const redirectUrl = redirectUrlInput.trim() || undefined;
      try {
        await updateCredentials.mutateAsync({ apiKey, apiSecret, redirectUrl });
        setApiKeyInput("");
        setApiSecretInput("");
      } catch (error) {
        console.error("Failed to save Zerodha credentials:", error);
        return; // mutation.onError surfaced a toast already
      }
    } else if (!credentialsConfigured) {
      toast.error("Enter API key and secret to continue");
      return;
    }

    try {
      const state = generateState();
      await login(state);
    } catch (error) {
      console.error("Failed to initiate Zerodha login:", error);
      toast.error("Failed to initiate Zerodha login");
    }
  }, [
    apiKeyInput,
    apiSecretInput,
    redirectUrlInput,
    formHasNewCredentials,
    credentialsConfigured,
    updateCredentials,
    generateState,
    login,
  ]);

  const handleRefreshToken = () => {
    refreshToken();
    toast.success("Token refresh initiated");
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Settings</h1>
        <p className="text-muted-foreground">
          Manage broker connections and application settings
        </p>
      </div>

      {/* Broker Connection */}
      <Card>
        <CardHeader>
          <CardTitle>Broker Connection</CardTitle>
          <CardDescription>Your connected trading account</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Zerodha</p>
              <p className="text-sm text-muted-foreground">
                User: {userIdentifier || "Not set"}
              </p>
            </div>
            <Badge variant={session?.status === "active" ? "default" : "secondary"}>
              {session?.status || "Not connected"}
            </Badge>
          </div>

          <div className="grid gap-4">
            <div className="space-y-2">
              <Label htmlFor="zerodha-api-key">API Key</Label>
              <Input
                id="zerodha-api-key"
                placeholder="Enter Zerodha API key"
                autoComplete="off"
                value={apiKeyInput}
                onChange={(event) => setApiKeyInput(event.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="zerodha-api-secret">API Secret</Label>
              <Input
                id="zerodha-api-secret"
                type="password"
                placeholder="Enter Zerodha API secret"
                autoComplete="off"
                value={apiSecretInput}
                onChange={(event) => setApiSecretInput(event.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="zerodha-redirect-url">Redirect URL (optional)</Label>
              <Input
                id="zerodha-redirect-url"
                placeholder={brokerStatus?.zerodha?.redirect_url || "https://piyushdev.com/api/v1/auth/zerodha/callback"}
                autoComplete="off"
                value={redirectUrlInput}
                onChange={(event) => setRedirectUrlInput(event.target.value)}
              />
            </div>
            <Button
              type="button"
              className="w-full"
              onClick={handleAuthenticate}
              disabled={!canConnect || updateCredentials.isPending}
            >
              {updateCredentials.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : null}
              {formHasNewCredentials
                ? "Save & Connect to Zerodha"
                : credentialsConfigured
                  ? "Connect to Zerodha"
                  : "Enter credentials to connect"}
            </Button>
            {credentialsConfigured && !formHasNewCredentials && (
              <p className="text-xs text-muted-foreground text-center">
                Using credentials from server configuration. Fill the fields above only to override.
              </p>
            )}
          </div>

          {session && (
            <>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Broker:</span>
                  <span className="font-medium capitalize">{session.broker}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Token Expires:</span>
                  <span className="font-medium">
                    {session.expires_at 
                      ? new Date(session.expires_at).toLocaleString()
                      : "N/A"}
                  </span>
                </div>
                {session.access_token_preview && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Token:</span>
                    <span className="font-mono text-xs">{session.access_token_preview}</span>
                  </div>
                )}
              </div>

              <Button
                onClick={handleRefreshToken}
                variant="outline"
                className="w-full"
              >
                <RefreshCw className="mr-2 h-4 w-4" />
                Refresh Token
              </Button>
            </>
          )}
        </CardContent>
      </Card>

      {/* Broker Status */}
      <Card>
        <CardHeader>
          <CardTitle>Available Brokers</CardTitle>
          <CardDescription>Configured broker integrations</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {brokerStatus?.zerodha && (
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Zerodha</p>
                  <p className="text-sm text-muted-foreground">
                    {brokerStatus.zerodha.message}
                  </p>
                </div>
                <Badge variant={brokerStatus.zerodha.configured ? "default" : "secondary"}>
                  {brokerStatus.zerodha.status}
                </Badge>
              </div>
            )}
            {brokerStatus?.groww && (
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Groww</p>
                  <p className="text-sm text-muted-foreground">
                    {brokerStatus.groww.message}
                  </p>
                </div>
                <Badge variant="secondary">{brokerStatus.groww.status}</Badge>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Application Info */}
      <Card>
        <CardHeader>
          <CardTitle>Application Information</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Version:</span>
              <span className="font-medium">1.0.0</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Environment:</span>
              <span className="font-medium">Development</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">API URL:</span>
              <span className="font-mono text-xs">
                {process.env.NEXT_PUBLIC_API_URL}
              </span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

