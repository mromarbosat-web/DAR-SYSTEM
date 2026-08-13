import React, { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import axios from "axios";
import { Trophy, Coins } from "lucide-react";

interface TopUser {
  user_id: string;
  balance: number;
  bank_balance: number;
  total: number;
}

const Economy: React.FC = () => {
  const { selectedGuildId } = useAuth();
  const [topUsers, setTopUsers] = useState<TopUser[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTop = async () => {
      try {
        const res = await axios.get(`/api/guilds/${selectedGuildId}/economy/top`);
        setTopUsers(res.data.top);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchTop();
  }, [selectedGuildId]);

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div className="bg-gradient-to-r from-amber-600/20 to-yellow-600/20 border border-amber-500/30 p-8 rounded-3xl">
        <h2 className="text-3xl font-bold text-white mb-2">إحصائيات الاقتصاد</h2>
        <p className="text-zinc-400">قائمة أغنى 10 أعضاء في السيرفر بعملة سراب.</p>
      </div>

      <div className="bg-zinc-900 border border-zinc-800 rounded-3xl overflow-hidden">
        <div className="p-6 border-b border-zinc-800 flex items-center justify-between">
          <h3 className="text-xl font-bold text-white flex items-center gap-2">
            <Trophy className="w-5 h-5 text-amber-500" />
            قائمة الأوائل (Top 10)
          </h3>
          <Coins className="w-5 h-5 text-zinc-500" />
        </div>

        {loading ? (
          <div className="p-12 text-center text-zinc-500">جاري تحميل البيانات...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-right">
              <thead>
                <tr className="text-zinc-500 text-sm border-b border-zinc-800 bg-zinc-950/50">
                  <th className="px-6 py-4 font-medium uppercase tracking-wider">#</th>
                  <th className="px-6 py-4 font-medium uppercase tracking-wider">المستخدم</th>
                  <th className="px-6 py-4 font-medium uppercase tracking-wider">المحفظة</th>
                  <th className="px-6 py-4 font-medium uppercase tracking-wider">البنك</th>
                  <th className="px-6 py-4 font-medium uppercase tracking-wider text-white">الإجمالي</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800">
                {topUsers.map((user, idx) => (
                  <tr key={user.user_id} className="hover:bg-zinc-800/50 transition-colors">
                    <td className="px-6 py-4">
                      {idx === 0 && <span className="text-xl">🥇</span>}
                      {idx === 1 && <span className="text-xl">🥈</span>}
                      {idx === 2 && <span className="text-xl">🥉</span>}
                      {idx > 2 && <span className="text-zinc-500 font-bold">{idx + 1}</span>}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-zinc-800 flex items-center justify-center text-zinc-500 overflow-hidden">
                          <img src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${user.user_id}`} alt="avatar" />
                        </div>
                        <div className="text-right">
                          <p className="text-white font-medium">{user.user_id}</p>
                          <p className="text-[10px] text-zinc-500 uppercase">ID: {user.user_id}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-zinc-300">{user.balance.toLocaleString()} سراب</td>
                    <td className="px-6 py-4 text-zinc-300">{user.bank_balance.toLocaleString()} سراب</td>
                    <td className="px-6 py-4">
                      <span className="bg-indigo-500/20 text-indigo-400 px-3 py-1 rounded-full text-sm font-bold">
                        {user.total.toLocaleString()} سراب
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default Economy;
