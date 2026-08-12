import React, { useState } from 'react';
import { Sliders, Shield, Zap, Lock, ListFilter, Check, Copy, Terminal } from 'lucide-react';

export const Configurator: React.FC = () => {
  const [activeSection, setActiveSection] = useState<'security' | 'automod' | 'verification' | 'logs' | 'punishments'>('security');
  const [copiedCmd, setCopiedCmd] = useState(false);

  // Security Form
  const [antiRaidEnabled, setAntiRaidEnabled] = useState(true);
  const [raidThreshold, setRaidThreshold] = useState(5);
  const [raidWindow, setRaidWindow] = useState(10);
  const [raidAction, setRaidAction] = useState('lockdown');

  const [antiNukeEnabled, setAntiNukeEnabled] = useState(true);
  const [nukeChannelThreshold, setNukeChannelThreshold] = useState(3);
  const [nukeRoleThreshold, setNukeRoleThreshold] = useState(3);
  const [nukeAction, setNukeAction] = useState('remove_roles');

  // AutoMod Form
  const [autoModEnabled, setAutoModEnabled] = useState(true);
  const [antiSpamEnabled, setAntiSpamEnabled] = useState(true);
  const [blockInvites, setBlockInvites] = useState(true);
  const [blockLinks, setBlockLinks] = useState(false);
  const [maxMentions, setMaxMentions] = useState(5);
  const [badWords, setBadWords] = useState('badword1, badword2, scamlink');

  // Generated Commands
  const generateCommand = () => {
    if (activeSection === 'security') {
      return `/security setup anti_raid:${antiRaidEnabled} raid_threshold:${raidThreshold} raid_window:${raidWindow} raid_action:${raidAction} anti_nuke:${antiNukeEnabled} nuke_channel_threshold:${nukeChannelThreshold} nuke_role_threshold:${nukeRoleThreshold} nuke_action:${nukeAction}`;
    }
    if (activeSection === 'automod') {
      return `/automod setup enabled:${autoModEnabled} anti_spam:${antiSpamEnabled} block_invites:${blockInvites} block_links:${blockLinks} max_mentions:${maxMentions}`;
    }
    if (activeSection === 'verification') {
      return `/verification setup channel:#verify-here verified_role:@Verified title:"نظام التحقق" description:"اضغط للتوثيق"`;
    }
    if (activeSection === 'logs') {
      return `/logs setup log_type:Security Logs channel:#security-logs`;
    }
    if (activeSection === 'punishments') {
      return `/punishments setup warn_3:timeout_1h warn_5:kick warn_7:ban`;
    }
    return '';
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(generateCommand());
    setCopiedCmd(true);
    setTimeout(() => setCopiedCmd(false), 2000);
  };

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
        <h2 className="text-xl font-bold text-white flex items-center gap-2 mb-2">
          <Sliders className="w-6 h-6 text-indigo-400" />
          موجه ومولد إعدادات البوت (Bot Setup Builder)
        </h2>
        <p className="text-sm text-slate-400">
          اختر القسم الذي تريد ضبط إعداداته للحصول على أمر Slash Command التفاعلي الجاهز للتطبيق المباشر في ديسكورد.
        </p>

        <div className="flex flex-wrap gap-2 mt-4 pt-4 border-t border-slate-800">
          {[
            { id: 'security', label: '🛡️ /security setup', icon: Shield },
            { id: 'automod', label: '⚡ /automod setup', icon: Zap },
            { id: 'verification', label: '🔐 /verification setup', icon: Lock },
            { id: 'logs', label: '📋 /logs setup', icon: ListFilter },
            { id: 'punishments', label: '🔨 /punishments setup', icon: Sliders }
          ].map((sec) => (
            <button
              key={sec.id}
              onClick={() => setActiveSection(sec.id as any)}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
                activeSection === sec.id
                  ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                  : 'bg-slate-950 text-slate-400 hover:text-white hover:bg-slate-800 border border-slate-800'
              }`}
            >
              {sec.label}
            </button>
          ))}
        </div>
      </div>

      {/* Form Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Form Controls */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6">
          {activeSection === 'security' && (
            <div className="space-y-6">
              <h3 className="text-base font-bold text-white border-b border-slate-800 pb-3 flex items-center gap-2">
                <Shield className="w-5 h-5 text-indigo-400" />
                إعدادات حماية Anti-Raid و Anti-Nuke
              </h3>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-sm text-white">تفعيل Anti-Raid:</span>
                    <input
                      type="checkbox"
                      checked={antiRaidEnabled}
                      onChange={(e) => setAntiRaidEnabled(e.target.checked)}
                      className="w-5 h-5 accent-indigo-500 rounded"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-slate-400 block mb-1">حد دخول الأعضاء (Raid Threshold):</label>
                    <input
                      type="number"
                      value={raidThreshold}
                      onChange={(e) => setRaidThreshold(parseInt(e.target.value) || 5)}
                      className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-sm text-white"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-slate-400 block mb-1">النافذة الزمنية (Raid Window in Sec):</label>
                    <input
                      type="number"
                      value={raidWindow}
                      onChange={(e) => setRaidWindow(parseInt(e.target.value) || 10)}
                      className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-sm text-white"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-slate-400 block mb-1">الإجراء عند الاكتشاف:</label>
                    <select
                      value={raidAction}
                      onChange={(e) => setRaidAction(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-sm text-white"
                    >
                      <option value="lockdown">Lockdown</option>
                      <option value="kick">Kick</option>
                      <option value="ban">Ban</option>
                      <option value="timeout">Timeout</option>
                    </select>
                  </div>
                </div>

                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-sm text-white">تفعيل Anti-Nuke:</span>
                    <input
                      type="checkbox"
                      checked={antiNukeEnabled}
                      onChange={(e) => setAntiNukeEnabled(e.target.checked)}
                      className="w-5 h-5 accent-indigo-500 rounded"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-slate-400 block mb-1">حد حذف القنوات (Channel Threshold):</label>
                    <input
                      type="number"
                      value={nukeChannelThreshold}
                      onChange={(e) => setNukeChannelThreshold(parseInt(e.target.value) || 3)}
                      className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-sm text-white"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-slate-400 block mb-1">حد حذف الرتب (Role Threshold):</label>
                    <input
                      type="number"
                      value={nukeRoleThreshold}
                      onChange={(e) => setNukeRoleThreshold(parseInt(e.target.value) || 3)}
                      className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-sm text-white"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-slate-400 block mb-1">الإجراء الوقائي الضاد:</label>
                    <select
                      value={nukeAction}
                      onChange={(e) => setNukeAction(e.target.value)}
                      className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-sm text-white"
                    >
                      <option value="remove_roles">Remove Roles</option>
                      <option value="ban">Ban Offender</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeSection === 'automod' && (
            <div className="space-y-4">
              <h3 className="text-base font-bold text-white border-b border-slate-800 pb-3 flex items-center gap-2">
                <Zap className="w-5 h-5 text-amber-400" />
                إعدادات نظام AutoMod وفلترة المحتوى
              </h3>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-slate-200">تفعيل AutoMod:</span>
                    <input type="checkbox" checked={autoModEnabled} onChange={(e) => setAutoModEnabled(e.target.checked)} className="accent-amber-500 w-5 h-5" />
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-200">Anti-Spam (رسائل متكررة):</span>
                    <input type="checkbox" checked={antiSpamEnabled} onChange={(e) => setAntiSpamEnabled(e.target.checked)} className="accent-amber-500 w-5 h-5" />
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-200">منع روابط Discord Invites:</span>
                    <input type="checkbox" checked={blockInvites} onChange={(e) => setBlockInvites(e.target.checked)} className="accent-amber-500 w-5 h-5" />
                  </div>
                </div>

                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-slate-200">منع الروابط الخارجية (Links):</span>
                    <input type="checkbox" checked={blockLinks} onChange={(e) => setBlockLinks(e.target.checked)} className="accent-amber-500 w-5 h-5" />
                  </div>
                  <div>
                    <label className="text-xs text-slate-400 block mb-1">الحد الأقصى للمنشن (Max Mentions):</label>
                    <input type="number" value={maxMentions} onChange={(e) => setMaxMentions(parseInt(e.target.value) || 5)} className="w-full bg-slate-900 border border-slate-800 rounded p-1.5 text-white" />
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeSection === 'verification' && (
            <div className="space-y-4">
              <h3 className="text-base font-bold text-white border-b border-slate-800 pb-3 flex items-center gap-2">
                <Lock className="w-5 h-5 text-emerald-400" />
                خيارات لوحة التحقق والتوثيق
              </h3>
              <p className="text-sm text-slate-300">
                استخدم الأمر الجاهز لإنشاء بنل التوثيق مباشرة في قناتك المحددة وتوزيع رتبة Verified تلقائيًا.
              </p>
            </div>
          )}

          {activeSection === 'logs' && (
            <div className="space-y-4">
              <h3 className="text-base font-bold text-white border-b border-slate-800 pb-3">
                تخصيص قنوات اللوجز والتنبيهات
              </h3>
              <p className="text-sm text-slate-300">
                يدعم البوت 7 قنوات مستقلة للسجلات (Member, Message, Moderation, Role, Channel, Server, Security).
              </p>
            </div>
          )}

          {activeSection === 'punishments' && (
            <div className="space-y-4">
              <h3 className="text-base font-bold text-white border-b border-slate-800 pb-3">
                سلم العقوبات التلقائية للتحذيرات
              </h3>
              <p className="text-sm text-slate-300">
                حدد العقوبات التلقائية فور وصول التحذيرات إلى 3 أو 5 أو 7.
              </p>
            </div>
          )}
        </div>

        {/* Command Output Box */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4 flex flex-col justify-between">
          <div className="space-y-3">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Terminal className="w-5 h-5 text-indigo-400" />
              أمر Slash Command الناتج:
            </h3>
            <p className="text-xs text-slate-400">
              انسخ هذا الأمر المباشر وقم بتنفيذه داخل سيرفرك في ديسكورد للشيء المطلوب:
            </p>

            <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 font-mono text-xs text-indigo-300 break-all leading-relaxed relative group">
              {generateCommand()}
            </div>
          </div>

          <button
            onClick={copyToClipboard}
            className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-3 rounded-xl shadow-lg shadow-indigo-600/30 transition-all flex items-center justify-center gap-2"
          >
            {copiedCmd ? <Check className="w-5 h-5 text-emerald-300" /> : <Copy className="w-5 h-5" />}
            {copiedCmd ? 'تم نسخ الأمر بنجاح!' : 'نسخ الأمر المباشر'}
          </button>
        </div>

      </div>

    </div>
  );
};
