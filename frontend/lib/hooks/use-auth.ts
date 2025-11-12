"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { authApi } from "../api";
import { useState, useEffect } from "react";

export function useAuth() {
  const [userIdentifier, setUserIdentifier] = useState<string | null>(null);
  const queryClient = useQueryClient();

  // Load user identifier from localStorage
  useEffect(() => {
    const stored = localStorage.getItem("user_identifier");
    if (stored) setUserIdentifier(stored);
  }, []);

  // Get broker status
  const { data: brokerStatus, isLoading: brokerLoading } = useQuery({
    queryKey: ["broker-status"],
    queryFn: authApi.getBrokerStatus,
  });

  // Get session if user identifier exists
  const { data: session, isLoading: sessionLoading, refetch: refetchSession } = useQuery({
    queryKey: ["zerodha-session", userIdentifier],
    queryFn: () => authApi.getZerodhaSession(userIdentifier || undefined),
    enabled: !!userIdentifier,
  });

  // Get refresh status
  const { data: refreshStatus } = useQuery({
    queryKey: ["refresh-status"],
    queryFn: authApi.getRefreshStatus,
    refetchInterval: 60000, // Refetch every minute
  });

  // Login mutation
  const loginMutation = useMutation({
    mutationFn: async (state?: string) => {
      const response = await authApi.getZerodhaLoginUrl(state);
      return response;
    },
  });

  // Refresh token mutation
  const refreshMutation = useMutation({
    mutationFn: async () => {
      return await authApi.refreshToken(userIdentifier || undefined);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["zerodha-session"] });
    },
  });

  const login = async (state?: string) => {
    const response = await loginMutation.mutateAsync(state);
    if (response.login_url) {
      // Save state for callback
      if (state) {
        localStorage.setItem("user_identifier", state);
        setUserIdentifier(state);
      }
      // Redirect to Zerodha login
      window.location.href = response.login_url;
    }
  };

  const logout = () => {
    localStorage.removeItem("user_identifier");
    setUserIdentifier(null);
    queryClient.clear();
  };

  const isAuthenticated = !!session?.session && session.session.status === "active";

  return {
    isAuthenticated,
    userIdentifier,
    session: session?.session,
    brokerStatus: brokerStatus?.brokers,
    refreshStatus: refreshStatus?.refresh_service,
    isLoading: brokerLoading || sessionLoading,
    login,
    logout,
    refreshToken: refreshMutation.mutate,
    refetchSession,
  };
}

