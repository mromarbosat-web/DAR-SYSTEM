import React, { useState } from 'react';
import { Terminal, Search, Shield, Zap, Lock, ListFilter, Sliders, Info, KeyRound } from 'lucide-react';
import { CommandInfo } from '../types';

export const CommandMatrix: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCat, setSelectedCat] = useState<string>('all');

  const commands: CommandInfo[] = [
    // Security
    { name: '/security setup', category: 'security', description: 'ضبط إعدادات وقيم أنظمة Anti-Raid و Anti-Nuke', permission: 'Administrator', syntax: '/security setup [anti_raid] [raid_threshold] [raid_action] [anti_nuke] [nuke_action]', options: [{ name: 'anti_raid', description: 'تفعيل/تعطيل Anti-Raid', required: false }] },
    { name: '/security status', category: 'security', description: 'عرض تقرير شاملاً بحالة الخيارات الأمنية والحدود المعتمدة', permission: 'Administrator', syntax: '/security status', options: [] },
    { name: '/lock', category: 'security', description: 'إغلاق القناة الحالية أو كافة قنوات السيرفر بمنع إرسال الرسائل', permission: 'Manage Channels', syntax: '/lock [all_channels] [reason]', options: [{ name: 'all_channels', description: 'إغلاق كلي لجميع القنوات النصية', required: false }] },
    { name: '/unlock', category: 'security', description: 'فتح القناة أو كافة القنوات والسماح بالكتابة مجددًا', permission: 'Manage Channels', syntax: '/unlock [all_channels]', options: [] },

    // AutoMod
    { name: '/automod setup', category: 'automod', description: 'تخصيص فلاتر منع الروابط والدعوات والسبام والسلوك التكراري', permission: 'Administrator', syntax: '/automod setup [enabled] [anti_spam] [block_invites] [block_links] [max_mentions]', options: [] },
    { name: '/automod status', category: 'automod', description: 'استعراض حالة فلاتر AutoMod ونوع الإجراءات المعتمدة', permission: 'Administrator', syntax: '/automod status', options: [] },
    { name: '/automod badwords', category: 'automod', description: 'إضافة أو حذف كلمات من قائمة المحظورات والـ Blacklist', permission: 'Administrator', syntax: '/automod badwords <mode> <words>', options: [{ name: 'words', description: 'الكلمات مفصولة بفواصل', required: true }] },

    // Warnings & Moderation
    { name: '/warn', category: 'warnings', description: 'توجيه تحذير رسمي أو شفهي للعضو مع تسجيل الأدلة وفحص العقوبات التلقائية', permission: 'Issuer Role / Moderate Members', syntax: '/warn <user> <reason> [type: formal|verbal] [duration] [evidence]', options: [] },
    { name: '/warnings', category: 'warnings', description: 'عرض قائمة وسجل تحذيرات عضو محدد أو تحذيراتك الشخصية', permission: 'Viewer Role / Moderate Members', syntax: '/warnings [user]', options: [] },
    { name: '/warning view', category: 'warnings', description: 'عرض تفاصيل تحذير محدد باستخدام المعرف ID بما فيها الأدلة والتعديلات', permission: 'Viewer Role / Moderate Members', syntax: '/warning view <warning_id>', options: [] },
    { name: '/warning history', category: 'warnings', description: 'استعراض السجل الكامل للتغييرات والإجراءات المتخذة بحق عضو', permission: 'Viewer Role / Moderate Members', syntax: '/warning history <user>', options: [] },
    { name: '/warning edit', category: 'warnings', description: 'تعديل سبب أو دليل أو مدة تحذير نشط مسبقًا', permission: 'Editor Role / Moderate Members', syntax: '/warning edit <warning_id> [reason] [evidence] [duration]', options: [] },
    { name: '/warning remove', category: 'warnings', description: 'حذف أو إلغاء (Void) تحذير معين مع تسجيل سبب الحذف', permission: 'Remover Role / Administrator', syntax: '/warning remove <warning_id> <reason> [void: true|false]', options: [] },
    { name: '/warning expire', category: 'warnings', description: 'إنهاء صلاحية تحذير نشط فوراً دون حذفه من السجل التاريخي', permission: 'Expirer Role / Moderate Members', syntax: '/warning expire <warning_id>', options: [] },
    { name: '/warning settings', category: 'warnings', description: 'ضبط رتب وصلاحيات وقناة أدلة تحذيرات السيرفر والترقية الآلية', permission: 'Settings Manager / Administrator', syntax: '/warning settings [issuer_role] [viewer_role] [editor_role] [evidence_channel] [demotion_threshold]', options: [] },

    // Voice Management
    { name: '/voice move', category: 'voice', description: 'نقل عضو واحد أو جميع أعضاء قناة صوتية إلى قناة أخرى مع مراعاة الرتب', permission: 'Move Members / Voice Manager', syntax: '/voice move <target_channel> [member] [source_channel]', options: [] },
    { name: '/voice disconnect', category: 'voice', description: 'فصل عضو أو جميع أعضاء قناة صوتية من الروم الصوتي', permission: 'Move Members / Voice Manager', syntax: '/voice disconnect [member] [channel]', options: [] },
    { name: '/voice mute', category: 'voice', description: 'كتم صوت عضو أو جميع أعضاء القناة الصوتية (Server Mute)', permission: 'Mute Members / Voice Manager', syntax: '/voice mute [member] [channel] [reason]', options: [] },
    { name: '/voice unmute', category: 'voice', description: 'إلغاء كتم صوت عضو أو جميع أعضاء القناة الصوتية', permission: 'Mute Members / Voice Manager', syntax: '/voice unmute [member] [channel] [reason]', options: [] },
    { name: '/voice lock', category: 'voice', description: 'قفل القناة الصوتية وتحديد سعة الدخول أو منع الاتصال', permission: 'Manage Channels / Voice Manager', syntax: '/voice lock [channel] [user_limit] [reason]', options: [] },
    { name: '/voice unlock', category: 'voice', description: 'فتح القناة الصوتية وإزالة قيود الدخول المقفلة', permission: 'Manage Channels / Voice Manager', syntax: '/voice unlock [channel] [reason]', options: [] },
    { name: '/voice settings', category: 'voice', description: 'ضبط رتبة مدير الصوت وقناة سجلات الإجراءات الصوتية', permission: 'Administrator / Voice Manager', syntax: '/voice settings [manager_role] [log_channel]', options: [] },

    // Standard Moderation
    { name: '/timeout', category: 'moderation', description: 'عزل العضو مؤقتًا لمدة محددة (مثل 10m, 1h, 1d)', permission: 'Moderate Members', syntax: '/timeout <user> <duration> [reason]', options: [] },
    { name: '/untimeout', category: 'moderation', description: 'فك العزل المؤقت عن العضو', permission: 'Moderate Members', syntax: '/untimeout <user>', options: [] },
    { name: '/kick', category: 'moderation', description: 'طرد عضو من السيرفر', permission: 'Kick Members', syntax: '/kick <user> [reason]', options: [] },
    { name: '/ban', category: 'moderation', description: 'حظر عضو نهائيًا من السيرفر مع خيار حذف الرسائل', permission: 'Ban Members', syntax: '/ban <user> [reason] [delete_days]', options: [] },
    { name: '/unban', category: 'moderation', description: 'فك حظر عضو باستخدام User ID', permission: 'Ban Members', syntax: '/unban <user_id> [reason]', options: [] },
    { name: '/softban', category: 'moderation', description: 'حظر ثم فك حظر فورًا لتطهير رسائل العضو الأخيرة', permission: 'Ban Members', syntax: '/softban <user> [reason]', options: [] },
    { name: '/purge', category: 'moderation', description: 'مسح عدد محدد من الرسائل في القناة (حتى 100 رسالة)', permission: 'Manage Messages', syntax: '/purge <amount> [user]', options: [] },
    { name: '/slowmode', category: 'moderation', description: 'ضبط الوضع البطيء للقناة بالثواني بين كل رسالة', permission: 'Manage Channels', syntax: '/slowmode <seconds>', options: [] },

    // Verification
    { name: '/verification setup', category: 'verification', description: 'إرسال لوحة التحقق التفاعلية برتبة Verified بزر تفاعلي', permission: 'Administrator', syntax: '/verification setup <channel> <verified_role> [unverified_role]', options: [] },
    { name: '/verification status', category: 'verification', description: 'عرض إعدادات وقناة ورتب نظام التحقق', permission: 'Administrator', syntax: '/verification status', options: [] },

    // Logs
    { name: '/logs setup', category: 'logs', description: 'تحديد القناة المخصصة لكل نوع من أنواع الـ Logs الـ 7', permission: 'Administrator', syntax: '/logs setup <log_type> [channel]', options: [] },
    { name: '/logs status', category: 'logs', description: 'عرض خريطة القنوات المخصصة للسجلات بالكامل', permission: 'Administrator', syntax: '/logs status', options: [] },

    // Whitelist & Setup
    { name: '/whitelist user', category: 'whitelist', description: 'إضافة/إزالة عضو موثوق من القائمة البيضاء لتجاوز الحماية', permission: 'Administrator', syntax: '/whitelist user <action> <user>', options: [] },
    { name: '/whitelist role', category: 'whitelist', description: 'إضافة/إزالة رتبة موثوقة بالكامل من القائمة البيضاء', permission: 'Administrator', syntax: '/whitelist role <action> <role>', options: [] },
    { name: '/whitelist list', category: 'whitelist', description: 'استعراض القائمة البيضاء للأعضاء والرتب الموثوقة', permission: 'Administrator', syntax: '/whitelist list', options: [] },
    { name: '/punishments setup', category: 'whitelist', description: 'تخصيص عقوبة الترقية عند 3 و 5 و 7 تحذيرات', permission: 'Administrator', syntax: '/punishments setup [warn_3] [warn_5] [warn_7]', options: [] },

    // Utility
    { name: '/ping', category: 'utility', description: 'فحص زَمَن الاستجابة وتأخير اتصال البوت مع Discord Gateway', permission: 'Everyone', syntax: '/ping', options: [] },
    { name: '/botinfo', category: 'utility', description: 'استعراض بيانات وإحصائيات وتقنيات تشغيل البوت', permission: 'Everyone', syntax: '/botinfo', options: [] }
  ];

  const filteredCommands = commands.filter((cmd) => {
    const matchesCat = selectedCat === 'all' || cmd.category === selectedCat;
    const matchesSearch = cmd.name.toLowerCase().includes(searchTerm.toLowerCase()) || cmd.description.includes(searchTerm);
    return matchesCat && matchesSearch;
  });

  return (
    <div className="space-y-6">
      
      {/* Header & Controls */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <Terminal className="w-6 h-6 text-indigo-400" />
              مصفوفة أوامر البوت المتاحة (Slash Commands Matrix)
            </h2>
            <p className="text-sm text-slate-400 mt-1">
              جميع الأوامر تعمل بنظام Discord Slash Commands الرسمية مع التحقق الآلي من الصلاحيات وتسلسل الرتب (Role Hierarchy).
            </p>
          </div>

          {/* Search Input */}
          <div className="relative min-w-64">
            <Search className="w-4 h-4 text-slate-500 absolute top-3 right-3" />
            <input
              type="text"
              placeholder="البحث في الأوامر..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 text-white rounded-xl pr-9 pl-4 py-2 text-sm focus:outline-none focus:border-indigo-500"
            />
          </div>
        </div>

        {/* Category Filter Badges */}
        <div className="flex flex-wrap gap-2 pt-2 border-t border-slate-800">
          {[
            { id: 'all', label: 'جميع الأوامر' },
            { id: 'security', label: '🛡️ الحماية والأمان' },
            { id: 'automod', label: '⚡ الإشراف التلقائي' },
            { id: 'warnings', label: '⚠️ نظام التحذيرات والعقوبات' },
            { id: 'voice', label: '🔊 إدارة القنوات الصوتية' },
            { id: 'moderation', label: '🔨 إدارة الأعضاء العادية' },
            { id: 'verification', label: '🔐 التوثيق والتحقق' },
            { id: 'logs', label: '📋 السجلات واللوجز' },
            { id: 'whitelist', label: '⚪ القائمة البيضاء' },
            { id: 'utility', label: 'ℹ️ العامة والإدوات' }
          ].map((c) => (
            <button
              key={c.id}
              onClick={() => setSelectedCat(c.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                selectedCat === c.id
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                  : 'bg-slate-950 text-slate-400 border border-slate-800 hover:text-white hover:bg-slate-800'
              }`}
            >
              {c.label}
            </button>
          ))}
        </div>
      </div>

      {/* Grid of Commands */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filteredCommands.map((cmd, idx) => (
          <div key={idx} className="bg-slate-900 border border-slate-800 hover:border-slate-700 transition-all rounded-2xl p-5 space-y-3 flex flex-col justify-between">
            <div className="space-y-2">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <span className="font-bold text-base text-indigo-300 font-mono">
                  {cmd.name}
                </span>
                <span className="text-[11px] bg-slate-950 text-slate-300 px-2.5 py-0.5 rounded-full font-medium border border-slate-800 flex items-center gap-1">
                  <KeyRound className="w-3 h-3 text-amber-400" />
                  {cmd.permission}
                </span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">{cmd.description}</p>
            </div>

            <div className="bg-slate-950 border border-slate-800/80 rounded-xl p-2.5 font-mono text-xs text-indigo-400 break-all">
              {cmd.syntax}
            </div>
          </div>
        ))}
      </div>

    </div>
  );
};
