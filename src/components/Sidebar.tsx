import React from "react";
import { NavLink } from "react-router-dom";
import { Home, Zap, Shield, Coins, ClipboardList } from "lucide-react";

const Sidebar: React.FC = () => {
  const links = [
    { name: "الرئيسية", icon: Home, path: "/" },
    { name: "الاختصارات", icon: Zap, path: "/shortcuts" },
    { name: "الحماية", icon: Shield, path: "/protection" },
    { name: "الاقتصاد", icon: Coins, path: "/economy" },
    { name: "اللوجات", icon: ClipboardList, path: "/logs" },
  ];

  return (
    <aside className="w-64 bg-zinc-900 border-l border-zinc-800 h-screen fixed right-0 top-0 pt-20 hidden md:block">
      <nav className="px-4 space-y-2">
        {links.map((link) => (
          <NavLink
            key={link.path}
            to={link.path}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                isActive ? "bg-indigo-600 text-white" : "text-zinc-400 hover:bg-zinc-800 hover:text-white"
              }`
            }
          >
            <link.icon className="w-5 h-5" />
            <span className="font-medium">{link.name}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
};

export default Sidebar;
