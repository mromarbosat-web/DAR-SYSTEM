import React from "react";
import { Shield, MessageSquare, Zap, Globe } from "lucide-react";

const Login: React.FC = () => {
  return (
    <div className="min-h-screen bg-black flex flex-col items-center justify-center p-6 font-['Cairo']" dir="rtl">
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden z-0 opacity-20 pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-indigo-600/30 rounded-full blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-purple-600/30 rounded-full blur-[120px]" />
      </div>

      <div className="relative z-10 w-full max-w-md bg-zinc-900 border border-zinc-800 p-12 rounded-[2.5rem] shadow-2xl text-center">
        <div className="bg-indigo-600 w-20 h-20 rounded-3xl mx-auto flex items-center justify-center mb-8 shadow-xl shadow-indigo-500/20 transform hover:rotate-12 transition-transform duration-500">
          <Shield className="w-10 h-10 text-white" />
        </div>

        <h1 className="text-4xl font-black text-white mb-4 tracking-tight">Security Bot</h1>
        <p className="text-zinc-400 mb-10 leading-relaxed">قم بتسجيل الدخول عبر ديسكورد للوصول إلى لوحة التحكم وإدارة سيرفراتك باحترافية.</p>

        <a
          href="/api/auth/login"
          className="w-full bg-[#5865F2] hover:bg-[#4752C4] text-white py-4 px-8 rounded-2xl font-bold flex items-center justify-center gap-4 transition-all hover:scale-[1.02] active:scale-95 shadow-lg shadow-[#5865F2]/20"
        >
          <img src="https://assets-global.website-files.com/6257ade0c7a694a2331a0d7c/636e30a065184f7062483863_Discord%20Logomark-White.svg" className="w-6 h-6" alt="Discord" />
          تسجيل الدخول باستخدام ديسكورد
        </a>

        <div className="mt-12 grid grid-cols-3 gap-4">
          <div className="flex flex-col items-center gap-2">
            <div className="p-2 bg-zinc-800 rounded-lg text-zinc-500"><Zap className="w-4 h-4" /></div>
            <span className="text-[10px] text-zinc-600 font-bold uppercase tracking-widest">سريع</span>
          </div>
          <div className="flex flex-col items-center gap-2">
            <div className="p-2 bg-zinc-800 rounded-lg text-zinc-500"><Globe className="w-4 h-4" /></div>
            <span className="text-[10px] text-zinc-600 font-bold uppercase tracking-widest">آمن</span>
          </div>
          <div className="flex flex-col items-center gap-2">
            <div className="p-2 bg-zinc-800 rounded-lg text-zinc-500"><MessageSquare className="w-4 h-4" /></div>
            <span className="text-[10px] text-zinc-600 font-bold uppercase tracking-widest">متكامل</span>
          </div>
        </div>
      </div>
      
      <p className="mt-12 text-zinc-700 text-xs font-medium uppercase tracking-[0.2em]">© 2026 Security Management System</p>
    </div>
  );
};

export default Login;
