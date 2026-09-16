"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { AuditEvent } from "@/types";
import { formatNumber } from "@/lib/utils";

export default function AuditPage() {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [entityFilter, setEntityFilter] = useState("");
  const [loading, setLoading] = useState(true);

  const fetchEvents = async (p: number) => {
    setLoading(true);
    try {
      const params: Record<string, string> = { page: String(p), page_size: "50" };
      if (entityFilter) params.entity = entityFilter;
      const res = await api.getAuditEvents(params);
      setEvents(res.items);
      setTotal(res.total);
    } catch {} finally { setLoading(false); }
  };

  useEffect(() => { fetchEvents(page); }, [page, entityFilter]);

  const ACTION_LABELS: Record<string, string> = {
    "application.create": "ایجاد درخواست", "application.submit": "ارسال درخواست",
    "engine.decision": "تصمیم موتور", "case.assign": "اختصاص پرونده",
    "review.action": "عملیات بررسی",
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">گزارش رویدادها</h1>
          <p className="text-slate-400 mt-1">{formatNumber(total)} رویداد</p>
        </div>
      </div>
      <div className="flex gap-3">
        <select value={entityFilter} onChange={(e) => { setEntityFilter(e.target.value); setPage(1); }}
          className="px-4 py-2.5 bg-slate-800/50 border border-slate-700/50 rounded-xl text-sm text-white focus:outline-none focus:ring-2 focus:ring-brand-500/50">
          <option value="">همه موجودیت‌ها</option>
          <option value="application">درخواست</option>
          <option value="case">پرونده</option>
          <option value="document">مدرک</option>
        </select>
      </div>
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-700/50">
              <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400">تاریخ</th>
              <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400">عملیات</th>
              <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400">موجودیت</th>
              <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400">شناسه</th>
              <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400">بازیگر</th>
              <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400">دلیل</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={6} className="px-6 py-12 text-center text-slate-500">در حال بارگذاری...</td></tr>
            ) : events.length === 0 ? (
              <tr><td colSpan={6} className="px-6 py-12 text-center text-slate-500">رویدادی یافت نشد</td></tr>
            ) : events.map((e) => (
              <tr key={e.id} className="border-b border-slate-700/30 hover:bg-slate-700/30 transition-colors">
                <td className="px-6 py-4 text-slate-400 text-xs whitespace-nowrap">{e.created_at ? new Date(e.created_at).toLocaleString("fa-IR") : "-"}</td>
                <td className="px-6 py-4"><span className="px-2.5 py-1 rounded-lg text-xs bg-brand-600/10 text-brand-400">{ACTION_LABELS[e.action] || e.action}</span></td>
                <td className="px-6 py-4 text-slate-300 text-xs">{e.entity}</td>
                <td className="px-6 py-4 text-slate-400 font-mono text-xs">{e.entity_id.slice(0, 8)}...</td>
                <td className="px-6 py-4 text-slate-400 text-xs">{e.actor_role || "-"}</td>
                <td className="px-6 py-4 text-slate-400 text-xs max-w-[200px] truncate">{e.reason || "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {total > 50 && (
        <div className="flex items-center justify-center gap-2">
          <button disabled={page <= 1} onClick={() => setPage(page - 1)} className="px-3 py-1.5 text-sm bg-slate-800 border border-slate-700 rounded-lg text-slate-300 hover:bg-slate-700 disabled:opacity-40">قبلی</button>
          <span className="text-sm text-slate-400">صفحه {page} از {Math.ceil(total / 50)}</span>
          <button disabled={page >= Math.ceil(total / 50)} onClick={() => setPage(page + 1)} className="px-3 py-1.5 text-sm bg-slate-800 border border-slate-700 rounded-lg text-slate-300 hover:bg-slate-700 disabled:opacity-40">بعدی</button>
        </div>
      )}
    </div>
  );
}