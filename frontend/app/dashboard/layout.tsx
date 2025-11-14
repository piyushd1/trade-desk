import { DashboardLayout } from "@/components/layouts/DashboardLayout";

/**
 * Dashboard layout wrapper
 * Provides the authenticated layout with sidebar navigation
 */
export default function Layout({ children }: { children: React.ReactNode }) {
  return <DashboardLayout>{children}</DashboardLayout>;
}