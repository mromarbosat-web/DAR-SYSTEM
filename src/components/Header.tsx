import React from 'react';
import { Shield, ShieldAlert, Database, Server, CheckCircle2, AlertTriangle } from 'lucide-react';
import { BotStatus } from '../types';

interface HeaderProps {
  status: BotStatus | null;
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const Header: React.FC<HeaderProps> = ({ status, activeTab, setActiveTab }) => {
  return (
    <header className="bg-slate-900 border-b border-slate-800 text-white sticky top-0 z-50 shadow-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          
          {/* Logo & Title */}
          <div className="flex items-center space-x-3 space-x-reverse">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-pink-500 p-0.5 shadow-lg shadow-indigo-500/20">
              <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
                <Shield className="w-6 h-6 text-indigo-400" />
              </div>
            </div>
            <div>
              <div className="flex items-center space-x-2 space-x-reverse">
                <h1 className="text-xl font-bold tracking-tight bg-gradient-to-r from-white via-slate-100 to-indigo-200 bg-clip-text text-transparent">
                  Security & Management Bot
                </h1>
                <span className="px-2 py-0.5 text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 rounded-full">
                  v1.0.0
                </span>
              </div>
              <p className="text-xs text-slate-400">
                مستودع الكود وتطبيقات الاختبار والنشر على Railway & Supabase PostgreSQL
              </p>
            </div>
          </div>

          {/* Quick Badges & Actions */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 bg-slate-800/80 border border-slate-700/60 px-3 py-1.5 rounded-lg text-xs font-medium">
              <Server className="w-4 h-4 text-purple-400" />
              <span className="text-slate-300">Railway:</span>
              <span className="text-emerald-400 font-semibold">Worker Ready</span>
            </div>

            <div className="flex items-center gap-2 bg-slate-800/80 border border-slate-700/60 px-3 py-1.5 rounded-lg text-xs font-medium">
              <Database className="w-4 h-4 text-emerald-400" />
              <span className="text-slate-300">Database:</span>
              <span className="text-indigo-400 font-semibold">Supabase AsyncPG</span>
            </div>

            {status && (
              <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border ${
                status.configured 
                  ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' 
                  : 'bg-amber-500/10 border-amber-500/20 text-amber-400'
              }`}>
                {status.configured ? (
                  <>
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    <span>Env Complete</span>
                  </>
                ) : (
                  <>
                    <AlertTriangle className="w-4 h-4 text-amber-400" />
                    <span>Ready for Railway Config</span>
                  </>
                )}
              </div>
            )}
          </div>

        </div>

        {/* Navigation Tabs */}
        <nav className="flex space-x-1 space-x-reverse overflow-x-auto mt-4 pt-2 border-t border-slate-800/60 text-sm font-medium scrollbar-none">
          {[
            { id: 'simulator', label: '🧪 مختبر المحاكاة (Live Simulator)', icon: 'ShieldAlert' },
            { id: 'configurator', label: '⚙️ موجه الإعدادات (Bot Setup)', icon: 'Sliders' },
            { id: 'database', label: '🗄️ Supabase Schema (14 Tables)', icon: 'Database' },
            { id: 'railway', label: '🚀 النشر على Railway & Env', icon: 'Server' },
            { id: 'commands', label: '📜 مصفوفة الأوامر (Commands)', icon: 'Terminal' },
            { id: 'code', label: '💻 كود المشروع بـ Python', icon: 'Code' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 rounded-lg whitespace-nowrap transition-all duration-200 ${
                activeTab === tab.id
                  ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30 font-semibold'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>
    </header>
  );
};
