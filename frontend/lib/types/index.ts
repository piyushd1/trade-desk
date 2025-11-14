/**
 * Shared TypeScript types for the TradeDesk frontend
 */

// Re-export API types
export type {
  ApiResponse,
  BrokerSession,
  RiskConfig,
  DailyMetrics,
  AuditLog,
  SystemEvent,
  RiskBreach,
} from "@/lib/api";

// User types
export interface User {
  id: number;
  username: string;
  email?: string | null;
  full_name?: string | null;
  role?: string | null;
}

// Auth types
export interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

// Component prop types
export interface WithClassName {
  className?: string;
}

export interface WithChildren {
  children: React.ReactNode;
}

// Form types
export interface LoginFormData {
  username: string;
  password: string;
}

// API error types
export interface ApiError {
  error?: {
    message?: string;
    detail?: string;
  };
  detail?: string;
  message?: string;
}

// Table column types
export interface TableColumn<T> {
  key: keyof T | string;
  header: string;
  accessor?: (item: T) => React.ReactNode;
  className?: string;
}

// Status types
export type TradingStatus = "enabled" | "disabled";
export type SessionStatus = "active" | "expired" | "not_found";
export type HealthStatus = "healthy" | "unhealthy" | "unknown";
