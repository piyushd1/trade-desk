import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface LoadingSpinnerProps {
  /** Size of the spinner */
  size?: "sm" | "md" | "lg";
  /** Additional CSS classes */
  className?: string;
  /** Loading text to display */
  text?: string;
  /** Whether to center the spinner in its container */
  center?: boolean;
}

const sizeClasses = {
  sm: "h-4 w-4",
  md: "h-6 w-6",
  lg: "h-8 w-8",
};

/**
 * Reusable loading spinner component
 * 
 * @example
 * ```tsx
 * <LoadingSpinner />
 * <LoadingSpinner size="lg" text="Loading data..." />
 * <LoadingSpinner center />
 * ```
 */
export function LoadingSpinner({
  size = "md",
  className,
  text,
  center = false,
}: LoadingSpinnerProps) {
  const spinner = (
    <div className={cn("flex items-center gap-2", className)}>
      <Loader2 className={cn("animate-spin text-primary", sizeClasses[size])} />
      {text && <span className="text-sm text-muted-foreground">{text}</span>}
    </div>
  );

  if (center) {
    return (
      <div className="flex min-h-[200px] items-center justify-center">
        {spinner}
      </div>
    );
  }

  return spinner;
}
