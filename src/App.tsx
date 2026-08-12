import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { Simulator } from './components/Simulator';
import { Configurator } from './components/Configurator';
import { DatabaseSchema } from './components/DatabaseSchema';
import { RailwayDeployment } from './components/RailwayDeployment';
import { CommandMatrix } from './components/CommandMatrix';
import { CodeViewer } from './components/CodeViewer';
import { BotStatus } from './types';

export default function App() {
  const [activeTab, setActiveTab] = useState<string>('simulator');
  const [status, setStatus] = useState<BotStatus | null>(null);

  useEffect(() => {
    fetch('/api/bot/status')
      .then((res) => res.json())
      .then((data) => setStatus(data))
      .catch((err) => console.error(err));
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans antialiased selection:bg-indigo-500 selection:text-white">
      
      {/* Top Header & Tab Navigation */}
      <Header status={status} activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'simulator' && <Simulator />}
        {activeTab === 'configurator' && <Configurator />}
        {activeTab === 'database' && <DatabaseSchema />}
        {activeTab === 'railway' && <RailwayDeployment />}
        {activeTab === 'commands' && <CommandMatrix />}
        {activeTab === 'code' && <CodeViewer />}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 text-slate-500 py-6 text-center text-xs">
        <div className="max-w-7xl mx-auto px-4">
          <p>Security & Management Bot • المصمم للإنتاج على Railway و Supabase PostgreSQL</p>
          <p className="mt-1 text-slate-600">Python 3.11 • discord.py • SQLAlchemy Async • Slash Commands</p>
        </div>
      </footer>

    </div>
  );
}
