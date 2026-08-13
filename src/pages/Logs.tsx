import React, { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import axios from "axios";
import { ClipboardList, Save, CheckCircle2 } from "lucide-react";

const logTypes = [
  { key: "member_log_channel_id", name: "لوج الأعضاء (In/Out)" },
  { key: "message_log_channel_id", name: "لوج الرسائل (Edit/Delete)" },
  { key: "moderation_log_channel_id", name: "لوج الإدارة (Kick/Ban)" },
  { key: "role_log_channel_id", name: "لوج الرتب" },
  { key: "channel_log_channel_id", name: "لوج القنوات" },
  { key: "voice_log_channel_id", name: "لوج الصوت" },
  { key: "security_log_channel_id", name: "لوج الحماية (Security)" },
  { key: "automod_log_channel_id", name: "لوج الأوتومود" },
  { key: "economy_log_channel_id", name: "لوج الاقتصاد" },
];

const Logs: React.FC = () => {
  const { selectedGuildId } = useAuth();
  const [settings, setSettings] = useState<any>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const res = await axios.get(`/api/guilds/${selectedGuildId}/logs`);
        setSettings(res.data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchLogs();
  }, [selectedGuildId]);

  const handleSave = async () => {
    setSaving(true);
    try {
      await axios.patch(`/api/guilds/${selectedGuildId}/logs`, settings);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (e) {
      console.error(e);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="text-center p-12 text-zinc-500">جاري تحميل الإعدادات...</div>;

  return (
    <div className="space-y-8 animate-in fade-in duration-500 pb-20">
      <div className="bg-gradient-to-r from-blue-600/20 to-cyan-600/20 border border-blue-500/30 p-8 rounded-3xl flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold text-white mb-2">إدارة اللوجات</h2>
          <p className="text-zinc-400">حدد القنوات التي سيتم إرسال سجلات النشاط إليها.</p>
        </div>
        <button
          onClick={handleSave}
          disabled={saving}
          className="bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-800 text-white px-8 py-3 rounded-xl font-bold transition-all flex items-center gap-2 shadow-lg shadow-indigo-500/20"
        >
          {saving ? "جاري الحفظ..." : saved ? <><CheckCircle2 className="w-5 h-5" /> تم الحفظ</> : <><Save className="w-5 h-5" /> حفظ التغييرات</>}
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {logTypes.map((type) => (
          <div key={type.key} className="bg-zinc-900 border border-zinc-800 p-6 rounded-2xl">
            <label className="block text-zinc-400 text-sm font-medium mb-3">{type.name}</label>
            <input
              type="text"
              placeholder="أدخل ID القناة (أو اتركه فارغاً للتعطيل)"
              value={settings[type.key] || ""}
              onChange={(e) => setSettings({ ...settings, [type.key]: e.target.value })}
              className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-indigo-500 transition-colors"
            />
            <p className="mt-2 text-[10px] text-zinc-600">مثال: 123456789012345678</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Logs;
