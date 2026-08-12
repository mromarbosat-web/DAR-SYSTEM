import React, { useState } from 'react';
import { Shield, Zap, AlertOctagon, CheckCircle, Flame, Lock, UserCheck, AlertTriangle } from 'lucide-react';

export const Simulator: React.FC = () => {
  const [activeSim, setActiveSim] = useState<'anti_raid' | 'automod' | 'verification' | 'warn_ladder'>('anti_raid');

  // Anti-Raid State
  const [raidJoins, setRaidJoins] = useState(8);
  const [raidWindow, setRaidWindow] = useState(10);
  const [raidAction, setRaidAction] = useState('lockdown');
  const [raidResult, setRaidResult] = useState<any>(null);

  // AutoMod State
  const [automodInput, setAutomodInput] = useState('انضموا إلى سيرفرنا المميز discord.gg/example_invite !');
  const [automodResult, setAutomodResult] = useState<any>(null);

  // Verification State
  const [isVerified, setIsVerified] = useState(false);
  const [verifLog, setVerifLog] = useState<string[]>([]);

  // Warn Ladder State
  const [warnCount, setWarnCount] = useState(0);
  const [warnLogs, setWarnLogs] = useState<any[]>([]);

  const runRaidSim = async () => {
    try {
      const res = await fetch('/api/bot/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: 'anti_raid',
          payload: { joinCount: raidJoins, window: raidWindow, action: raidAction }
        })
      });
      const data = await res.json();
      setRaidResult(data);
    } catch (e) {
      console.error(e);
    }
  };

  const runAutoModSim = async () => {
    try {
      const res = await fetch('/api/bot/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: 'automod',
          payload: { content: automodInput }
        })
      });
      const data = await res.json();
      setAutomodResult(data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleVerify = () => {
    setIsVerified(true);
    setVerifLog((prev) => [
      `[${new Date().toLocaleTimeString()}] ✅ User @Visitor_982 verified successfully. Added role @Verified, Removed role @Unverified.`,
      ...prev
    ]);
  };

  const handleAddWarn = async () => {
    try {
      const res = await fetch('/api/bot/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: 'warn_ladder',
          payload: { currentWarns: warnCount }
        })
      });
      const data = await res.json();
      setWarnCount(data.totalWarns);
      setWarnLogs((prev) => [data, ...prev]);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Overview Intro Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 border border-indigo-500/30 rounded-2xl p-6 shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500"></div>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center space-x-2 space-x-reverse">
              <span className="p-2 bg-indigo-500/20 text-indigo-400 rounded-xl border border-indigo-500/30">
                <Zap className="w-5 h-5" />
              </span>
              <h2 className="text-xl font-bold text-white">مختبر المحاكاة التفاعلي (Interactive Security Test Lab)</h2>
            </div>
            <p className="text-sm text-slate-300 max-w-2xl leading-relaxed">
              اختبر استجابة خوارزميات الحماية والإشراف التلقائي كأن البوت يعمل مباشرة في سيرفرك. يمكنك تجربة هجمات الدخول المفاجئ (Anti-Raid)، فحص فلاتر الكلمات والمحاذير (AutoMod)، زر التوثيق (Verification Panel)، وسلم العقوبات التلقائية (Warn Ladder).
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            {[
              { id: 'anti_raid', label: '🛡️ Anti-Raid' },
              { id: 'automod', label: '⚡ AutoMod Scanner' },
              { id: 'verification', label: '🔐 Verification Panel' },
              { id: 'warn_ladder', label: '🔨 Warn Ladder' }
            ].map((s) => (
              <button
                key={s.id}
                onClick={() => setActiveSim(s.id as any)}
                className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
                  activeSim === s.id
                    ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/40 border border-indigo-400/40'
                    : 'bg-slate-800 text-slate-300 border border-slate-700 hover:bg-slate-700'
                }`}
              >
                {s.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Simulator 1: Anti-Raid */}
      {activeSim === 'anti_raid' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* Controls Panel */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <AlertOctagon className="w-5 h-5 text-pink-500" />
                محاكاة هجوم الدخول الجماعي (Anti-Raid Flood)
              </h3>
              <span className="text-xs px-2.5 py-1 bg-pink-500/10 text-pink-400 border border-pink-500/20 rounded-full font-medium">
                Live Logic Test
              </span>
            </div>

            <div className="space-y-4 text-sm">
              <div>
                <label className="block text-slate-300 mb-1 font-medium">عدد الأعضاء المنضمين دفعة واحدة:</label>
                <div className="flex items-center gap-4">
                  <input
                    type="range"
                    min="1"
                    max="20"
                    value={raidJoins}
                    onChange={(e) => setRaidJoins(parseInt(e.target.value))}
                    className="w-full accent-indigo-500"
                  />
                  <span className="px-3 py-1 bg-slate-800 border border-slate-700 rounded-lg font-bold text-indigo-400 min-w-16 text-center">
                    {raidJoins} عضو
                  </span>
                </div>
              </div>

              <div>
                <label className="block text-slate-300 mb-1 font-medium">النافذة الزمنية لاكتشاف الهجوم:</label>
                <select
                  value={raidWindow}
                  onChange={(e) => setRaidWindow(parseInt(e.target.value))}
                  className="w-full bg-slate-950 border border-slate-800 text-white rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-indigo-500"
                >
                  <option value={5}>5 ثوانٍ (حماية قصوى)</option>
                  <option value={10}>10 ثوانٍ (قياسي)</option>
                  <option value={30}>30 ثانية</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-300 mb-1 font-medium">الإجراء الوقائي المعتمد:</label>
                <select
                  value={raidAction}
                  onChange={(e) => setRaidAction(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 text-white rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-indigo-500"
                >
                  <option value="lockdown">Lockdown (إغلاق قنوات السيرفر)</option>
                  <option value="kick">Kick New Members (طرد الأعضاء الجدد)</option>
                  <option value="ban">Ban New Members (حظر الأعضاء الجدد)</option>
                  <option value="timeout">Timeout New Members (عزل مؤقت ساعتين)</option>
                </select>
              </div>

              <button
                onClick={runRaidSim}
                className="w-full bg-gradient-to-r from-pink-600 to-purple-600 hover:from-pink-500 hover:to-purple-500 text-white font-bold py-3 rounded-xl shadow-lg shadow-pink-600/30 transition-all flex items-center justify-center gap-2"
              >
                <Flame className="w-5 h-5" />
                تنفيذ محاكاة انضمام {raidJoins} عضوًا الآن
              </button>
            </div>
          </div>

          {/* Results Display */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
            <h3 className="text-base font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-4">
              <Lock className="w-5 h-5 text-indigo-400" />
              مخرجات معالج الأمان وتنبيه اللوجز (Security Logs Output)
            </h3>

            {raidResult ? (
              <div className="space-y-4">
                <div className={`p-4 rounded-xl border ${
                  raidResult.triggered 
                    ? 'bg-pink-500/10 border-pink-500/30 text-pink-300' 
                    : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                }`}>
                  <div className="flex items-center gap-2 font-bold text-base mb-1">
                    {raidResult.triggered ? <AlertTriangle className="w-5 h-5 text-pink-400" /> : <CheckCircle className="w-5 h-5 text-emerald-400" />}
                    {raidResult.triggered ? 'تم اكتشاف هجوم دخول جماعي (Anti-Raid Activated)!' : 'دخول طبيعي تحت حدود الأمان'}
                  </div>
                  <p className="text-xs text-slate-300">
                    {raidResult.triggered 
                      ? `تم انضمام ${raidResult.joinCount} أعضاء خلال ${raidResult.windowSeconds} ثوانٍ. تجاوز حد الأمان المسموح (5 اعضاء).`
                      : `الانضمامات الحالية (${raidResult.joinCount}) أقل من الحد الأدنى للـ Raid.`
                    }
                  </p>
                </div>

                {raidResult.logEmbed && (
                  <div className="bg-slate-950 border-r-4 border-r-pink-500 border border-slate-800 rounded-xl p-4 space-y-3 font-mono text-xs text-slate-200">
                    <div className="font-bold text-sm text-pink-400 flex items-center gap-2">
                      <Shield className="w-4 h-4" />
                      {raidResult.logEmbed.title}
                    </div>
                    <div className="grid grid-cols-2 gap-2 bg-slate-900/80 p-2.5 rounded-lg border border-slate-800">
                      {raidResult.logEmbed.fields.map((f: any, idx: number) => (
                        <div key={idx} className={f.inline ? 'col-span-1' : 'col-span-2'}>
                          <span className="text-slate-400 block text-[11px]">{f.name}:</span>
                          <span className="font-semibold text-white">{f.value}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="h-48 flex flex-col items-center justify-center text-slate-500 text-sm border-2 border-dashed border-slate-800 rounded-xl p-6 text-center">
                <AlertOctagon className="w-8 h-8 mb-2 opacity-40 text-slate-400" />
                اضغط على زر التنفيذ لمحاكاة خوارزمية Anti-Raid ومتابعة سجلات الأمان.
              </div>
            )}
          </div>

        </div>
      )}

      {/* Simulator 2: AutoMod */}
      {activeSim === 'automod' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
            <h3 className="text-base font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-4">
              <Zap className="w-5 h-5 text-amber-400" />
              مختبر تفحص الرسائل (AutoMod Scanner Test)
            </h3>

            <div className="space-y-3">
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">
                قم بإدخال رسالة لاختبار الفلترة:
              </label>
              <textarea
                value={automodInput}
                onChange={(e) => setAutomodInput(e.target.value)}
                rows={4}
                className="w-full bg-slate-950 border border-slate-800 text-white rounded-xl p-3 text-sm focus:outline-none focus:border-indigo-500 font-mono"
                placeholder="اكتب هنا تجربة تحتوي على رابط discord.gg/ أو كلمات محظورة..."
              />

              <div className="flex flex-wrap gap-2 text-xs">
                <span className="text-slate-400">عينات جاهزة للاختبار:</span>
                <button
                  onClick={() => setAutomodInput('انضموا بسرعة لرابط السيرفر discord.gg/vip123')}
                  className="text-indigo-400 hover:underline"
                >
                  [رابط دعوة]
                </button>
                <button
                  onClick={() => setAutomodInput('هذه الرسالة تحتوي على badword صريحة')}
                  className="text-indigo-400 hover:underline"
                >
                  [كلمة محظورة]
                </button>
                <button
                  onClick={() => setAutomodInput('منشن جماعي @user1 @user2 @user3 @user4 @user5')}
                  className="text-indigo-400 hover:underline"
                >
                  [منشن مكثف]
                </button>
              </div>

              <button
                onClick={runAutoModSim}
                className="w-full bg-amber-600 hover:bg-amber-500 text-white font-bold py-3 rounded-xl shadow-lg shadow-amber-600/30 transition-all flex items-center justify-center gap-2"
              >
                <Zap className="w-5 h-5" />
                فحص الرسالة عبر AutoMod Engine
              </button>
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
            <h3 className="text-base font-bold text-white border-b border-slate-800 pb-4">
              نتيجة الفحص (Scanner Decision)
            </h3>

            {automodResult ? (
              <div className="space-y-4">
                <div className={`p-4 rounded-xl border ${
                  automodResult.flagged 
                    ? 'bg-red-500/10 border-red-500/30 text-red-300' 
                    : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                }`}>
                  <div className="flex items-center gap-2 font-bold text-base mb-1">
                    {automodResult.flagged ? <AlertOctagon className="w-5 h-5 text-red-400" /> : <CheckCircle className="w-5 h-5 text-emerald-400" />}
                    {automodResult.flagged ? 'تم رصد مخالفة وحذف الرسالة!' : 'الرسالة سليمة وتفي بكل معايير الأمان'}
                  </div>
                  <p className="text-xs mt-1">السبب: <strong className="underline">{automodResult.reason}</strong></p>
                  <p className="text-xs mt-1 font-mono">الإجراء المطبق: {automodResult.action}</p>
                </div>
              </div>
            ) : (
              <div className="h-40 flex items-center justify-center text-slate-500 text-sm border-2 border-dashed border-slate-800 rounded-xl">
                أدخل رسالة واضغط على زر الفحص للتحقق من الفلاتر.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Simulator 3: Verification Panel */}
      {activeSim === 'verification' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
            <h3 className="text-base font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-4">
              <UserCheck className="w-5 h-5 text-emerald-400" />
              معاينة بنل التحقق (Verification Panel Preview)
            </h3>

            {/* Simulated Discord Message */}
            <div className="bg-slate-950 border border-slate-800 rounded-2xl p-5 space-y-4 font-sans">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-indigo-600 flex items-center justify-center text-white font-bold">
                  BOT
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-white">Security & Management Bot</span>
                    <span className="bg-indigo-600 text-[10px] text-white px-1.5 py-0.2 rounded font-semibold">BOT</span>
                  </div>
                  <span className="text-[11px] text-slate-400">Today at 12:00 PM</span>
                </div>
              </div>

              {/* Embed Box */}
              <div className="bg-slate-900 border-r-4 border-r-emerald-500 border border-slate-800 rounded-xl p-4 space-y-2 text-sm text-slate-200">
                <h4 className="font-bold text-white text-base">🔐 نظام التحقق - Verification System</h4>
                <p className="text-slate-300 text-xs leading-relaxed">
                  أهلاً بك في السيرفر! اضغط على الزر الزاهي أدناه لإكمال عملية التوثيق والحصول على رتبة الموثقين <span className="bg-indigo-500/20 text-indigo-300 px-1.5 py-0.5 rounded text-xs font-mono">@Verified</span>.
                </p>
              </div>

              {/* Action Button */}
              <div>
                <button
                  onClick={handleVerify}
                  disabled={isVerified}
                  className={`px-5 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
                    isVerified
                      ? 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700'
                      : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-600/30'
                  }`}
                >
                  <UserCheck className="w-4 h-4" />
                  {isVerified ? 'تم التحقق بنجاح (Verified)' : 'تحقق الآن / Verify'}
                </button>
              </div>
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
            <h3 className="text-base font-bold text-white border-b border-slate-800 pb-4">
              سجل التحقق المباشر (Verification Log Feed)
            </h3>

            <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 h-60 overflow-y-auto font-mono text-xs space-y-2 text-slate-300">
              {verifLog.length > 0 ? (
                verifLog.map((log, i) => (
                  <div key={i} className="text-emerald-400 bg-slate-900 p-2 rounded border border-slate-800">
                    {log}
                  </div>
                ))
              ) : (
                <div className="text-slate-600 h-full flex items-center justify-center">
                  اضغط على زر "تحقق الآن" لمعاينة استجابة البوت وإرسال السجل.
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Simulator 4: Warn Ladder */}
      {activeSim === 'warn_ladder' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
            <h3 className="text-base font-bold text-white flex items-center gap-2 border-b border-slate-800 pb-4">
              <Flame className="w-5 h-5 text-red-400" />
              سلم العقوبات التلقائية (Punishment Ladder Escalation)
            </h3>

            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-3 text-sm">
              <div className="flex justify-between items-center">
                <span className="text-slate-300">العضو المستهدف بالتحذيرات:</span>
                <span className="font-mono text-indigo-400 font-bold">@Offender_User#1234</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-300">عدد التحذيرات الحالي:</span>
                <span className="px-3 py-1 bg-red-500/20 text-red-400 font-bold rounded-lg border border-red-500/30">
                  {warnCount} تحذير
                </span>
              </div>

              <div className="space-y-1.5 pt-2 text-xs">
                <div className={`p-2 rounded border flex justify-between ${warnCount >= 3 ? 'bg-amber-500/20 border-amber-500/40 text-amber-300 font-bold' : 'bg-slate-900 border-slate-800 text-slate-400'}`}>
                  <span>3 Warns:</span>
                  <span>Timeout 1 Hour</span>
                </div>
                <div className={`p-2 rounded border flex justify-between ${warnCount >= 5 ? 'bg-orange-500/20 border-orange-500/40 text-orange-300 font-bold' : 'bg-slate-900 border-slate-800 text-slate-400'}`}>
                  <span>5 Warns:</span>
                  <span>Kick Member</span>
                </div>
                <div className={`p-2 rounded border flex justify-between ${warnCount >= 7 ? 'bg-red-500/20 border-red-500/40 text-red-300 font-bold' : 'bg-slate-900 border-slate-800 text-slate-400'}`}>
                  <span>7 Warns:</span>
                  <span>Ban Member</span>
                </div>
              </div>

              <button
                onClick={handleAddWarn}
                className="w-full bg-red-600 hover:bg-red-500 text-white font-bold py-3 rounded-xl shadow-lg shadow-red-600/30 transition-all flex items-center justify-center gap-2 mt-4"
              >
                <AlertOctagon className="w-5 h-5" />
                إضافة تحذير جديد (/warn @Offender_User)
              </button>
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
            <h3 className="text-base font-bold text-white border-b border-slate-800 pb-4">
              سجل استجابة سلم العقوبات (Escalation Log)
            </h3>

            <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 h-64 overflow-y-auto font-mono text-xs space-y-2 text-slate-300">
              {warnLogs.length > 0 ? (
                warnLogs.map((log, i) => (
                  <div key={i} className="p-3 bg-slate-900 border border-slate-800 rounded-lg space-y-1">
                    <div className="flex justify-between text-indigo-400 font-bold">
                      <span>Warn ID: {log.warningId}</span>
                      <span>Total Warns: {log.totalWarns}</span>
                    </div>
                    <div className="text-slate-200">Action Triggered: <strong className="text-red-400">{log.escalation}</strong></div>
                    <p className="text-slate-400 text-[11px]">{log.note}</p>
                  </div>
                ))
              ) : (
                <div className="text-slate-600 h-full flex items-center justify-center">
                  اضغط على زر إضافة تحذير لمراقبة الترقية التلقائية.
                </div>
              )}
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
