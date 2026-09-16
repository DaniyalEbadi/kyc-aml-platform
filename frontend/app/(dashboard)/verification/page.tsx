"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { Application } from "@/types";
import { STATUS_MAP, RISK_LEVEL_MAP, RISK_LEVEL_COLORS, formatNumber } from "@/lib/utils";

export default function VerificationListPage() {
  const router = useRouter();
  const [apps, setApps] = useState<Application[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  const fetchApps = async (p: number, s: string, q: string) => {
    setLoading(true);
    try {
      const params: Record<string, string> = { page: String(p), page_size: "20" };
      if (s) params.status = s;
      if (q) params.search = q;
      const res = await api.getApplications(params);
      setApps(res.items);
      setTotal(res.total);
    } catch {} finally { setLoading(false); }
  };

  useEffect(() => { fetchApps(page, statusFilter, search); }, [page, statusFilter]);

  const handleSearch = () => { setPage(1); fetchApps(1, statusFilter, search); };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">بررسی مدارک</h1>
          <p className="text-slate-400 mt-1">{formatNumber(total)} درخواست</p>
        </div>
      </div>
      <div className="flex gap-3 flex-wrap">
        <input
          type="text" value={search} onChange={(e) => setSearch(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          placeholder="جستجو..."
          className="flex-1 min-w-[200px] px-4 py-2.5 bg-slate-800/50 border border-slate-700/50 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500/50"
        />
        <select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
          className="px-4 py-2.5 bg-slate-800/50 border border-slate-700/50 rounded-xl text-sm text-white focus:outline-none focus:ring-2 focus:ring-brand-500/50">
          <option value="">همه وضعیت‌ها</option>
          {Object.entries(STATUS_MAP).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <button onClick={handleSearch} className="px-6 py-2.5 bg-brand-600 hover:bg-brand-700 text-white text-sm font-medium rounded-xl transition-all">جستجو</button>
      </div>
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-700/50">
              <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400">شماره</th>
              <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400">مشتری</th>
              <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400">وضعیت</th>
              <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400">ریسک</th>
              <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400">تاریخ</th>
              <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400">عملیات</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={6} className="px-6 py-12 text-center text-slate-500">در حال بارگذاری...</td></tr>
            ) : apps.length === 0 ? (
              <tr><td colSpan={6} className="px-6 py-12 text-center text-slate-500">درخواستی یافت نشد</td></tr>
            ) : apps.map((app) => (
              <tr key={app.id} className="border-b border-slate-700/30 hover:bg-slate-700/30 transition-colors">
                <td className="px-6 py-4 text-brand-400 font-mono text-xs">{app.application_number}</td>
                <td className="px-6 py-4 text-white font-medium">{app.customer_name}</td>
                <td className="px-6 py-4">
                  <span className="inline-flex px-2.5 py-1 rounded-lg text-xs font-medium bg-slate-700/50 text-slate-300">
                    {STATUS_MAP[app.status] || app.status}
                  </span>
                </td>
                <td className="px-6 py-4">
                  {app.risk_level && (
                    <span className={`inline-flex px-2.5 py-1 rounded-lg text-xs font-medium ${RISK_LEVEL_COLORS[app.risk_level] || ""}`}>
                      {RISK_LEVEL_MAP[app.risk_level] || app.risk_level}
                    </span>
                  )}
                </td>
                <td className="px-6 py-4 text-slate-400 text-xs">{app.created_at ? new Date(app.created_at).toLocaleDateString("fa-IR") : "-"}</td>
                <td className="px-6 py-4">
                  <button onClick={() => router.push(`/verification/${app.id}`)}
                    className="px-3 py-1.5 bg-brand-600/20 text-brand-400 text-xs rounded-lg hover:bg-brand-600/30 transition-all">
                    بررسی
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {total > 20 && (
        <div className="flex items-center justify-center gap-2">
          <button disabled={page <= 1} onClick={() => setPage(page - 1)} className="px-3 py-1.5 text-sm bg-slate-800 border border-slate-700 rounded-lg text-slate-300 hover:bg-slate-700 disabled:opacity-40">قبلی</button>
          <span className="text-sm text-slate-400">صفحه {page} از {Math.ceil(total / 20)}</span>
          <button disabled={page >= Math.ceil(total / 20)} onClick={() => setPage(page + 1)} className="px-3 py-1.5 text-sm bg-slate-800 border border-slate-700 rounded-lg text-slate-300 hover:bg-slate-700 disabled:opacity-40">بعدی</button>
        </div>
      )}
    </div>
  );
}
