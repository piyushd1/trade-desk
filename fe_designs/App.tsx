import { useState } from 'react';
import { Dashboard } from './components/Dashboard';
import { Strategies } from './components/Strategies';
import { Backtest } from './components/Backtest';
import { Orders } from './components/Orders';
import { Settings } from './components/Settings';
import { TradeHistory } from './components/TradeHistory';
import { Sidebar } from './components/Sidebar';

export default function App() {
  const [currentPage, setCurrentPage] = useState<'dashboard' | 'strategies' | 'backtest' | 'orders' | 'trade-history' | 'settings'>('dashboard');

  return (
    <div className="flex h-screen bg-[#F5F5F5]">
      <Sidebar currentPage={currentPage} onNavigate={setCurrentPage} />
      <main className="flex-1 overflow-auto">
        {currentPage === 'dashboard' && <Dashboard />}
        {currentPage === 'strategies' && <Strategies />}
        {currentPage === 'backtest' && <Backtest />}
        {currentPage === 'orders' && <Orders />}
        {currentPage === 'trade-history' && <TradeHistory />}
        {currentPage === 'settings' && <Settings />}
      </main>
    </div>
  );
}