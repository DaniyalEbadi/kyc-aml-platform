"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { Customer } from "@/types";
import { RISK_LEVEL_MAP, RISK_LEVEL_COLORS, STATUS_MAP } from "@/lib/utils";

type CustomerDetail = Customer & { applications: any[]; notes: any[] };

export default function CustomerDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [customer, setCustomer] = useState<CustomerDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (params.id) {
      api.getCustomer(params.id as string).then(setCustomer as any).catch(() => {}).finally(() => setLoading(false));
    }
  }, [params.id]);

  if (loading) return <div className="flex items-center justify-center h-96"><div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" /></div>;
  if (!customer) return <div className="text-center text-slate-400 py-20">مشتری یافت نشد</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <button onClick={() => router.back()} className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
        </button>
        <div>
          <h1 className="text-2xl font-bold text-white">{customer.first_name} {customer.last_name}</h1>
          <p className="text-slate-400 mt-1">{customer.national_id || ""} | {customer.email || ""}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Info Card */}
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6">
          <h3 className="text-sm font-semibold text-white mb-4">اطلاعات پایه</h3>
          <div className="space-y-3">
            <InfoRow label="نام" value={`${customer.first_name} ${customer.last_name}`} />
            <InfoRow label="کد ملی" value={customer.national_id || "-"} />
            <InfoRow label="شماره پاسپورت" value={customer.passport_number || "-"} />
            <InfoRow label="تاریخ تولد" value={customer.birth_date || "-"} />
            <InfoRow label="جنسیت" value={customer.gender || "-"} />
            <InfoRow label="ملیت" value={customer.nationality} />
            <InfoRow label="استان" value={customer.province || "-"} />
            <InfoRow label="شهر" value={customer.city || "-"} />
            <InfoRow label="تلفن" value={customer.phone || "-"} />
            <InfoRow label="آدرس" value={customer.address || "-"} />
          </div>
        </div>

        {/* Risk Card */}
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6">
          <h3 className="text-sm font-semibold text-white mb-4">وضعیت ریسک</h3>
          <div className="flex flex-col items-center py-6">
            <div className="relative w-32 h-32">
              <svg className="w-32 h-32 -rotate-90" viewBox="0 0 120 120">
                <circle cx="60" cy="60" r="50" fill="none" stroke="#1e293b" strokeWidth="10" />
                <circle cx="60" cy="60" r="50" fill="none" stroke={customer.overall_risk_level === "low" ? "#10b981" : customer.overall_risk_level === "medium" ? "#f59e0b" : customer.overall_risk_level === "high" ? "#f97316" : "#ef4444"} strokeWidth="10" strokeDasharray={`${customer.overall_risk_score * 3.14} 314`} strokeLinecap="round" />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-3xl font-bold text-white">{customer.overall_risk_score}</span>
                <span className="text-xs text-slate-400">از ۱۰۰</span>
              </div>
            </div>
            <span className={`mt-4 px-4 py-1.5 rounded-lg text-sm font-medium ${RISK_LEVEL_COLORS[customer.overall_risk_level] || ""}`}>
              {RISK_LEVEL_MAP[customer.overall_risk_level] || customer.overall_risk_level}
            </span>
          </div>
        </div>

        {/* Applications */}
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6">
          <h3 className="text-sm font-semibold text-white mb-4">درخواست‌ها ({customer.applications?.length || 0})</h3>
          <div className="space-y-2 max-h-80 overflow-y-auto">
            {customer.applications?.map((app: any) => (
              <button key={app.id} onClick={() => router.push(`/applications/${app.id}`)} className="w-full text-right p-3 bg-slate-700/30 hover:bg-slate-700/50 rounded-xl transition-colors">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-white font-medium">{app.application_number}</span>
                  <span className="text-xs px-2 py-0.5 rounded bg-slate-600/50 text-slate-300">{STATUS_MAP[app.status] || app.status}</span>
                </div>
              </button>
            ))}
            {(!customer.applications || customer.applications.length === 0) && (
              <p className="text-sm text-slate-500 text-center py-4">بدون درخواست</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between py-1.5 border-b border-slate-700/30 last:border-0">
      <span className="text-xs text-slate-400">{label}</span>
      <span className="text-sm text-white">{value}</span>
    </div>
  );
}
