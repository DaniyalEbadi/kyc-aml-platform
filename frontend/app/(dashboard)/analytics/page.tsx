"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { AnalyticsData } from "@/types";
import { formatNumber } from "@/lib/utils";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, AreaChart, Area, LineChart, Line
} from "recharts";

const RISK_COLORS: Record<string, string> = { low: "#10b981", medium: "#f59e0b", high: "#f97316", critical: "#ef4444" };
const STATUS_LABELS: Record<string, string> = {
  draft: "پیش‌نویس", submitted: "ارسال‌شده", processing: "در حال پردازش",
  in_review: "در انتظار بررسی", approved: "تأیید شده", rejected: "رد شده",
  needs_resubmission: "ارسال مجدد", escalated: "ارجاع‌شده",
};
const DOC_TYPE_MAP: Record<string, string> = {
  passport: "گذرنامه", national_id: "کارت ملی", driver_license: "گواهینامه",
  proof_of_address: "نشانی", selfie: "سلفی", business: "کسب‌وکار", residence: "اقامت"
};

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getAnalytics().then(setData).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex items-center justify-center h-96"><div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" /></div>;
  if (!data) return <div className="text-center text-slate-400 py-20">خطا در بارگذاری داده‌ها</div>;

  const { kpis } = data;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">تحلیل‌ها و گزارش‌ها</h1>
          <p className="text-slate-400 mt-1">نمای کلی عملکرد سامانه</p>
        </div>
        <div className="text-sm text-slate-500">{new Date().toLocaleDateString("fa-IR")}</div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        <KPICard title="کل درخواست‌ها" value={kpis.total_applications} icon="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        <KPICard title="درخواست‌های جدید" value={kpis.new_applications} icon="M12 4v16m8-8H4" color="text-blue-400" />
        <KPICard title="نرخ تأیید" value={`${kpis.approval_rate}%`} icon="M5 13l4 4L19 7" color="text-emerald-400" />
        <KPICard title="پرونده‌های باز" value={kpis.open_cases} icon="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2" color="text-amber-400" />
        <KPICard title="ریسک بالا" value={kpis.high_risk_count + kpis.critical_count} icon="M12 9v2m0 4h.01" color="text-red-400" />
      </div>

      {/* Second row KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        <StatCard label="تأیید شده" value={kpis.approved_count} color="text-emerald-400" />
        <StatCard label="رد شده" value={kpis.rejected_count} color="text-red-400" />
        <StatCard label="در بررسی" value={kpis.in_review_count} color="text-amber-400" />
        <StatCard label="مشتریان" value={kpis.total_customers} color="text-blue-400" />
        <StatCard label="کل پرونده‌ها" value={kpis.total_cases} color="text-purple-400" />
        <StatCard label="بحرانی" value={kpis.critical_count} color="text-red-500" />
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard title="روند درخواست‌ها (۳۰ روز اخیر)">
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={data.applications_over_time}>
              <defs>
                <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="date" stroke="#64748b" fontSize={11} tickFormatter={(v) => v.slice(5)} />
              <YAxis stroke="#64748b" fontSize={11} />
              <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: "8px", direction: "rtl" }} />
              <Area type="monotone" dataKey="value" stroke="#3b82f6" fillOpacity={1} fill="url(#colorValue)" />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="توزیع ریسک">
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie data={data.risk_distribution} cx="50%" cy="50%" innerRadius={70} outerRadius={110} dataKey="value" nameKey="label" label={({ label, value }) => `${value}`} labelLine={false}>
                {data.risk_distribution.map((entry, i) => (
                  <Cell key={i} fill={RISK_COLORS[entry.label] || "#64748b"} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: "8px", direction: "rtl" }} />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex justify-center gap-4 mt-2">
            {data.risk_distribution.map((d) => (
              <div key={d.label} className="flex items-center gap-2 text-xs text-slate-400">
                <div className="w-2.5 h-2.5 rounded-full" style={{ background: RISK_COLORS[d.label] }} />
                <span>{d.label === "low" ? "پایین" : d.label === "medium" ? "متوسط" : d.label === "high" ? "بالا" : "بحرانی"}</span>
              </div>
            ))}
          </div>
        </ChartCard>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard title="وضعیت درخواست‌ها">
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={data.status_distribution.filter(d => d.value > 0)} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis type="number" stroke="#64748b" fontSize={11} />
              <YAxis dataKey="label" type="category" stroke="#64748b" fontSize={11} width={100} tickFormatter={(v) => STATUS_LABELS[v] || v} />
              <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: "8px", direction: "rtl" }} formatter={(v: any) => [v, "تعداد"]} />
              <Bar dataKey="value" fill="#3b82f6" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="سند بر اساس نوع">
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={data.document_type_distribution.filter(d => d.value > 0)}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="label" stroke="#64748b" fontSize={11} tickFormatter={(v) => DOC_TYPE_MAP[v] || v} />
              <YAxis stroke="#64748b" fontSize={11} />
              <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: "8px", direction: "rtl" }} />
              <Bar dataKey="value" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* Funnel */}
      <ChartCard title="قیف احراز هویت">
        <div className="flex items-end justify-between gap-2 px-4 py-6">
          {data.verification_funnel.map((step, i) => {
            const maxCount = data.verification_funnel[0]?.count || 1;
            const heightPct = (step.count / maxCount) * 100;
            return (
              <div key={i} className="flex-1 flex flex-col items-center gap-2">
                <span className="text-xs text-white font-medium">{formatNumber(step.count)}</span>
                <div className="w-full bg-brand-600/20 rounded-t-lg relative" style={{ height: `${Math.max(heightPct, 5)}%`, minHeight: "20px" }}>
                  <div className="absolute bottom-0 left-0 right-0 bg-brand-500 rounded-t-lg transition-all" style={{ height: "100%" }} />
                </div>
                <span className="text-xs text-slate-400 text-center">{step.step}</span>
              </div>
            );
          })}
        </div>
      </ChartCard>

      {/* Additional Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <ChartCard title="نرخ‌ها">
          <div className="space-y-4">
            <RateBar label="نرخ تأیید" value={kpis.approval_rate} color="bg-emerald-500" />
            <RateBar label="نرخ رد" value={kpis.rejection_rate} color="bg-red-500" />
            <RateBar label="نرخ بررسی انسانی" value={kpis.human_review_rate} color="bg-amber-500" />
          </div>
        </ChartCard>

        <ChartCard title="آمار پردازش">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-400">میانگین زمان پردازش</span>
              <span className="text-lg font-bold text-white">{kpis.avg_processing_hours.toFixed(1)} ساعت</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-400">میانگین زمان بررسی</span>
              <span className="text-lg font-bold text-white">{kpis.avg_review_hours.toFixed(1)} ساعت</span>
            </div>
          </div>
        </ChartCard>

        <ChartCard title="خلاصه">
          <div className="space-y-3">
            <SummaryRow label="کل مشتریان" value={kpis.total_customers} />
            <SummaryRow label="کل پرونده‌ها" value={kpis.total_cases} />
            <SummaryRow label="پرونده‌های باز" value={kpis.open_cases} />
            <SummaryRow label="ریسک بالا" value={kpis.high_risk_count} />
            <SummaryRow label="بحرانی" value={kpis.critical_count} />
          </div>
        </ChartCard>
      </div>
    </div>
  );
}

function KPICard({ title, value, icon, color = "text-brand-400" }: { title: string; value: string | number; icon: string; color?: string }) {
  return (
    <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-5 hover:border-slate-600/50 transition-all">
      <div className="flex items-center justify-between mb-3">
        <div className={`w-10 h-10 rounded-xl bg-slate-700/50 flex items-center justify-center ${color}`}>
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d={icon} />
          </svg>
        </div>
      </div>
      <p className="text-2xl font-bold text-white">{typeof value === "number" ? formatNumber(value) : value}</p>
      <p className="text-sm text-slate-400 mt-1">{title}</p>
    </div>
  );
}

function StatCard({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="bg-slate-800/30 border border-slate-700/30 rounded-xl px-4 py-3 flex items-center justify-between">
      <span className="text-sm text-slate-400">{label}</span>
      <span className={`text-lg font-bold ${color}`}>{formatNumber(value)}</span>
    </div>
  );
}

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6">
      <h3 className="text-sm font-semibold text-white mb-4">{title}</h3>
      {children}
    </div>
  );
}

function RateBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm text-slate-400">{label}</span>
        <span className="text-sm font-medium text-white">{value}%</span>
      </div>
      <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all`} style={{ width: `${Math.min(value, 100)}%` }} />
      </div>
    </div>
  );
}

function SummaryRow({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-slate-400">{label}</span>
      <span className="text-sm font-bold text-white">{formatNumber(value)}</span>
    </div>
  );
}
