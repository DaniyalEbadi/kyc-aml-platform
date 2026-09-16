"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { Case } from "@/types";
import { STATUS_MAP, RISK_LEVEL_MAP, RISK_LEVEL_COLORS, PRIORITY_MAP, formatNumber } from "@/lib/utils";

export default function CasesPage() {
  const router = useRouter();
  const [cases, setCases] = useState<Case[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(true);

  const fetchCases = async (p: number, s: string) => {
    setLoading(true);
    try {
      const params: Record<string, string> = { page: String(p), page_size: "20" };
      if (s) params.status = s;
      const res = await api.getCases(params);
      setCases(res.items);
      setTotal(res.total);
    } catch {} finally { setLoading(false); }
  };

  useEffect(() => { fetchCases(page, statusFilter); }, [page, statusFilter]);

  const PRIORITY_COLORS: Record<string, string> = {
    low: "text-slate-400 bg-slate-400/10", normal: "text-blue-400 bg-blue-400/10",
    high: "text-amber-400 bg-amber-400/10", critical: "text-red-400 bg-red-400/10",
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">پرونده‌ها</h1>
          <p className="text-slate-400 mt-1">{formatNumber(total)} پرونده</p>
        </div>
      </div>
      <div className="flex gap-3">
        <select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
          className="px-4 py-2.5 bg-slate-800/50 border border-slate-700/50 rounded-xl text-sm text-white focus:outline-none focus:ring-2 focus:ring-brand-500/50">
          <option value="">همه وضعیت‌ها</option>
          {Object.entries(STATUS_MAP).slice(5).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {loading ? (
          <div className="col-span-3 flex items-center justify-center py-20"><div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" /></div>
        ) : cases.length === 0 ? (
          <div className="col-span-3 text-center text-slate-500 py-20">پرونده‌ای یافت نشد</div>
        ) : cases.map((c) => (
          <button key={c.id} onClick={() => router.push(`/cases/${c.id}`)}
            className="text-right bg-slate-800/50 border border-slate-700/50 rounded-2xl p-5 hover:border-slate-600/50 transition-all">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-brand-400 font-mono">{c.case_number}</span>
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${PRIORITY_COLORS[c.priority] || ""}`}>
                {PRIORITY_MAP[c.priority] || c.priority}
              </span>
            </div>
            <p className="text-sm text-white font-medium mb-1">{c.customer_name}</p>
            <p className="text-xs text-slate-400 mb-3">{c.application_number}</p>
            <div className="flex items-center justify-between">
              <span className={`px-2.5 py-1 rounded-lg text-xs font-medium ${RISK_LEVEL_COLORS[c.risk_level] || ""}`}>
                {RISK_LEVEL_MAP[c.risk_level] || c.risk_level}
              </span>
              <span className="text-xs text-slate-500">{STATUS_MAP[c.status] || c.status}</span>
            </div>
            {c.sla_due_at && (
              <p className="text-xs text-slate-500 mt-2">SLA: {new Date(c.sla_due_at).toLocaleDateString("fa-IR")}</p>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}