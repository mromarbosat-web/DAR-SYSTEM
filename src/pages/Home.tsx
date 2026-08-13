import React, { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import axios from "axios";
import { Users, AlertTriangle, ShieldCheck, Activity } from "lucide-react";
import { motion } from "motion/react";

interface Stats {
  bot_status: string;
  guild_count: number;
  warnings_count: number;
  actions_count: number;
  economy_users: number;
}

const Home: React.FC = () => {
  const { selectedGuildId } = useAuth();
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!selectedGuildId) return;
    
    const fetchStats = async () => {
      try {
        const res = await axios.get(`/api/guilds/${selectedGuildId}/stats`);
        setStats(res.data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, [selectedGuildId]);

  if (loading) return <div className="flex items-center justify-center h-full text-white">جاري التحميل...</div>;

  const statCards = [
    { title: "حالة البوت", value: stats?.bot_status === "online" ? "متصل" : "غير متصل", icon: Activity, color: "text-green-400" },
    { title: "إجمالي السيرفرات", value: stats?.guild_count || 0, icon: ShieldCheck, color: "text-blue-400" },
    { title: "تحذيرات السيرفر", value: stats?.warnings_count || 0, icon: AlertTriangle, color: "text-yellow-400" },
    { title: "مستخدمي الاقتصاد", value: stats?.economy_users || 0, icon: Users, color: "text-indigo-400" },
  ];

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div className="bg-gradient-to-r from-indigo-600/20 to-purple-600/20 border border-indigo-500/30 p-8 rounded-3xl backdrop-blur-sm">
        <h2 className="text-3xl font-bold text-white mb-2">مرحباً بك في لوحة التحكم</h2>
        <p className="text-zinc-400">إحصائيات وتحكم كامل في بوت Security & Management الخاص بك.</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((card, idx) => (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.1 }}
            key={card.title}
            className="bg-zinc-900 border border-zinc-800 p-6 rounded-2xl flex items-center justify-between group hover:border-zinc-700 transition-colors"
          >
            <div>
              <p className="text-zinc-500 text-sm font-medium mb-1">{card.title}</p>
              <p className="text-2xl font-bold text-white">{card.value}</p>
            </div>
            <div className={`p-3 rounded-xl bg-zinc-800 group-hover:scale-110 transition-transform ${card.color}`}>
              <card.icon className="w-6 h-6" />
            </div>
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="bg-zinc-900 border border-zinc-800 p-8 rounded-3xl">
          <h3 className="text-xl font-bold text-white mb-6">نشاط البوت</h3>
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex items-center gap-4 p-4 rounded-xl bg-zinc-800/50 border border-zinc-700/50">
                <div className="w-10 h-10 rounded-full bg-indigo-500/20 flex items-center justify-center text-indigo-400">
                  <Activity className="w-5 h-5" />
                </div>
                <div>
                  <p className="text-sm text-white font-medium">تم تسجيل عملية إشراف جديدة</p>
                  <p className="text-xs text-zinc-500">منذ 5 دقائق</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-zinc-900 border border-zinc-800 p-8 rounded-3xl flex flex-col items-center justify-center text-center">
          <ShieldCheck className="w-16 h-16 text-indigo-500 mb-4" />
          <h3 className="text-xl font-bold text-white mb-2">النظام محمي بالكامل</h3>
          <p className="text-zinc-400 max-w-xs">أنظمة Anti-Raid و AutoMod مفعلة وتعمل بكفاءة عالية على هذا السيرفر.</p>
        </div>
      </div>
    </div>
  );
};

export default Home;
