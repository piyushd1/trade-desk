"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState, useCallback } from "react";
import { api, authApi } from "../api";

type StoredUser = {
  id: number;
  username: string;
  email?: string | null;
  full_name?: string | null;
  role?: string | null;
};

export function useAuth() {
  const queryClient = useQueryClient();

  const [userIdentifier, setUserIdentifier] = useState<string | null>(null);
  const [user, setUser] = useState<StoredUser | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [refreshTokenValue, setRefreshTokenValue] = useState<string | null>(null);
  const [authReady, setAuthReady] = useState(false);

  /**
   * Initialize auth state from localStorage
   */
  useEffect(() => {
    const loadAuthState = () => {
      try {
        const storedIdentifier = localStorage.getItem("user_identifier");
        const storedUser = localStorage.getItem("user");
        const storedAccess = localStorage.getItem("access_token");
        const storedRefresh = localStorage.getItem("refresh_token");

        if (storedIdentifier) {
          setUserIdentifier(storedIdentifier);
        } else {
          setUserIdentifier(null);
        }

        if (storedUser) {
          setUser(JSON.parse(storedUser));
        } else {
          setUser(null);
        }

        setAccessToken(storedAccess);
        setRefreshTokenValue(storedRefresh);
      } catch (error) {
        console.error("Failed to load auth state:", error);
        setUser(null);
        setAccessToken(null);
        setRefreshTokenValue(null);
        setUserIdentifier(null);
      } finally {
        setAuthReady(true);
      }
    };

    loadAuthState();

    const handleStorage = (event: StorageEvent) => {
      if (event.storageArea !== localStorage) return;
      if (["user_identifier", "user", "access_token", "refresh_token"].includes(event.key || "")) {
        loadAuthState();
      }
    };

    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
  }, []);

  /**
   * Keep Authorization header in sync with stored access token
   */
  useEffect(() => {
    if (accessToken) {
      api.defaults.headers.common.Authorization = `Bearer ${accessToken}`;
    } else {
      delete api.defaults.headers.common.Authorization;
    }
  }, [accessToken]);

  /**
   * React Query: Broker status (global)
   */
  const { data: brokerStatus, isLoading: brokerLoading } = useQuery({
    queryKey: ["broker-status"],
    queryFn: authApi.getBrokerStatus,
    enabled: authReady,
  });

  /**
   * React Query: Zerodha session (requires user identifier)
   */
  const {
    data: session,
    isLoading: sessionLoading,
    refetch: refetchSession,
  } = useQuery({
    queryKey: ["zerodha-session", userIdentifier],
    queryFn: () => authApi.getZerodhaSession(userIdentifier || undefined),
    enabled: authReady && !!userIdentifier,
  });

  /**
   * React Query: Refresh service status
   */
  const { data: refreshStatus } = useQuery({
    queryKey: ["refresh-status"],
    queryFn: authApi.getRefreshStatus,
    enabled: authReady,
    refetchInterval: 60000,
  });

  /**
   * Zerodha login mutation (legacy broker login)
   */
  const loginMutation = useMutation({
    mutationFn: async (state?: string) => {
      const response = await authApi.getZerodhaLoginUrl(state);
      return response;
    },
  });

  /**
   * Refresh Zerodha token mutation
   */
  const refreshMutation = useMutation({
    mutationFn: async () => {
      return await authApi.refreshToken(userIdentifier || undefined);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["zerodha-session"] });
    },
  });

  /**
   * Derived auth state
   */
  const isAuthenticated = useMemo(() => {
    return authReady && !!accessToken;
  }, [authReady, accessToken]);

  /**
   * Public login helper for broker connection (legacy)
   */
  const login = useCallback(
    async (state?: string) => {
      const response = await loginMutation.mutateAsync(state);
      if (response.login_url) {
        if (state) {
          localStorage.setItem("user_identifier", state);
          setUserIdentifier(state);
        }
        window.location.href = response.login_url;
      }
    },
    [loginMutation]
  );

  /**
   * Logout: clear all auth state
   */
  const logout = useCallback(() => {
    localStorage.removeItem("user_identifier");
    localStorage.removeItem("user");
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setUserIdentifier(null);
    setUser(null);
    setAccessToken(null);
    setRefreshTokenValue(null);
    queryClient.clear();
  }, [queryClient]);

  const isLoading = useMemo(() => {
    if (!authReady) return true;
    return brokerLoading || sessionLoading;
  }, [authReady, brokerLoading, sessionLoading]);

  return {
    isAuthenticated,
    isLoading,
    authReady,
    user,
    userIdentifier,
    accessToken,
    storedRefreshToken: refreshTokenValue,
    session: session?.session,
    brokerStatus: brokerStatus?.brokers,
    refreshStatus: refreshStatus?.refresh_service,
    login,
    logout,
    refreshToken: refreshMutation.mutate,
    refetchSession,
  };
}

