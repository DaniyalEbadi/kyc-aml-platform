"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { ApplicationDetail } from "@/types";
import { STATUS_MAP, RISK_LEVEL_MAP, RISK_LEVEL_COLORS, DOC_TYPE_MAP, SCREENING_KIND_MAP, formatNumber } from "@/lib/utils";

type Tab = "overview" | "documents" | "verification" | "risk" | "screening" | "decisions" | "timeline";

export default function ApplicationDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [app, setApp] = useState<ApplicationDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<Tab>("overview");
  const [uploading, setUploading] = useState(false);
  const [uploadDocType, setUploadDocType] = useState("national_id");

  useEffect(() => {
    if (params.id) api.getApplication(params.id as string).then(setApp).catch(() => {}).finally(() => setLoading(false));
  }, [params.id]);

  if (loading) return <div className="flex items-center justify-center h-96"><div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" /></div>;
  if (!app) return <div className="text-center text-slate-400 py-20">درخواست یافت نشد</div>;

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !app) return;
    setUploading(true);
    try {
      await api.uploadDocument(app.id, uploadDocType, file);
      const updated = await api.getApplication(app.id);
      setApp(updated);
      setTab("documents");
    } catch {} finally { setUploading(false); if (e.target) e.target.value = ""; }
  };

  const tabs: { key: Tab; label: string }[] = [
    { key: "overview", label: "نمای کلی" },
    { key: "documents", label: "مدارک" },
    { key: "verification", label: "احراز هویت" },
    { key: "risk", label: "ریسک" },
    { key: "screening", label: "غربالگری" },
    { key: "decisions", label: "تصمیمات" },
    { key: "timeline", label: "تاریخچه" },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <button onClick={() => router.back()} className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
        </button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-white">{app.application_number}</h1>
          <p className="text-slate-400 mt-1">{app.customer_name} | <span className={`inline-flex px-2 py-0.5 rounded text-xs ${RISK_LEVEL_COLORS[app.risk?.level || ""]}`}>{RISK_LEVEL_MAP[app.risk?.level || ""] || "-"}</span></p>
        </div>
        <span className="px-4 py-2 rounded-xl text-sm font-medium bg-slate-700/50 text-slate-300">{STATUS_MAP[app.status] || app.status}</span>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-slate-800/50 p-1 rounded-xl border border-slate-700/50">
        {tabs.map((t) => (
          <button key={t.key} onClick={() => setTab(t.key)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${tab === t.key ? "bg-brand-600 text-white" : "text-slate-400 hover:text-white hover:bg-slate-700/50"}`}>
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6">
        {tab === "overview" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div>
              <h3 className="text-sm font-semibold text-white mb-3">اطلاعات مشتری</h3>
              <div className="space-y-2">
                <Row label="نام" value={app.customer ? `${app.customer.first_name} ${app.customer.last_name}` : "-"} />
                <Row label="کد ملی" value={app.customer?.national_id || "-"} />
                <Row label="ملیت" value={app.customer?.nationality || "-"} />
                <Row label="شغل" value={app.occupation || "-"} />
                <Row label="درآمد اعلامی" value={app.declared_income || "-"} />
                <Row label="منبع وجوه" value={app.source_of_funds || "-"} />
                <Row label="حجم مورد انتظار" value={app.expected_volume || "-"} />
              </div>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white mb-3">اطلاعات درخواست</h3>
              <div className="space-y-2">
                <Row label="jurisdiction" value={app.jurisdiction} />
                <Row label="منبع" value={app.source} />
                <Row label="تاریخ ارسال" value={app.submitted_at ? new Date(app.submitted_at).toLocaleDateString("fa-IR") : "-"} />
                <Row label="تاریخ تصمیم" value={app.decided_at ? new Date(app.decided_at).toLocaleDateString("fa-IR") : "-"} />
              </div>
              {app.face_verification && (
                <div className="mt-6">
                  <h3 className="text-sm font-semibold text-white mb-3">تطبیق چهره</h3>
                  <div className="space-y-2">
                    <Row label="شباهت" value={`${(app.face_verification.similarity * 100).toFixed(1)}%`} />
                    <Row label="کیفیت" value={`${(app.face_verification.quality_score * 100).toFixed(1)}%`} />
                    <Row label="تصمیم" value={app.face_verification.decision === "match" ? "تطبیق" : "عدم تطبیق"} />
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
        {tab === "documents" && (
          <div className="space-y-4">
            <div className="flex items-center gap-3 p-4 bg-slate-700/30 rounded-xl">
              <select value={uploadDocType} onChange={(e) => setUploadDocType(e.target.value)}
                className="px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-xl text-sm text-white focus:outline-none focus:ring-2 focus:ring-brand-500/50">
                <option value="national_id">کارت ملی</option>
                <option value="passport">گذرنامه</option>
                <option value="driver_license">گواهینامه</option>
                <option value="proof_of_address">مدرک نشانی</option>
                <option value="selfie">سلفی</option>
              </select>
              <label className={`flex-1 flex items-center justify-center gap-2 px-4 py-2.5 border-2 border-dashed rounded-xl text-sm cursor-pointer transition-all ${uploading ? "border-brand-500/30 text-brand-400" : "border-slate-600/50 text-slate-400 hover:border-brand-500/50 hover:text-brand-400"}`}>
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" /></svg>
                {uploading ? "در حال آپلود..." : "انتخاب فایل و آپلود"}
                <input type="file" className="hidden" accept="image/jpeg,image/png,application/pdf" onChange={handleUpload} disabled={uploading} />
              </label>
            </div>
            {app.documents.length === 0 ? <p className="text-slate-500 text-center py-8">مدرکی بارگذاری نشده</p> : app.documents.map((d) => (
              <div key={d.id} className="flex items-center justify-between p-4 bg-slate-700/30 rounded-xl">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-slate-600/50 flex items-center justify-center text-slate-300">
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>
                  </div>
                  <div>
                    <p className="text-sm text-white">{DOC_TYPE_MAP[d.doc_type] || d.doc_type}</p>
                    <p className="text-xs text-slate-400">{d.original_filename} | {(d.size_bytes / 1024).toFixed(0)} KB</p>
                  </div>
                </div>
                <span className={`px-3 py-1 rounded-lg text-xs font-medium ${d.status === "processed" ? "bg-emerald-400/10 text-emerald-400" : d.status === "failed" ? "bg-red-400/10 text-red-400" : "bg-slate-600/50 text-slate-300"}`}>
                  {d.status === "uploaded" ? "بارگذاری شده" : d.status === "processing" ? "در حال پردازش" : d.status === "processed" ? "پردازش شده" : d.status === "failed" ? "ناموفق" : d.status}
                </span>
              </div>
            ))}
          </div>
        )}
        {tab === "risk" && app.risk && (
          <div className="space-y-6">
            <div className="flex items-center gap-6">
              <div className="relative w-24 h-24">
                <svg className="w-24 h-24 -rotate-90" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="40" fill="none" stroke="#1e293b" strokeWidth="8" />
                  <circle cx="50" cy="50" r="40" fill="none" stroke={app.risk.level === "low" ? "#10b981" : app.risk.level === "medium" ? "#f59e0b" : app.risk.level === "high" ? "#f97316" : "#ef4444"} strokeWidth="8" strokeDasharray={`${app.risk.score * 2.51} 251`} strokeLinecap="round" />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-2xl font-bold text-white">{app.risk.score}</span>
                </div>
              </div>
              <div>
                <span className={`px-4 py-1.5 rounded-lg text-sm font-medium ${RISK_LEVEL_COLORS[app.risk.level]}`}>{RISK_LEVEL_MAP[app.risk.level]}</span>
                <p className="text-sm text-slate-400 mt-2">{app.risk.explanation}</p>
              </div>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-white mb-3">عوامل ریسک</h4>
              <div className="space-y-2">
                {app.risk.factors.map((f, i) => (
                  <div key={i} className={`flex items-center justify-between p-3 rounded-xl ${f.triggered ? "bg-red-400/5 border border-red-400/10" : "bg-slate-700/20"}`}>
                    <div className="flex items-center gap-3">
                      <div className={`w-2 h-2 rounded-full ${f.triggered ? "bg-red-400" : "bg-emerald-400"}`} />
                      <span className="text-sm text-white">{f.label}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-xs text-slate-400">{f.detail}</span>
                      {f.triggered && <span className="text-xs text-red-400 font-medium">+{f.weight}</span>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
        {tab === "screening" && (
          <div className="space-y-3">
            {app.screenings.length === 0 ? <p className="text-slate-500 text-center py-8">غربالگری انجام نشده</p> : app.screenings.map((s) => (
              <div key={s.id} className={`flex items-center justify-between p-4 rounded-xl ${s.matched ? "bg-red-400/5 border border-red-400/10" : "bg-slate-700/20"}`}>
                <div className="flex items-center gap-3">
                  <div className={`w-2.5 h-2.5 rounded-full ${s.matched ? "bg-red-400" : "bg-emerald-400"}`} />
                  <div>
                    <p className="text-sm text-white font-medium">{SCREENING_KIND_MAP[s.kind] || s.kind}</p>
                    <p className="text-xs text-slate-400">{s.list_name}</p>
                  </div>
                </div>
                <div className="text-left">
                  <span className="text-sm text-slate-300">{s.score.toFixed(1)}</span>
                  {s.matched && <span className="block text-xs text-red-400">تطبیق یافته</span>}
                </div>
              </div>
            ))}
          </div>
        )}
        {tab === "verification" && (
          <div className="space-y-4">
            {app.verifications.length === 0 ? <p className="text-slate-500 text-center py-8">احراز هویت انجام نشده</p> : app.verifications.map((v) => (
              <div key={v.id} className="p-4 bg-slate-700/20 rounded-xl">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-white font-medium">{v.kind === "ocr" ? "OCR" : v.kind}</span>
                  <span className={`px-2.5 py-1 rounded-lg text-xs ${v.status === "done" ? "bg-emerald-400/10 text-emerald-400" : "bg-slate-600/50 text-slate-300"}`}>{v.status}</span>
                </div>
                {v.score !== null && <p className="text-xs text-slate-400 mt-2">امتیاز: {(v.score * 100).toFixed(1)}%</p>}
              </div>
            ))}
          </div>
        )}
        {tab === "decisions" && (
          <div className="space-y-3">
            {app.decisions.length === 0 ? <p className="text-slate-500 text-center py-8">تصمیمی ثبت نشده</p> : app.decisions.map((d) => (
              <div key={d.id} className="p-4 bg-slate-700/20 rounded-xl">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-white font-medium">{d.code}</span>
                  <span className="text-xs text-slate-400">{d.source === "policy_engine" ? "موتور سیاست" : "بررسی‌کننده"}</span>
                </div>
                <p className="text-xs text-slate-400 mt-2">{d.reason}</p>
                {d.created_at && <p className="text-xs text-slate-500 mt-1">{new Date(d.created_at).toLocaleDateString("fa-IR")}</p>}
              </div>
            ))}
          </div>
        )}
        {tab === "timeline" && (
          <div className="space-y-0">
            {app.events.length === 0 ? <p className="text-slate-500 text-center py-8">رویدادی ثبت نشده</p> : app.events.map((e, i) => (
              <div key={e.id} className="flex gap-4 pb-6 relative">
                {i < app.events.length - 1 && <div className="absolute right-[11px] top-6 bottom-0 w-0.5 bg-slate-700" />}
                <div className="w-6 h-6 rounded-full bg-brand-600/20 border-2 border-brand-500/50 flex items-center justify-center shrink-0 mt-0.5">
                  <div className="w-2 h-2 rounded-full bg-brand-400" />
                </div>
                <div>
                  <p className="text-sm text-white">{e.message}</p>
                  <p className="text-xs text-slate-500 mt-1">{e.created_at ? new Date(e.created_at).toLocaleString("fa-IR") : ""}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between py-1.5 border-b border-slate-700/20 last:border-0">
      <span className="text-xs text-slate-400">{label}</span>
      <span className="text-sm text-white">{value}</span>
    </div>
  );
}
