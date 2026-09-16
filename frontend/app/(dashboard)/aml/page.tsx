"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { Application } from "@/types";
import { SCREENING_KIND_MAP, formatNumber } from "@/lib/utils";

export default function AmlPage() {
  const router = useRouter();
  const [apps, setApps] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getApplications({ page_size: "100" }).then((res) => setApps(res.items)).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const screeningStats = apps.reduce((acc, app) => {
    acc.total++;
    if (app.screenings && app.screenings.some(s => s.matched)) {
      acc.matched++;
      app.screenings.forEach(s => {
        if (s.matched) acc.byKind[s.kind] = (acc.byKind[s.kind] || 0) + 1;
      });
    }
    return acc;
  }, { total: 0, matched: 0, byKind: {} as Record<string, number> });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">مبارزه با پولشویی (AML)</h1>
        <p className="text-slate-400 mt-1">{screeningStats.total} درخواست، {screeningStats.matched} تطبیق</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard title="کل غربالگری‌ها" value={screeningStats.total} />
        <StatCard title="تطبیق یافته" value={screeningStats.matched} color="text-red-400" />
        <StatCard title="تحریم‌ها" value={screeningStats.byKind.sanctions || 0} color="text-orange-400" />
        <StatCard title="اشخاص سیاسی" value={screeningStats.byKind.pep || 0} color="text-amber-400" />
      </div>

      <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-700/50">
              <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400">شماره</th>
              <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400">مشتری</th>
              <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400">نوع</th>
              <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400">فهرست</th>
              <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400">نام تطبیق‌یافته</th>
              <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400">امتیاز</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={6} className="px-6 py-12 text-center text-slate-500">در حال بارگذاری...</td></tr>
            ) : apps.flatMap(app =>
              app.screenings?.map(s => ({ ...s, app_number: app.application_number, customer: app.customer_name })) || []
            ).filter(s => s.matched).map((s, i) => (
              <tr key={i} className="border-b border-slate-700/30 hover:bg-slate-700/30 transition-colors">
                <td className="px-6 py-4 text-brand-400 font-mono text-xs">{s.app_number}</td>
                <td className="px-6 py-4 text-white font-medium">{s.customer}</td>
                <td className="px-6 py-4">
                  <span className="px-2.5 py-1 rounded-lg text-xs bg-red-400/10 text-red-400">{SCREENING_KIND_MAP[s.kind] || s.kind}</span>
                </td>
                <td className="px-6 py-4 text-slate-300 text-sm">{s.list_name || "-"}</td>
                <td className="px-6 py-4 text-slate-400 text-sm">{s.matched_name || "-"}</td>
                <td className="px-6 py-4 text-red-400 font-mono">{s.score.toFixed(1)}</td>
              </tr>
            ))}
            {apps.flatMap(app => app.screenings?.map(s => ({ ...s, app_number: app.application_number, customer: app.customer_name })) || []).filter(s => s.matched).length === 0 && !loading && (
              <tr><td colSpan={6} className="px-6 py-12 text-center text-slate-500">تطبیقی یافت نشد</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function StatCard({ title, value, color = "text-brand-400" }: { title: string; value: number; color?: string }) {
  return (
    <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-5">
      <p className="text-sm text-slate-400">{title}</p>
      <p className={`text-3xl font-bold ${color} mt-1`}>{formatNumber(value)}</p>
    </div>
  );
}