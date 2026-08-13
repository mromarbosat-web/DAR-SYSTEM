import React from "react";
import { useAuth } from "../context/AuthContext";
import { LogOut, ChevronDown } from "lucide-react";

const Navbar: React.FC = () => {
  const { user, guilds, selectedGuildId, setSelectedGuildId, logout } = useAuth();
  const selectedGuild = guilds.find((g) => g.id === selectedGuildId);

  return (
    <header className="fixed top-0 left-0 right-0 h-16 bg-zinc-900/80 backdrop-blur-md border-b border-zinc-800 z-50 px-4 md:px-8 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <div className="bg-indigo-600 p-2 rounded-lg">
          <Shield className="w-6 h-6 text-white" />
        </div>
        <h1 className="text-xl font-bold text-white hidden sm:block">Security Bot Hub</h1>
      </div>

      <div className="flex items-center gap-4">
        {guilds.length > 0 && (
          <div className="relative group">
            <button className="flex items-center gap-3 bg-zinc-800 hover:bg-zinc-700 px-4 py-2 rounded-lg transition-colors text-white">
              {selectedGuild?.icon ? (
                <img src={`https://cdn.discordapp.com/icons/${selectedGuild.id}/${selectedGuild.icon}.png`} className="w-6 h-6 rounded-full" />
              ) : (
                <div className="w-6 h-6 rounded-full bg-indigo-500 flex items-center justify-center text-xs">
                  {selectedGuild?.name.charAt(0)}
                </div>
              )}
              <span className="max-w-[120px] truncate">{selectedGuild?.name}</span>
              <ChevronDown className="w-4 h-4 text-zinc-400" />
            </button>
            <div className="absolute top-full left-0 mt-2 w-56 bg-zinc-800 border border-zinc-700 rounded-xl shadow-2xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-[60]">
              <div className="p-2 space-y-1">
                {guilds.map((guild) => (
                  <button
                    key={guild.id}
                    onClick={() => setSelectedGuildId(guild.id)}
                    className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors text-left ${
                      selectedGuildId === guild.id ? "bg-indigo-600 text-white" : "text-zinc-300 hover:bg-zinc-700"
                    }`}
                  >
                    {guild.icon ? (
                      <img src={`https://cdn.discordapp.com/icons/${guild.id}/${guild.icon}.png`} className="w-6 h-6 rounded-full" />
                    ) : (
                      <div className="w-6 h-6 rounded-full bg-zinc-700 flex items-center justify-center text-xs">
                        {guild.name.charAt(0)}
                      </div>
                    )}
                    <span className="truncate">{guild.name}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {user && (
          <div className="flex items-center gap-3">
            <div className="text-left hidden sm:block">
              <p className="text-sm font-medium text-white leading-none">{user.username}</p>
              <button onClick={logout} className="text-[10px] text-zinc-500 hover:text-red-400 transition-colors uppercase tracking-wider font-bold">تسجيل الخروج</button>
            </div>
            <img 
              src={`https://cdn.discordapp.com/avatars/${user.id}/${user.avatar}.png`} 
              className="w-10 h-10 rounded-full border-2 border-zinc-700"
              alt={user.username}
            />
          </div>
        )}
      </div>
    </header>
  );
};

import { Shield } from "lucide-react";

export default Navbar;
