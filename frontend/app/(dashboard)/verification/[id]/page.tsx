"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { ApplicationDetail } from "@/types";
import { DOC_TYPE_MAP, formatNumber } from "@/lib/utils";

export default function VerificationPage() {
  const params = useParams();
  const router = useRouter();
  const [app, setApp] = useState<ApplicationDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (params.id) api.getApplication(params.id as string).then(setApp).catch(() => {}).finally(() => setLoading(false));
  }, [params.id]);

  if (loading) return <div className="flex items-center justify-center h-96"><div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" /></div>;
  if (!app) return <div className="text-center text-slate-400 py-20">درخواست یافت نشد</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <button onClick={() => router.back()} className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
        </button>
        <div>
          <h1 className="text-2xl font-bold text-white">احراز هویت</h1>
          <p className="text-slate-400 mt-1">{app.application_number} | {app.customer_name}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Face Verification */}
        <div className="lg:col-span-2 bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6">
          <h3 className="text-sm font-semibold text-white mb-4">تطبیق چهره</h3>
          {app.face_verification ? (
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <MetricCard label="شباهت" value={`${(app.face_verification.similarity * 100).toFixed(1)}%`} color={app.face_verification.similarity >= 0.62 ? "text-emerald-400" : "text-red-400"} />
                <MetricCard label="کیفیت" value={`${(app.face_verification.quality_score * 100).toFixed(1)}%`} color="text-blue-400" />
                <MetricCard label="اطمینان" value={`${(app.face_verification.confidence * 100).toFixed(1)}%`} color="text-purple-400" />
              </div>
              <div className="p-4 bg-slate-700/30 rounded-xl">
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-full ${app.face_verification.decision === "match" ? "bg-emerald-400/20" : "bg-red-400/20"}`}>
                    <svg className="w-5 h-5 mx-auto mt-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={app.face_verification.decision === "match" ? "M5 13l4 4L19 7" : "M6 18L18 6M6 6l12 12"} />
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-white">{app.face_verification.decision === "match" ? "تطبیق" : "عدم تطبیق"}</p>
                    <p className="text-xs text-slate-400">آستانه: ۶۲٪</p>
                  </div>
                </div>
                <div className="mt-3 pt-3 border-t border-slate-700/30">
                  <p className="text-xs text-slate-400">دلیل‌ها: {app.face_verification.reasons?.join("، ") || "بدون دلیل"}</p>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-12">
              <svg className="w-16 h-16 mx-auto text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
              <p className="text-slate-400 mt-4">اعتبارسنجی چهره انجام نشده</p>
            </div>
          )}
        </div>

        {/* Document Verification */}
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6">
          <h3 className="text-sm font-semibold text-white mb-4">بررسی مدارک</h3>
          <div className="space-y-3">
            {app.verifications.length === 0 ? <p className="text-slate-500 text-center py-4">احراز هویت انجام نشده</p> : app.verifications.map((v) => (
              <div key={v.id} className="p-4 bg-slate-700/20 rounded-xl">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-lg ${v.kind === "ocr" ? "bg-blue-400/20" : "bg-purple-400/20"}`}>
                      <svg className="w-4 h-4 mx-auto mt-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d={v.kind === "ocr" ? "M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" : "M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"} />
                      </svg>
                    </div>
                    <span className="text-sm font-medium text-white capitalize">{v.kind}</span>
                  </div>
                  <span className={`px-2.5 py-1 rounded-lg text-xs ${v.status === "done" ? "bg-emerald-400/10 text-emerald-400" : "bg-slate-600/50 text-slate-300"}`}>
                    {v.status === "done" ? "تکمیل" : v.status}
                  </span>
                </div>
                {v.score !== null && (
                  <div className="mt-2 h-2 bg-slate-700 rounded-full overflow-hidden">
                    <div className="h-full bg-brand-500 rounded-full transition-all" style={{ width: `${v.score * 100}%` }} />
                  </div>
                )}
                {v.kind === "ocr" && v.details && (
                  <div className="mt-2 flex items-center gap-3 text-xs text-slate-500">
                    <span>ارائه‌دهنده: {(v.details as any).provider === "mock" ? "شبیه‌ساز" : (v.details as any).provider === "easyocr" ? "EasyOCR (واقعی)" : (v.details as any).provider}</span>
                    {(v.details as any).is_simulated !== undefined && (
                      <span className={(v.details as any).is_simulated ? "text-amber-400" : "text-emerald-400"}>
                        {(v.details as any).is_simulated ? "شبیه‌سازی شده" : "واقعی"}
                      </span>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Document Quality & Extracted Fields */}
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6">
          <h3 className="text-sm font-semibold text-white mb-4">کیفیت و اطلاعات استخراج شده</h3>
          <div className="space-y-3">
            {app.documents.length === 0 ? <p className="text-slate-500 text-center py-4">مدرکی بارگذاری نشده</p> : app.documents.map((d) => (
              <div key={d.id} className="p-3 bg-slate-700/20 rounded-xl">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-white">{DOC_TYPE_MAP[d.doc_type] || d.doc_type}</span>
                  <span className={`px-2 py-0.5 rounded text-xs ${d.status === "processed" ? "bg-emerald-400/10 text-emerald-400" : d.status === "processing" ? "bg-brand-400/10 text-brand-400" : "bg-slate-600/50 text-slate-300"}`}>
                    {d.status === "uploaded" ? "بارگذاری" : d.status === "processing" ? "پردازش" : d.status === "processed" ? "تکمیل" : d.status}
                  </span>
                </div>
                {d.fields && d.fields.length > 0 ? (
                  <div className="space-y-1.5 mt-3">
                    {d.fields.map((f) => (
                      <div key={f.id} className="flex items-center justify-between text-xs">
                        <span className="text-slate-400">{f.field_label}</span>
                        <div className="flex items-center gap-2">
                          <span className="text-white font-medium">{f.value || "-"}</span>
                          <div className="w-12 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                            <div className={`h-full rounded-full ${f.confidence >= 0.8 ? "bg-emerald-500" : f.confidence >= 0.6 ? "bg-amber-500" : "bg-red-500"}`} style={{ width: `${f.confidence * 100}%` }} />
                          </div>
                          <span className="text-slate-500 w-8 text-left">{Math.round(f.confidence * 100)}%</span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-500 mt-2">اطلاعاتی استخراج نشده</p>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function MetricCard({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="p-4 bg-slate-700/30 rounded-xl">
      <p className="text-xs text-slate-400">{label}</p>
      <p className={`text-2xl font-bold ${color} mt-1`}>{value}</p>
    </div>
  );
}