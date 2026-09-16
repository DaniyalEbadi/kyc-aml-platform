"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { Document } from "@/types";
import { DOC_TYPE_MAP, formatNumber } from "@/lib/utils";

export default function DocumentsPage() {
  const router = useRouter();
  const [docs, setDocs] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getDocuments?.().then(setDocs).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const STATUS_MAP: Record<string, string> = {
    uploaded: "بارگذاری شده", processing: "در حال پردازش", processed: "پردازش شده", failed: "ناموفق", rejected: "رد شده",
  };
  const STATUS_COLORS: Record<string, string> = {
    uploaded: "text-slate-400 bg-slate-400/10", processing: "text-brand-400 bg-brand-400/10",
    processed: "text-emerald-400 bg-emerald-400/10", failed: "text-red-400 bg-red-400/10", rejected: "text-amber-400 bg-amber-400/10",
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">مدارک</h1>
        <p className="text-slate-400 mt-1">{docs.length} مدرک</p>
      </div>
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-700/50">
              <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400">نوع</th>
              <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400">فایل</th>
              <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400">حجم</th>
              <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400">وضعیت</th>
              <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400">درخواست</th>
              <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400">تاریخ</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={6} className="px-6 py-12 text-center text-slate-500">در حال بارگذاری...</td></tr>
            ) : docs.length === 0 ? (
              <tr><td colSpan={6} className="px-6 py-12 text-center text-slate-500">مدرکی یافت نشد</td></tr>
            ) : docs.map((d) => (
              <tr key={d.id} className="border-b border-slate-700/30 hover:bg-slate-700/30 transition-colors">
                <td className="px-6 py-4">
                  <span className={`px-2.5 py-1 rounded-lg text-xs font-medium ${STATUS_COLORS[d.status] || ""}`}>
                    {DOC_TYPE_MAP[d.doc_type] || d.doc_type}
                  </span>
                </td>
                <td className="px-6 py-4 text-white font-medium text-sm">{d.original_filename}</td>
                <td className="px-6 py-4 text-slate-400 text-xs">{(d.size_bytes / 1024).toFixed(0)} KB</td>
                <td className="px-6 py-4">
                  <span className={`px-2.5 py-1 rounded-lg text-xs font-medium ${STATUS_COLORS[d.status] || ""}`}>
                    {STATUS_MAP[d.status] || d.status}
                  </span>
                </td>
                <td className="px-6 py-4 text-slate-400 text-xs">{d.application_id.slice(0, 8)}...</td>
                <td className="px-6 py-4 text-slate-400 text-xs">{d.created_at ? new Date(d.created_at).toLocaleDateString("fa-IR") : "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}