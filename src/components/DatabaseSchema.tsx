import React, { useState } from 'react';
import { Database, Table, Key, Copy, Check, ShieldCheck, Download } from 'lucide-react';

export const DatabaseSchema: React.FC = () => {
  const [copiedSql, setCopiedSql] = useState(false);
  const [supabaseUrl, setSupabaseUrl] = useState('postgresql+asyncpg://postgres:your-password@db.project-ref.supabase.co:5432/postgres');
  const [copiedUrl, setCopiedUrl] = useState(false);

  const tables = [
    { name: 'guilds', desc: 'جدول السيرفرات الأساسية والمحالة الفعالة', pk: 'guild_id (BIGINT)', fields: ['guild_id', 'name', 'joined_at', 'is_active', 'created_at'] },
    { name: 'guild_settings', desc: 'إعدادات اللغة والبادئة والمنطقة الزمنية', pk: 'guild_id (FK -> guilds)', fields: ['guild_id', 'prefix', 'language', 'timezone'] },
    { name: 'security_settings', desc: 'إعدادات وحدود Anti-Raid و Anti-Nuke', pk: 'guild_id (FK -> guilds)', fields: ['anti_raid_enabled', 'anti_raid_join_threshold', 'anti_raid_time_window', 'anti_raid_action', 'anti_nuke_enabled', 'anti_nuke_channel_threshold', 'anti_nuke_role_threshold', 'anti_nuke_action'] },
    { name: 'automod_settings', desc: 'خيارات الإشراف التلقائي وقوائم الكلمات المحظورة', pk: 'guild_id (FK -> guilds)', fields: ['enabled', 'anti_spam_enabled', 'max_messages_per_5s', 'max_mentions', 'block_invites', 'block_links', 'bad_words TEXT[]', 'whitelisted_words TEXT[]', 'ignored_channels BIGINT[]'] },
    { name: 'verification_settings', desc: 'إعدادات بنل التوثيق ورتب الموثقين', pk: 'guild_id (FK -> guilds)', fields: ['enabled', 'channel_id', 'verified_role_id', 'unverified_role_id', 'panel_message_id', 'title', 'description'] },
    { name: 'log_settings', desc: 'خريطة قنوات اللوجز الـ 7 لكل الأحداث الإدارية', pk: 'guild_id (FK -> guilds)', fields: ['member_log_channel_id', 'message_log_channel_id', 'moderation_log_channel_id', 'role_log_channel_id', 'channel_log_channel_id', 'server_log_channel_id', 'security_log_channel_id'] },
    { name: 'punishment_settings', desc: 'سلم العقوبات التلقائية للتحذيرات', pk: 'guild_id (FK -> guilds)', fields: ['warn_3_action', 'warn_5_action', 'warn_7_action'] },
    { name: 'warnings', desc: 'سجل تحذيرات الأعضاء والمعرفات الفريدة UUID', pk: 'warning_id (VARCHAR-36)', fields: ['warning_id', 'guild_id', 'user_id', 'moderator_id', 'reason', 'created_at'] },
    { name: 'moderation_actions', desc: 'سجل كافة الأوامر الإدارية (Kicks, Bans, Timeouts)', pk: 'action_id (VARCHAR-36)', fields: ['action_id', 'guild_id', 'user_id', 'moderator_id', 'action_type', 'reason', 'duration'] },
    { name: 'whitelist_users', desc: 'الأعضاء الموثوقون المعفون من نظام الحماية', pk: 'id (SERIAL)', fields: ['id', 'guild_id', 'user_id', 'added_by', 'reason'] },
    { name: 'whitelist_roles', desc: 'الرتب الموثوقة المعفاة من الحماية', pk: 'id (SERIAL)', fields: ['id', 'guild_id', 'role_id', 'added_by', 'reason'] },
    { name: 'whitelist_bots', desc: 'البوتات الموثوقة المستثناة', pk: 'id (SERIAL)', fields: ['id', 'guild_id', 'bot_id', 'added_by', 'reason'] }
  ];

  const sqlCode = `-- Supabase PostgreSQL Complete DDL Script
CREATE TABLE IF NOT EXISTS guilds (
    guild_id BIGINT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS security_settings (
    guild_id BIGINT PRIMARY KEY REFERENCES guilds(guild_id) ON DELETE CASCADE,
    anti_raid_enabled BOOLEAN DEFAULT FALSE,
    anti_raid_join_threshold INT DEFAULT 5,
    anti_raid_time_window INT DEFAULT 10,
    anti_raid_action VARCHAR(50) DEFAULT 'lockdown',
    anti_nuke_enabled BOOLEAN DEFAULT FALSE,
    anti_nuke_channel_threshold INT DEFAULT 3,
    anti_nuke_role_threshold INT DEFAULT 3,
    anti_nuke_action VARCHAR(50) DEFAULT 'remove_roles'
);
-- See schema.sql for full 14 tables DDL`;

  const copySql = () => {
    navigator.clipboard.writeText(sqlCode);
    setCopiedSql(true);
    setTimeout(() => setCopiedSql(false), 2000);
  };

  const copyUrl = () => {
    navigator.clipboard.writeText(supabaseUrl);
    setCopiedUrl(true);
    setTimeout(() => setCopiedUrl(false), 2000);
  };

  return (
    <div className="space-y-6">
      
      {/* Intro & Connection String */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <Database className="w-6 h-6 text-emerald-400" />
              هيكلية قاعدة البيانات في Supabase PostgreSQL
            </h2>
            <p className="text-sm text-slate-400 mt-1">
              صممت قاعدة البيانات خصيصًا لتلبي متطلبات **Multi-Guild Data Isolation** مع 14 جدولا متكاملاً مبنية بواسطة SQLAlchemy Async ومحرك `asyncpg`.
            </p>
          </div>

          <button
            onClick={copySql}
            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-xl text-xs flex items-center gap-2 shadow-lg shadow-emerald-600/20"
          >
            {copiedSql ? <Check className="w-4 h-4" /> : <Download className="w-4 h-4" />}
            {copiedSql ? 'تم النسخ!' : 'نسخ ملف schema.sql'}
          </button>
        </div>

        {/* Supabase Connection String Builder */}
        <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-2">
          <label className="text-xs font-bold text-slate-300 block">
            صيغة رابط الاتصال لقاعدة البيانات Supabase DATABASE_URL:
          </label>
          <div className="flex gap-2">
            <input
              type="text"
              value={supabaseUrl}
              onChange={(e) => setSupabaseUrl(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 text-emerald-400 font-mono text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-emerald-500"
            />
            <button
              onClick={copyUrl}
              className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-semibold whitespace-nowrap flex items-center gap-1.5"
            >
              {copiedUrl ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
              نسخ
            </button>
          </div>
          <p className="text-[11px] text-slate-500">
            * ملاحظة: يجب استخدام بادئة <code className="text-indigo-400">postgresql+asyncpg://</code> لتمكين دعم الاتصالات اللا تزامنية مع Supabase Transaction Pooler.
          </p>
        </div>
      </div>

      {/* Grid of Database Tables */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {tables.map((t, idx) => (
          <div key={idx} className="bg-slate-900 border border-slate-800 hover:border-slate-700 transition-all rounded-2xl p-5 space-y-3 flex flex-col justify-between">
            <div className="space-y-2">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <span className="font-bold text-sm text-indigo-300 flex items-center gap-2 font-mono">
                  <Table className="w-4 h-4 text-indigo-400" />
                  {t.name}
                </span>
                <span className="text-[10px] bg-slate-800 text-slate-300 px-2 py-0.5 rounded-full font-mono border border-slate-700">
                  SQL Table
                </span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">{t.desc}</p>
            </div>

            <div className="space-y-2 text-xs pt-2 border-t border-slate-800/80">
              <div className="flex items-center gap-1.5 font-mono text-amber-400">
                <Key className="w-3.5 h-3.5" />
                <span>PK: {t.pk}</span>
              </div>

              <div className="flex flex-wrap gap-1 pt-1">
                {t.fields.map((f, i) => (
                  <span key={i} className="bg-slate-950 text-slate-300 border border-slate-800 px-2 py-0.5 rounded text-[11px] font-mono">
                    {f}
                  </span>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>

    </div>
  );
};
