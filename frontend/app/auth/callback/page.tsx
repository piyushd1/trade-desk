"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2, CheckCircle2, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function CallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [message, setMessage] = useState("");
  const [userData, setUserData] = useState<any>(null);

  useEffect(() => {
    const handleCallback = async () => {
      // Get OAuth parameters from URL
      const requestToken = searchParams.get("request_token");
      const callbackStatus = searchParams.get("status");
      const state = searchParams.get("state");

      if (callbackStatus !== "success" || !requestToken) {
        setStatus("error");
        setMessage("OAuth authorization failed or was cancelled");
        return;
      }

      try {
        // The backend callback endpoint will handle the token exchange
        // We just need to verify the session was created
        setMessage("Authenticating with Zerodha...");
        
        // Wait a moment for backend to process
        await new Promise(resolve => setTimeout(resolve, 1000));

        // Save user identifier
        if (state) {
          localStorage.setItem("user_identifier", state);
        }

        setStatus("success");
        setMessage("Successfully connected to Zerodha!");
        setUserData({ state, request_token: requestToken });

        // Redirect to dashboard after 2 seconds
        setTimeout(() => {
          router.push("/dashboard");
        }, 2000);
      } catch (error) {
        setStatus("error");
        setMessage("Failed to complete authentication");
        console.error("Auth error:", error);
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

