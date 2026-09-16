"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Policy } from "@/types";

export default function PoliciesPage() {
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [showSearch, setShowSearch] = useState(false);

  useEffect(() => {
    api.getPolicies().then(setPolicies).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const handleSearch = async (q: string) => {
    setSearchQuery(q);
    if (q.length < 2) { setSearchResults([]); setShowSearch(false); return; }
    try {
      const res = await api.searchPolicies(q);
      setSearchResults(res);
      setShowSearch(true);
    } catch {}
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">سیاست‌ها</h1>
          <p className="text-slate-400 mt-1">{policies.length} سیاست</p>
        </div>
      </div>
      <div className="relative">
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => handleSearch(e.target.value)}
          placeholder="جستجو در متن سیاست‌ها..."
          className="w-full px-4 py-2.5 bg-slate-800/50 border border-slate-700/50 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500/50"
        />
        {showSearch && searchResults.length > 0 && (
          <div className="absolute top-full mt-2 w-full bg-slate-800 border border-slate-700 rounded-xl shadow-2xl overflow-hidden z-50 max-h-96 overflow-y-auto">
            {searchResults.map((r: any, i) => (
              <div key={i} className="p-4 border-b border-slate-700/30 last:border-0">
                <p className="text-xs text-brand-400 font-medium">{r.section} - {r.clause}</p>
                <p className="text-sm text-white mt-1 line-clamp-3">{r.text}</p>
                <p className="text-xs text-slate-500 mt-2">نسخه سیاست: {r.policy_version}</p>
              </div>
            ))}
          </div>
        )}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {loading ? (
          <div className="col-span-2 flex items-center justify-center py-20"><div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" /></div>
        ) : policies.map((p) => (
          <div key={p.id} className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-5 hover:border-slate-600/50 transition-all">
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="text-white font-medium">{p.title}</h3>
                <p className="text-xs text-slate-400">{p.code}</p>
              </div>
            </div>
            <div className="space-y-2">
              {p.versions.map((v) => (
                <div key={v.id} className="flex items-center justify-between text-sm">
                  <span className="text-slate-300">نسخه {v.version}</span>
                  <span className={`px-2 py-0.5 rounded text-xs ${v.is_active ? "bg-emerald-400/10 text-emerald-400" : "bg-slate-600/50 text-slate-300"}`}>
                    {v.is_active ? "فعال" : "غیرفعال"}
                  </span>
                </div>
              ))}
            </div>
            <p className="text-xs text-slate-500 mt-3">{p.versions.reduce((acc, v) => acc + (v.chunk_count || 0), 0)} بند</p>
          </div>
        ))}
      </div>
    </div>
  );
}