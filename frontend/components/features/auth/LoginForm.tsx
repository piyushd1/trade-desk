"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import type { LoginFormData } from "@/lib/types";

interface LoginFormProps {
  /** Callback after successful login */
  onSuccess?: () => void;
  /** Whether to redirect to dashboard after login */
  redirectToDashboard?: boolean;
}

/**
 * Login form component with username/password authentication
 * 
 * Features:
 * - Form validation
 * - Loading states
 * - Error handling
 * - JWT token storage
 * - Automatic redirect to dashboard
 * 
 * @example
 * ```tsx
 * <LoginForm />
 * <LoginForm onSuccess={() => console.log('Logged in!')} />
 * ```
 */
export function LoginForm({ onSuccess, redirectToDashboard = true }: LoginFormProps) {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState<LoginFormData>({
    username: "",
    password: "",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Basic validation
    if (!formData.username || !formData.password) {
      toast.error("Please enter both username and password");
      return;
    }

    setIsLoading(true);

    try {
      const response = await api.post("/auth/login", formData);

      if (response.data.status === "success") {
        // Store authentication data
        localStorage.setItem("access_token", response.data.access_token);
        localStorage.setItem("refresh_token", response.data.refresh_token);
        localStorage.setItem("user", JSON.stringify(response.data.user));
        localStorage.setItem("user_identifier", response.data.user.username);

        toast.success("Login successful!");

        // Trigger callback if provided
        onSuccess?.();

        // Redirect to dashboard
        if (redirectToDashboard) {
          router.push("/dashboard");
        }
      }
    } catch (error: any) {
      const errorMessage = 
        error.response?.data?.detail || 
        error.response?.data?.message || 
        "Login failed. Please try again.";
      
      toast.error(errorMessage);
      
      // Clear password on error
      setFormData((prev) => ({ ...prev, password: "" }));
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (field: keyof LoginFormData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="username">Username</Label>
        <Input
          id="username"
          type="text"
          placeholder="Enter your username"
          value={formData.username}
          onChange={(e) => handleInputChange("username", e.target.value)}
          disabled={isLoading}
          autoComplete="username"
          autoFocus
          required
        />
      </div>
      
      <div className="space-y-2">
        <Label htmlFor="password">Password</Label>
        <Input
          id="password"
          type="password"
          placeholder="Enter your password"
          value={formData.password}
          onChange={(e) => handleInputChange("password", e.target.value)}
          disabled={isLoading}
          autoComplete="current-password"
          required
        />
      </div>

      <Button 
        type="submit" 
        className="w-full" 
        disabled={isLoading || !formData.username || !formData.password}
      >
        {isLoading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Logging in...
          </>
        ) : (
          "Login"
        )}
      </Button>
    </form>
  );
}
