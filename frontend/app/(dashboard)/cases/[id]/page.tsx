"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { CaseDetail } from "@/types";
import { STATUS_MAP, RISK_LEVEL_MAP, RISK_LEVEL_COLORS, PRIORITY_MAP, ACTION_MAP, formatNumber } from "@/lib/utils";

export default function CaseDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [caseData, setCaseData] = useState<CaseDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [showReview, setShowReview] = useState(false);
  const [reviewAction, setReviewAction] = useState("approve");
  const [reviewReason, setReviewReason] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (params.id) api.getCase(params.id as string).then(setCaseData).catch(() => {}).finally(() => setLoading(false));
  }, [params.id]);

  const handleReview = async () => {
    if (!caseData) return;
    setSubmitting(true);
    try {
      await api.reviewCase(caseData.id, reviewAction, reviewReason);
      const updated = await api.getCase(caseData.id);
      setCaseData(updated);
      setShowReview(false);
      setReviewReason("");
    } catch {} finally { setSubmitting(false); }
  };

  if (loading) return <div className="flex items-center justify-center h-96"><div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" /></div>;
  if (!caseData) return <div className="text-center text-slate-400 py-20">پرونده یافت نشد</div>;

  const PRIORITY_COLORS: Record<string, string> = {
    low: "text-slate-400 bg-slate-400/10", normal: "text-blue-400 bg-blue-400/10",
    high: "text-amber-400 bg-amber-400/10", critical: "text-red-400 bg-red-400/10",
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <button onClick={() => router.back()} className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
        </button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-white">{caseData.case_number}</h1>
          <p className="text-slate-400 mt-1">{caseData.customer_name} | {caseData.application_number}</p>
        </div>
        <div className="flex gap-2">
          <span className={`px-3 py-1.5 rounded-xl text-xs font-medium ${RISK_LEVEL_COLORS[caseData.risk_level] || ""}`}>{RISK_LEVEL_MAP[caseData.risk_level] || caseData.risk_level}</span>
          <span className={`px-3 py-1.5 rounded-xl text-xs font-medium ${PRIORITY_COLORS[caseData.priority] || ""}`}>{PRIORITY_MAP[caseData.priority] || caseData.priority}</span>
          <span className="px-3 py-1.5 rounded-xl text-xs font-medium bg-slate-700/50 text-slate-300">{STATUS_MAP[caseData.status] || caseData.status}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6">
          <h3 className="text-sm font-semibold text-white mb-4">اطلاعات پرونده</h3>
          <div className="space-y-2">
            <Row label="شماره پرونده" value={caseData.case_number} />
            <Row label="مشتری" value={caseData.customer_name} />
            <Row label="درخواست" value={caseData.application_number} />
            <Row label="وضعیت" value={STATUS_MAP[caseData.status] || caseData.status} />
            <Row label="اولویت" value={PRIORITY_MAP[caseData.priority] || caseData.priority} />
            <Row label="SLA (ساعت)" value={String(caseData.sla_hours)} />
            {caseData.sla_due_at && <Row label="مهلت" value={new Date(caseData.sla_due_at).toLocaleDateString("fa-IR")} />}
            {caseData.decision && <Row label="تصمیم" value={ACTION_MAP[caseData.decision] || caseData.decision} />}
            {caseData.decision_reason && <Row label="دلیل" value={caseData.decision_reason} />}
          </div>
        </div>

        <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-white">بررسی‌ها ({caseData.reviews.length})</h3>
            {caseData.status !== "closed" && (
              <button onClick={() => setShowReview(true)} className="px-3 py-1.5 bg-brand-600 hover:bg-brand-700 text-white text-xs font-medium rounded-lg transition-all">
                بررسی
              </button>
            )}
          </div>
          <div className="space-y-3 max-h-80 overflow-y-auto">
            {caseData.reviews.length === 0 ? <p className="text-slate-500 text-sm text-center py-4">بررسی ثبت نشده</p> :
              caseData.reviews.map((r) => (
                <div key={r.id} className="p-3 bg-slate-700/20 rounded-xl">
                  <div className="flex items-center justify-between">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${r.action === "approve" ? "bg-emerald-400/10 text-emerald-400" : r.action === "reject" ? "bg-red-400/10 text-red-400" : "bg-slate-600/50 text-slate-300"}`}>
                      {ACTION_MAP[r.action] || r.action}
                    </span>
                    <span className="text-xs text-slate-500">{r.created_at ? new Date(r.created_at).toLocaleDateString("fa-IR") : ""}</span>
                  </div>
                  <p className="text-xs text-slate-400 mt-2">{r.reason}</p>
                </div>
              ))
            }
          </div>
        </div>

        <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6">
          <h3 className="text-sm font-semibold text-white mb-4">تاریخچه اختصاص</h3>
          <div className="space-y-3">
            {caseData.assignments.map((a) => (
              <div key={a.id} className="p-3 bg-slate-700/20 rounded-xl">
                <p className="text-xs text-slate-400">اختصاص به: {a.user_id.slice(0, 8)}...</p>
                <p className="text-xs text-slate-500 mt-1">{a.created_at ? new Date(a.created_at).toLocaleDateString("fa-IR") : ""}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Review Modal */}
      {showReview && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={() => setShowReview(false)}>
          <div className="bg-slate-800 border border-slate-700 rounded-2xl p-6 w-full max-w-md" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-lg font-bold text-white mb-4">بررسی پرونده</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-slate-300 mb-2">عملیات</label>
                <select value={reviewAction} onChange={(e) => setReviewAction(e.target.value)}
                  className="w-full px-4 py-2.5 bg-slate-700/50 border border-slate-600/50 rounded-xl text-sm text-white">
                  <option value="approve">تأیید</option>
                  <option value="reject">رد</option>
                  <option value="resubmit">ارسال مجدد</option>
                  <option value="escalate">ارجاع</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-slate-300 mb-2">دلیل</label>
                <textarea value={reviewReason} onChange={(e) => setReviewReason(e.target.value)} rows={3}
                  className="w-full px-4 py-2.5 bg-slate-700/50 border border-slate-600/50 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500/50"
                  placeholder="دلیل بررسی..." />
              </div>
              <div className="flex gap-3">
                <button onClick={handleReview} disabled={submitting || !reviewReason}
                  className="flex-1 py-2.5 bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white text-sm font-medium rounded-xl transition-all">
                  {submitting ? "در حال ارسال..." : "ثبت"}
                </button>
                <button onClick={() => setShowReview(false)} className="px-6 py-2.5 bg-slate-700 hover:bg-slate-600 text-white text-sm font-medium rounded-xl transition-all">لغو</button>
              </div>
            </div>
          </div>
        </div>
      )}
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