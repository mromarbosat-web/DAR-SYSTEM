import React, { useState } from 'react';
import { Server, Check, Copy, Terminal, FileCode, Shield, Info, AlertCircle } from 'lucide-react';

export const RailwayDeployment: React.FC = () => {
  const [tokenInput, setTokenInput] = useState('');
  const [dbInput, setDbInput] = useState('');
  const [copiedEnv, setCopiedEnv] = useState(false);

  const generateEnv = () => {
    return `# Security & Management Bot Production Environment Variables
DISCORD_BOT_TOKEN=${tokenInput || 'your_discord_bot_token_here'}
DATABASE_URL=${dbInput || 'postgresql+asyncpg://postgres:password@db.example.supabase.co:5432/postgres'}
LOG_LEVEL=INFO
ENVIRONMENT=production
BOT_PREFIX=!
DEFAULT_EMBED_COLOR=0x5865F2`;
  };

  const copyEnv = () => {
    navigator.clipboard.writeText(generateEnv());
    setCopiedEnv(true);
    setTimeout(() => setCopiedEnv(false), 2000);
  };

  return (
    <div className="space-y-6">
      
      {/* Intro Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
        <div className="flex items-center space-x-3 space-x-reverse mb-2">
          <div className="p-2 bg-purple-500/10 border border-purple-500/20 rounded-xl text-purple-400">
            <Server className="w-6 h-6" />
          </div>
          <h2 className="text-xl font-bold text-white">دليل النشر والتشغيل على Railway Worker</h2>
        </div>
        <p className="text-sm text-slate-300 leading-relaxed max-w-3xl">
          تم تصميم البوت كـ **Background Worker** بدون الحاجة لمنفذ سيرفر محلي، مما يجعله جاهزًا فورًا للنشر الاستضافي التلقائي على Railway مجانًا أو عبر خطة المشاريع.
        </p>
      </div>

      {/* Deployment Steps */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          {
            step: '01',
            title: 'ربط المستودع بـ Railway',
            desc: 'قم بإنشاء مشروع جديد في Railway واختر Deploy from GitHub Repo. سيقوم Railway باكتشاف الـ Dockerfile و railway.json تلقائيًا.'
          },
          {
            step: '02',
            title: 'تحديد نوع التطبيق Worker',
            desc: 'تأكد أن نوع الخدمة هو Worker وأن أمر البدء هو: python -m bot.main.'
          },
          {
            step: '03',
            title: 'إضافة المتغيرات البيئية',
            desc: 'انتقل لتبويب Variables في Railway وأضف DISCORD_BOT_TOKEN و DATABASE_URL الخاص بـ Supabase.'
          }
        ].map((s, idx) => (
          <div key={idx} className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-3 relative overflow-hidden">
            <div className="text-4xl font-black text-slate-800/80 absolute top-3 left-4 font-mono select-none">
              {s.step}
            </div>
            <h3 className="text-base font-bold text-white relative z-10">{s.title}</h3>
            <p className="text-xs text-slate-400 relative z-10 leading-relaxed">{s.desc}</p>
          </div>
        ))}
      </div>

      {/* Interactive Env Variable Generator */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Form Inputs */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
          <h3 className="text-base font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-3">
            <Shield className="w-5 h-5 text-indigo-400" />
            مولد متغيرات البيئة (Railway .env Generator)
          </h3>

          <div className="space-y-4 text-sm">
            <div>
              <label className="block text-slate-300 mb-1 font-medium">DISCORD_BOT_TOKEN:</label>
              <input
                type="password"
                placeholder="MTEyMzQ1Njc4OTAxMjM0NTY3OA.G..."
                value={tokenInput}
                onChange={(e) => setTokenInput(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 text-white rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-indigo-500 font-mono"
              />
              <span className="text-[11px] text-slate-500 block mt-1">
                احصل عليه من Discord Developer Portal -&gt; Bot -&gt; Reset Token.
              </span>
            </div>

            <div>
              <label className="block text-slate-300 mb-1 font-medium">DATABASE_URL (Supabase PostgreSQL):</label>
              <input
                type="text"
                placeholder="postgresql+asyncpg://postgres:pass@db.ref.supabase.co:5432/postgres"
                value={dbInput}
                onChange={(e) => setDbInput(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 text-white rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-indigo-500 font-mono text-xs"
              />
              <span className="text-[11px] text-slate-500 block mt-1">
                انسخه من Supabase Project Settings -&gt; Database URI مع استبدال البادئة بـ postgresql+asyncpg://
              </span>
            </div>
          </div>
        </div>

        {/* Output Box */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4 flex flex-col justify-between">
          <div className="space-y-3">
            <div className="flex justify-between items-center border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <FileCode className="w-5 h-5 text-purple-400" />
                ملف .env الجاهز للنسخ المباشر
              </h3>
            </div>

            <pre className="bg-slate-950 border border-slate-800 rounded-xl p-4 font-mono text-xs text-purple-300 leading-relaxed overflow-x-auto whitespace-pre-wrap">
              {generateEnv()}
            </pre>
          </div>

          <button
            onClick={copyEnv}
            className="w-full bg-purple-600 hover:bg-purple-500 text-white font-bold py-3 rounded-xl shadow-lg shadow-purple-600/30 transition-all flex items-center justify-center gap-2"
          >
            {copiedEnv ? <Check className="w-5 h-5 text-emerald-300" /> : <Copy className="w-5 h-5" />}
            {copiedEnv ? 'تم النسخ!' : 'نسخ النص ولصقه في Variables في Railway'}
          </button>
        </div>

      </div>

    </div>
  );
};
