"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export function Header() {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [showSearch, setShowSearch] = useState(false);

  const handleSearch = async (q: string) => {
    setSearchQuery(q);
    if (q.length < 2) { setSearchResults([]); return; }
    try {
      const res = await api.globalSearch(q);
      setSearchResults(res.results);
      setShowSearch(true);
    } catch {}
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    router.push("/login");
  };

  return (
    <header className="h-16 bg-slate-900/80 backdrop-blur-xl border-b border-slate-800 flex items-center justify-between px-6 sticky top-0 z-40">
      <div className="flex items-center gap-4 flex-1">
        <div className="relative max-w-md w-full">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            placeholder="جستجوی مشتری، درخواست، پرونده..."
            className="w-full px-4 py-2 bg-slate-800/50 border border-slate-700/50 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500/50 focus:border-brand-500/50 transition-all"
          />
          {showSearch && searchResults.length > 0 && (
            <div className="absolute top-full mt-2 w-full bg-slate-800 border border-slate-700 rounded-xl shadow-2xl overflow-hidden z-50">
              {searchResults.slice(0, 8).map((r) => (
                <button
                  key={r.id}
                  onClick={() => { router.push(r.url); setShowSearch(false); setSearchQuery(""); }}
                  className="w-full px-4 py-3 text-right hover:bg-slate-700/50 flex items-center gap-3 border-b border-slate-700/30 last:border-0"
                >
                  <span className="text-xs px-2 py-0.5 rounded bg-slate-700 text-slate-300">{r.type}</span>
                  <div>
                    <p className="text-sm text-white">{r.title}</p>
                    {r.subtitle && <p className="text-xs text-slate-400">{r.subtitle}</p>}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
      <div className="flex items-center gap-3">
        <button className="relative p-2 text-slate-400 hover:text-white transition-colors rounded-lg hover:bg-slate-800">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
          </svg>
          <span className="absolute -top-0.5 -left-0.5 w-4 h-4 bg-red-500 rounded-full text-[10px] text-white flex items-center justify-center">۳</span>
        </button>
        <button onClick={handleLogout} className="px-3 py-1.5 text-sm text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-all">
          خروج
        </button>
      </div>
    </header>
  );
}
