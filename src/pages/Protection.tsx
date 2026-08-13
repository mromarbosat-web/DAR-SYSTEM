import React, { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import axios from "axios";
import { ShieldAlert, Save, CheckCircle2, ShieldCheck, Zap } from "lucide-react";

const Protection: React.FC = () => {
  const { selectedGuildId } = useAuth();
  const [security, setSecurity] = useState<any>({});
  const [automod, setAutomod] = useState<any>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await axios.get(`/api/guilds/${selectedGuildId}/protection`);
        setSecurity(res.data.security);
        setAutomod(res.data.automod);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [selectedGuildId]);

  const handleSaveSecurity = async () => {
    setSaving(true);
    try {
      await axios.patch(`/api/guilds/${selectedGuildId}/protection/security`, security);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (e) {
      console.error(e);
    } finally {
      setSaving(false);
    }
  };

  const handleSaveAutomod = async () => {
    setSaving(true);
    try {
      await axios.patch(`/api/guilds/${selectedGuildId}/protection/automod`, automod);
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
      <div className="bg-gradient-to-r from-red-600/20 to-orange-600/20 border border-red-500/30 p-8 rounded-3xl">
        <h2 className="text-3xl font-bold text-white mb-2">إعدادات الحماية</h2>
        <p className="text-zinc-400">تحكم في أنظمة الحماية التلقائية ودرع السيرفر ضد الهجمات.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Security / Anti-Raid */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-3xl p-8 flex flex-col h-full">
          <div className="flex items-center gap-3 mb-8">
            <div className="bg-red-500/20 p-3 rounded-2xl">
              <ShieldAlert className="w-6 h-6 text-red-400" />
            </div>
            <h3 className="text-xl font-bold text-white">نظام Security & Anti-Raid</h3>
          </div>

          <div className="space-y-6 flex-grow">
            <div className="flex items-center justify-between p-4 rounded-2xl bg-zinc-800/50">
              <div>
                <p className="text-white font-medium">نظام Anti-Raid</p>
                <p className="text-xs text-zinc-500">حماية من دخول الأعضاء الجماعي (Raid)</p>
              </div>
              <input 
                type="checkbox" 
                checked={security.anti_raid_enabled} 
                onChange={(e) => setSecurity({...security, anti_raid_enabled: e.target.checked})}
                className="w-12 h-6 rounded-full bg-zinc-700 checked:bg-red-500 appearance-none transition-colors cursor-pointer relative after:content-[''] after:absolute after:top-1 after:left-1 after:w-4 after:h-4 after:bg-white after:rounded-full after:transition-all checked:after:left-7"
              />
            </div>

            <div className="flex items-center justify-between p-4 rounded-2xl bg-zinc-800/50">
              <div>
                <p className="text-white font-medium">نظام Anti-Nuke</p>
                <p className="text-xs text-zinc-500">حماية من تخريب المشرفين (مسح قنوات/رتب)</p>
              </div>
              <input 
                type="checkbox" 
                checked={security.anti_nuke_enabled} 
                onChange={(e) => setSecurity({...security, anti_nuke_enabled: e.target.checked})}
                className="w-12 h-6 rounded-full bg-zinc-700 checked:bg-red-500 appearance-none transition-colors cursor-pointer relative after:content-[''] after:absolute after:top-1 after:left-1 after:w-4 after:h-4 after:bg-white after:rounded-full after:transition-all checked:after:left-7"
              />
            </div>
          </div>

          <button
            onClick={handleSaveSecurity}
            className="mt-8 w-full bg-zinc-800 hover:bg-zinc-700 text-white py-4 rounded-2xl font-bold transition-all flex items-center justify-center gap-2"
          >
            {saving ? "جاري الحفظ..." : saved ? <><CheckCircle2 className="w-5 h-5 text-green-400" /> تم الحفظ</> : "حفظ إعدادات Security"}
          </button>
        </div>

        {/* AutoMod */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-3xl p-8 flex flex-col h-full">
          <div className="flex items-center gap-3 mb-8">
            <div className="bg-indigo-500/20 p-3 rounded-2xl">
              <Zap className="w-6 h-6 text-indigo-400" />
            </div>
            <h3 className="text-xl font-bold text-white">نظام AutoMod</h3>
          </div>

          <div className="space-y-6 flex-grow">
            <div className="flex items-center justify-between p-4 rounded-2xl bg-zinc-800/50">
              <div>
                <p className="text-white font-medium">تفعيل AutoMod</p>
                <p className="text-xs text-zinc-500">تشغيل نظام الفلترة التلقائية</p>
              </div>
              <input 
                type="checkbox" 
                checked={automod.enabled} 
                onChange={(e) => setAutomod({...automod, enabled: e.target.checked})}
                className="w-12 h-6 rounded-full bg-zinc-700 checked:bg-indigo-500 appearance-none transition-colors cursor-pointer relative after:content-[''] after:absolute after:top-1 after:left-1 after:w-4 after:h-4 after:bg-white after:rounded-full after:transition-all checked:after:left-7"
              />
            </div>

            <div className="flex items-center justify-between p-4 rounded-2xl bg-zinc-800/50">
              <div>
                <p className="text-white font-medium">منع السبام (Anti-Spam)</p>
                <p className="text-xs text-zinc-500">فلترة الرسائل المتكررة بسرعة</p>
              </div>
              <input 
                type="checkbox" 
                checked={automod.anti_spam_enabled} 
                onChange={(e) => setAutomod({...automod, anti_spam_enabled: e.target.checked})}
                className="w-12 h-6 rounded-full bg-zinc-700 checked:bg-indigo-500 appearance-none transition-colors cursor-pointer relative after:content-[''] after:absolute after:top-1 after:left-1 after:w-4 after:h-4 after:bg-white after:rounded-full after:transition-all checked:after:left-7"
              />
            </div>

            <div className="flex items-center justify-between p-4 rounded-2xl bg-zinc-800/50">
              <div>
                <p className="text-white font-medium">منع الروابط (Anti-Links)</p>
                <p className="text-xs text-zinc-500">حظر إرسال أي روابط خارجية</p>
              </div>
              <input 
                type="checkbox" 
                checked={automod.block_links} 
                onChange={(e) => setAutomod({...automod, block_links: e.target.checked})}
                className="w-12 h-6 rounded-full bg-zinc-700 checked:bg-indigo-500 appearance-none transition-colors cursor-pointer relative after:content-[''] after:absolute after:top-1 after:left-1 after:w-4 after:h-4 after:bg-white after:rounded-full after:transition-all checked:after:left-7"
              />
            </div>

            <div className="flex items-center justify-between p-4 rounded-2xl bg-zinc-800/50">
              <div>
                <p className="text-white font-medium">منع روابط الديسكورد (Anti-Invites)</p>
                <p className="text-xs text-zinc-500">حظر روابط دعوات السيرفرات الأخرى</p>
              </div>
              <input 
                type="checkbox" 
                checked={automod.block_invites} 
                onChange={(e) => setAutomod({...automod, block_invites: e.target.checked})}
                className="w-12 h-6 rounded-full bg-zinc-700 checked:bg-indigo-500 appearance-none transition-colors cursor-pointer relative after:content-[''] after:absolute after:top-1 after:left-1 after:w-4 after:h-4 after:bg-white after:rounded-full after:transition-all checked:after:left-7"
              />
            </div>
          </div>

          <button
            onClick={handleSaveAutomod}
            className="mt-8 w-full bg-zinc-800 hover:bg-zinc-700 text-white py-4 rounded-2xl font-bold transition-all flex items-center justify-center gap-2"
          >
            {saving ? "جاري الحفظ..." : saved ? <><CheckCircle2 className="w-5 h-5 text-green-400" /> تم الحفظ</> : "حفظ إعدادات AutoMod"}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Protection;
