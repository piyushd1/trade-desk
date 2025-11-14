"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/hooks/use-auth";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";

interface AuthGuardProps {
  children: React.ReactNode;
  /** Where to redirect if not authenticated */
  redirectTo?: string;
  /** Show loading spinner while checking auth */
  showLoader?: boolean;
}

/**
 * Authentication guard component
 * Protects routes by checking authentication status
 * 
 * @example
 * ```tsx
 * <AuthGuard>
 *   <ProtectedContent />
 * </AuthGuard>
 * ```
 */
export function AuthGuard({ 
  children, 
  redirectTo = "/", 
  showLoader = true 
}: AuthGuardProps) {
  const router = useRouter();
  const { isAuthenticated, isLoading, authReady } = useAuth();

  useEffect(() => {
    if (authReady && !isLoading && !isAuthenticated) {
      router.push(redirectTo);
    }
  }, [isAuthenticated, isLoading, authReady, router, redirectTo]);

  // Show loader while checking authentication
  if (!authReady || isLoading) {
    if (showLoader) {
      return <LoadingSpinner center size="lg" text="Checking authentication..." />;
    }
    return null;
  }

  // Not authenticated
  if (!isAuthenticated) {
    return null;
  }

  // Authenticated - render children
  return <>{children}</>;
}
