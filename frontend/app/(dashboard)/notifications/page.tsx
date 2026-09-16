"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Notification } from "@/types";

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);

  const fetch = async (p: number) => {
    setLoading(true);
    try {
      const res = await api.getNotifications({ page: String(p), page_size: "20" });
      setNotifications(res.items);
      setUnreadCount(res.unread_count);
    } catch {} finally { setLoading(false); }
  };

  useEffect(() => { fetch(page); }, [page]);

  const handleMarkAll = async () => {
    await api.markNotificationsRead([], true);
    fetch(page);
  };

  const KIND_LABELS: Record<string, string> = {
    new_case: "پرونده جدید", high_risk: "ریسک بالا", report: "گزارش", review_needed: "نیاز به بررسی",
  };
  const KIND_COLORS: Record<string, string> = {
    new_case: "text-brand-400 bg-brand-400/10", high_risk: "text-red-400 bg-red-400/10",
    report: "text-purple-400 bg-purple-400/10", review_needed: "text-amber-400 bg-amber-400/10",
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">اعلانات</h1>
          <p className="text-slate-400 mt-1">{unreadCount} خوانده‌نشده</p>
        </div>
        {unreadCount > 0 && (
          <button onClick={handleMarkAll} className="px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white text-sm font-medium rounded-xl transition-all">
            علامت‌گذاری همه به عنوان خوانده
          </button>
        )}
      </div>
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl overflow-hidden">
        <div className="divide-y divide-slate-700/30">
          {loading ? (
            <div className="p-12 text-center text-slate-500"><div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin mx-auto" /></div>
          ) : notifications.length === 0 ? (
            <div className="p-12 text-center text-slate-500">اعلانی وجود ندارد</div>
          ) : notifications.map((n) => (
            <div key={n.id} className={`p-5 flex items-start gap-4 ${n.read ? "" : "bg-brand-600/5"}`}>
              <div className={`w-2.5 h-2.5 rounded-full mt-1.5 flex-shrink-0 ${KIND_COLORS[n.kind] || "text-slate-400 bg-slate-400/10"}`} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <h4 className="text-sm font-medium text-white">{n.title}</h4>
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${KIND_COLORS[n.kind] || ""}`}>
                    {KIND_LABELS[n.kind] || n.kind}
                  </span>
                </div>
                <p className="text-sm text-slate-400 mt-1">{n.body}</p>
                <p className="text-xs text-slate-500 mt-2">{n.created_at ? new Date(n.created_at).toLocaleString("fa-IR") : ""}</p>
              </div>
              {!n.read && (
                <button onClick={() => api.markNotificationsRead([n.id]).then(() => fetch(page))}
                  className="px-3 py-1.5 text-xs bg-brand-600 hover:bg-brand-700 text-white rounded-lg transition-all">
                  خواندن
                </button>
              )}
            </div>
          ))}
        </div>
      </div>
      {notifications.length > 0 && (
        <div className="flex items-center justify-center gap-2">
          <button disabled={page <= 1} onClick={() => { setPage(page - 1); fetch(page - 1); }} className="px-3 py-1.5 text-sm bg-slate-800 border border-slate-700 rounded-lg text-slate-300 hover:bg-slate-700 disabled:opacity-40">قبلی</button>
          <span className="text-sm text-slate-400">صفحه {page}</span>
          <button disabled={notifications.length < 20} onClick={() => { setPage(page + 1); fetch(page + 1); }} className="px-3 py-1.5 text-sm bg-slate-800 border border-slate-700 rounded-lg text-slate-300 hover:bg-slate-700 disabled:opacity-40">بعدی</button>
        </div>
      )}
    </div>
  );
}