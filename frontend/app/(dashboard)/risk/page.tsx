"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { Application } from "@/types";
import { RISK_LEVEL_MAP, RISK_LEVEL_COLORS, formatNumber } from "@/lib/utils";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell
} from "recharts";

const RISK_COLORS: Record<string, string> = { low: "#10b981", medium: "#f59e0b", high: "#f97316", critical: "#ef4444" };

export default function RiskPage() {
  const router = useRouter();
  const [apps, setApps] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getApplications({ page_size: "100" }).then((res) => setApps(res.items)).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const riskDist = apps.reduce((acc, app) => {
    const level = app.risk_level || "unknown";
    acc[level] = (acc[level] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">ارزیابی ریسک</h1>
        <p className="text-slate-400 mt-1">{apps.length} درخواست</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6">
          <h3 className="text-sm font-semibold text-white mb-4">توزیع سطح ریسک</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie data={Object.entries(riskDist).map(([label, value]) => ({ label, value }))} cx="50%" cy="50%" innerRadius={60} outerRadius={100} dataKey="value" nameKey="label">
                {Object.entries(riskDist).map((_, i) => <Cell key={i} fill={RISK_COLORS[Object.entries(riskDist)[i][0]] || "#64748b"} />)}
              </Pie>
              <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: "8px" }} />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex justify-center gap-4 mt-4">
            {Object.entries(riskDist).map(([label, value]) => (
              <div key={label} className="flex items-center gap-2 text-xs text-slate-400">
                <div className="w-2.5 h-2.5 rounded-full" style={{ background: RISK_COLORS[label] }} />
                <span>{RISK_LEVEL_MAP[label] || label}</span>
                <span className="text-brand-400">{value}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6">
          <h3 className="text-sm font-semibold text-white mb-4">ریسک بر اساس منبع درآمد</h3>
          <ResponsiveContainer width="100%" height={300}>
<BarChart data={Object.entries(apps.reduce((acc, app) => {
                const k = app.source_of_funds || "نامشخص";
                acc[k] = (acc[k] || 0) + 1;
                return acc;
              }, {} as Record<string, number>)).map(([label, value]) => ({ label, value }))}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="label" stroke="#64748b" fontSize={11} />
              <YAxis stroke="#64748b" fontSize={11} />
              <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: "8px" }} />
              <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-700/50">
              <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400">شماره</th>
              <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400">مشتری</th>
              <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400">ریسک</th>
              <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400">امتیاز</th>
              <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400">منبع درآمد</th>
              <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400">حجم</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={6} className="px-6 py-12 text-center text-slate-500">در حال بارگذاری...</td></tr>
            ) : apps.map((app) => (
              <tr key={app.id} onClick={() => router.push(`/applications/${app.id}`)} className="border-b border-slate-700/30 hover:bg-slate-700/30 cursor-pointer transition-colors">
                <td className="px-6 py-4 text-brand-400 font-mono text-xs">{app.application_number}</td>
                <td className="px-6 py-4 text-white font-medium">{app.customer_name}</td>
                <td className="px-6 py-4">
                  <span className={`px-2.5 py-1 rounded-lg text-xs font-medium ${RISK_LEVEL_COLORS[app.risk_level || ""] || ""}`}>
                    {RISK_LEVEL_MAP[app.risk_level || ""] || "نامشخص"}
                  </span>
                </td>
                <td className="px-6 py-4 text-slate-300">{app.risk_score || "-"}</td>
                <td className="px-6 py-4 text-slate-400 text-sm">{app.source_of_funds || "-"}</td>
                <td className="px-6 py-4 text-slate-400 text-sm">{app.expected_volume || "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}