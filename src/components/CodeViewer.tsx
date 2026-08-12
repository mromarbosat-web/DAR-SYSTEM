import React, { useState, useEffect } from 'react';
import { Code, Folder, File, Copy, Check, Download, ChevronRight, ChevronDown } from 'lucide-react';
import { FileItem } from '../types';

export const CodeViewer: React.FC = () => {
  const [fileTree, setFileTree] = useState<FileItem[]>([]);
  const [selectedFile, setSelectedFile] = useState<string>('bot/main.py');
  const [fileContent, setFileContent] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);

  useEffect(() => {
    fetch('/api/bot/files')
      .then((res) => res.json())
      .then((data) => {
        if (data.files) setFileTree(data.files);
      })
      .catch((err) => console.error(err));
  }, []);

  useEffect(() => {
    if (selectedFile) {
      setLoading(true);
      fetch(`/api/bot/file-content?path=${encodeURIComponent(selectedFile)}`)
        .then((res) => res.json())
        .then((data) => {
          if (data.content) setFileContent(data.content);
          setLoading(false);
        })
        .catch(() => setLoading(false));
    }
  }, [selectedFile]);

  const copyCode = () => {
    navigator.clipboard.writeText(fileContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const renderTree = (items: FileItem[]) => {
    return (
      <ul className="space-y-1 pr-2 text-xs font-mono">
        {items.map((item, idx) => (
          <li key={idx}>
            {item.type === 'directory' ? (
              <details open className="group">
                <summary className="flex items-center gap-1.5 py-1 px-2 hover:bg-slate-800 rounded cursor-pointer text-slate-300 font-semibold select-none">
                  <Folder className="w-4 h-4 text-amber-400" />
                  <span>{item.name}</span>
                </summary>
                <div className="mr-3 border-r border-slate-800 pr-2">
                  {item.children && renderTree(item.children)}
                </div>
              </details>
            ) : (
              <button
                onClick={() => setSelectedFile(item.path)}
                className={`w-full text-right flex items-center gap-1.5 py-1 px-2 rounded font-sans text-xs transition-all ${
                  selectedFile === item.path
                    ? 'bg-indigo-600 text-white font-bold'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                }`}
              >
                <File className="w-3.5 h-3.5 text-indigo-400" />
                <span className="truncate">{item.name}</span>
              </button>
            )}
          </li>
        ))}
      </ul>
    );
  };

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Code className="w-6 h-6 text-indigo-400" />
            استعراض وتصدير كود المشروع بـ Python
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            جميع الملفات والوحدات محملة مسبقًا بالكامل وجاهزة للتشغيل المباشر كـ Railway Worker.
          </p>
        </div>

        <button
          onClick={copyCode}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-xl text-xs flex items-center gap-2 shadow-lg shadow-indigo-600/30"
        >
          {copied ? <Check className="w-4 h-4 text-emerald-300" /> : <Copy className="w-4 h-4" />}
          {copied ? 'تم نسخ ملف الكود!' : 'نسخ كود الملف الحالي'}
        </button>
      </div>

      {/* Explorer Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        
        {/* Sidebar File Tree */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 h-[600px] overflow-y-auto space-y-3">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider px-2 border-b border-slate-800 pb-2">
            شجرة الملفات (File Explorer)
          </h3>
          {renderTree(fileTree)}
        </div>

        {/* Code Content Editor/Viewer */}
        <div className="lg:col-span-3 bg-slate-950 border border-slate-800 rounded-2xl p-4 h-[600px] flex flex-col justify-between">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-2 font-mono text-xs">
            <span className="text-indigo-400 font-bold">{selectedFile}</span>
            <span className="text-slate-500">Python 3.11 / UTF-8</span>
          </div>

          <div className="flex-1 overflow-auto font-mono text-xs text-slate-200 leading-relaxed bg-slate-900/60 p-4 rounded-xl border border-slate-800/80">
            {loading ? (
              <div className="text-slate-500 h-full flex items-center justify-center">جاري تحميل الملف...</div>
            ) : (
              <pre className="whitespace-pre-wrap">{fileContent}</pre>
            )}
          </div>
        </div>

      </div>

    </div>
  );
};
