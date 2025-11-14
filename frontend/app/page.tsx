import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { LoginForm } from "@/components/features/auth/LoginForm";

/**
 * Home page - Login screen
 * 
 * This is the main entry point for the application.
 * Users must authenticate here before accessing the dashboard.
 */
export default function HomePage() {
  return (
    <div className="flex h-screen items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <Card className="w-[450px]">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold">TradeDesk</CardTitle>
          <CardDescription>
            SEBI-compliant algorithmic trading platform
          </CardDescription>
        </CardHeader>
        <CardContent>
          <LoginForm />
        </CardContent>
      </Card>
    </div>
  );
}