"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();

  const handleLogin = () => {
    // Redirect to OAuth endpoint
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || '/api/v1';
    window.location.href = `${apiUrl}/auth/zerodha/connect?state=web_user`;
  };

  return (
    <div className="flex h-screen items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="w-[450px] rounded-lg border bg-white p-8 shadow-lg">
        <div className="space-y-4">
          <div>
            <h1 className="text-2xl font-bold">TradeDesk</h1>
            <p className="text-sm text-gray-600">
              SEBI-compliant algorithmic trading platform
            </p>
          </div>
          
          <div className="space-y-2">
            <h3 className="font-semibold">Connect your broker</h3>
            <p className="text-sm text-gray-600">
              Login with Zerodha to start trading
            </p>
          </div>
          
          <button
            onClick={handleLogin}
            className="w-full rounded-lg bg-blue-600 px-4 py-3 text-white font-medium hover:bg-blue-700 transition-colors"
          >
            Connect Zerodha Account
          </button>

          <div className="text-xs text-center text-gray-500 space-y-1">
            <p>Secure OAuth authentication</p>
            <p>Your credentials are never stored</p>
          </div>
        </div>
      </div>
    </div>
  );
}
