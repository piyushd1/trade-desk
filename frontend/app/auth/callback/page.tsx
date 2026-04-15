"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, CheckCircle2, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

function CallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [message, setMessage] = useState("");
  const [userData, setUserData] = useState<any>(null);

  useEffect(() => {
    const handleCallback = async () => {
      // The backend /api/v1/auth/zerodha/callback handler already exchanged the
      // Kite request_token for an access_token and stored a broker_session row
      // with user_id = NULL, then 302-redirected us here. All we have to do is:
      //   1. Read status + state from the query string
      //   2. Call /api/v1/auth/zerodha/session/claim with the user's JWT so the
      //      session gets linked to the authenticated user (without this, every
      //      portfolio endpoint will 403 because ownership validation fails).
      //   3. Save user_identifier to localStorage so downstream React Query
      //      hooks know which session to look up.
      const callbackStatus = searchParams.get("status");
      const state = searchParams.get("state");
      const errorMessage = searchParams.get("message");

      if (callbackStatus === "error") {
        setStatus("error");
        setMessage(errorMessage || "OAuth authorization failed or was cancelled");
        return;
      }

      if (callbackStatus !== "success" || !state) {
        setStatus("error");
        setMessage("Missing required callback parameters");
        return;
      }

      try {
        setMessage("Linking Zerodha session to your account...");

        // The /auth/callback route isn't wrapped by the AuthProvider, so the
        // axios `api` instance doesn't have the Authorization header set yet.
        // Read the stored access token directly and attach it per-request.
        const accessToken = localStorage.getItem("access_token");
        if (!accessToken) {
          throw new Error("You must be logged in to link a Zerodha session. Please log in and try again.");
        }

        await api.post(
          `/auth/zerodha/session/claim?user_identifier=${encodeURIComponent(state)}`,
          null,
          { headers: { Authorization: `Bearer ${accessToken}` } }
        );

        // Save user identifier so portfolio/margins/holdings queries can find the session
        localStorage.setItem("user_identifier", state);

        setStatus("success");
        setMessage("Successfully connected to Zerodha!");
        setUserData({ state });

        // Redirect to dashboard after 2 seconds
        setTimeout(() => {
          router.push("/dashboard");
        }, 2000);
      } catch (error: any) {
        setStatus("error");
        const detail =
          error?.response?.data?.detail ||
          error?.message ||
          "Failed to complete authentication";
        setMessage(detail);
        console.error("Zerodha callback error:", error);
      }
    };

    handleCallback();
  }, [searchParams, router]);

  return (
    <div className="flex h-screen items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <Card className="w-[450px]">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {status === "loading" && <Loader2 className="h-5 w-5 animate-spin" />}
            {status === "success" && <CheckCircle2 className="h-5 w-5 text-green-600" />}
            {status === "error" && <XCircle className="h-5 w-5 text-red-600" />}
            {status === "loading" && "Authenticating..."}
            {status === "success" && "Success!"}
            {status === "error" && "Authentication Failed"}
          </CardTitle>
          <CardDescription>{message}</CardDescription>
        </CardHeader>
        <CardContent>
          {status === "success" && userData && (
            <div className="space-y-2 text-sm">
              <p className="text-muted-foreground">
                Redirecting to dashboard...
              </p>
              {userData.state && (
                <p className="text-xs text-muted-foreground">
                  User: {userData.state}
                </p>
              )}
            </div>
          )}
          {status === "error" && (
            <Button onClick={() => router.push("/")} className="w-full">
              Return to Login
            </Button>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default function CallbackPage() {
  return (
    <Suspense fallback={
      <div className="flex h-screen items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    }>
      <CallbackContent />
    </Suspense>
  );
}

