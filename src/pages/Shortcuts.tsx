import React, { useState } from "react";
import { Zap, Shield, Ban, Trash2, Clock, Lock, Unlock, AlertTriangle, UserMinus, ShieldAlert } from "lucide-react";

const commands = [
  { id: "warn", name: "Warn", icon: AlertTriangle, color: "bg-yellow-500/20 text-yellow-500", desc: "تحذير عضو" },
  { id: "warnings", name: "Warnings", icon: Shield, color: "bg-blue-500/20 text-blue-500", desc: "عرض تحذيرات عضو" },
  { id: "unwarn", name: "Unwarn", icon: ShieldCheck, color: "bg-green-500/20 text-green-500", desc: "إزالة تحذير" },
  { id: "timeout", name: "Timeout", icon: Clock, color: "bg-orange-500/20 text-orange-500", desc: "إسكات عضو مؤقتاً" },
  { id: "untimeout", name: "Untimeout", icon: Zap, color: "bg-indigo-500/20 text-indigo-500", desc: "إلغاء الإسكات" },
  { id: "kick", name: "Kick", icon: UserMinus, color: "bg-pink-500/20 text-pink-500", desc: "طرد عضو" },
  { id: "ban", name: "Ban", icon: Ban, color: "bg-red-500/20 text-red-500", desc: "حظر عضو" },
  { id: "unban", name: "Unban", icon: Shield, color: "bg-emerald-500/20 text-emerald-500", desc: "إلغاء الحظر" },
  { id: "softban", name: "Softban", icon: Trash2, color: "bg-rose-500/20 text-rose-500", desc: "حظر مؤقت لمسح الرسائل" },
  { id: "purge", name: "Purge", icon: Trash2, color: "bg-zinc-500/20 text-zinc-400", desc: "مسح الرسائل" },
  { id: "lock", name: "Lock", icon: Lock, color: "bg-red-600/20 text-red-600", desc: "قفل القناة" },
  { id: "unlock", name: "Unlock", icon: Unlock, color: "bg-green-600/20 text-green-600", desc: "فتح القناة" },
];

import { ShieldCheck } from "lucide-react";

const Shortcuts: React.FC = () => {
  const [selectedCmd, setSelectedCmd] = useState<any>(null);

  return (
    <div className="space-y-8 animate-in fade-in duration-500 pb-20">
      <div className="bg-gradient-to-r from-indigo-600/20 to-blue-600/20 border border-indigo-500/30 p-8 rounded-3xl">
        <h2 className="text-3xl font-bold text-white mb-2">اختصارات الأوامر</h2>
        <p className="text-zinc-400">وصول سريع لأوامر الإدارة وتخصيص صلاحيات استخدامها.</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {commands.map((cmd) => (
          <button
            key={cmd.id}
            onClick={() => setSelectedCmd(cmd)}
            className="bg-zinc-900 border border-zinc-800 p-6 rounded-3xl group hover:border-indigo-500/50 hover:bg-zinc-800/50 transition-all text-right"
          >
            <div className={`w-12 h-12 rounded-2xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform ${cmd.color}`}>
              <cmd.icon className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-white mb-1">/{cmd.id}</h3>
            <p className="text-xs text-zinc-500">{cmd.desc}</p>
          </button>
        ))}
      </div>

      {selectedCmd && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-[100] flex items-center justify-center p-4">
          <div className="bg-zinc-900 border border-zinc-800 w-full max-w-2xl rounded-3xl overflow-hidden shadow-2xl animate-in zoom-in duration-300">
            <div className="p-8 border-b border-zinc-800 flex justify-between items-center">
              <div className="flex items-center gap-4">
                <div className={`p-3 rounded-2xl ${selectedCmd.color}`}>
                  <selectedCmd.icon className="w-6 h-6" />
                </div>
                <h3 className="text-2xl font-bold text-white">إعدادات /{selectedCmd.id}</h3>
              </div>
              <button onClick={() => setSelectedCmd(null)} className="text-zinc-500 hover:text-white transition-colors">إغلاق</button>
            </div>

            <div className="p-8 space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-zinc-400 block">الرتب المسموح بها (Allowed Roles)</label>
                  <textarea 
                    placeholder="@Admin, @Moderator..."
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-xl p-4 text-white focus:outline-none focus:border-indigo-500 h-24"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-zinc-400 block">الرتب الممنوعة (Denied Roles)</label>
                  <textarea 
                    placeholder="@Member..."
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-xl p-4 text-white focus:outline-none focus:border-red-500 h-24"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-zinc-400 block">القنوات المسموح بها (Allowed Channels)</label>
                  <textarea 
                    placeholder="#moderation..."
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-xl p-4 text-white focus:outline-none focus:border-indigo-500 h-24"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-zinc-400 block">القنوات الممنوعة (Denied Channels)</label>
                  <textarea 
                    placeholder="#general, #chat..."
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-xl p-4 text-white focus:outline-none focus:border-red-500 h-24"
                  />
                </div>
              </div>

              <div className="pt-4">
                <button className="w-full bg-indigo-600 hover:bg-indigo-500 text-white py-4 rounded-2xl font-bold shadow-lg shadow-indigo-500/20 transition-all">حفظ الصلاحيات</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Shortcuts;
