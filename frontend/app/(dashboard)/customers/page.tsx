"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { Customer } from "@/types";
import { RISK_LEVEL_MAP, RISK_LEVEL_COLORS, formatNumber } from "@/lib/utils";

export default function CustomersPage() {
  const router = useRouter();
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  const fetch = async (p: number, q: string) => {
    setLoading(true);
    try {
      const res = await api.getCustomers({ page: String(p), page_size: "20", search: q });
      setCustomers(res.items);
      setTotal(res.total);
    } catch {} finally { setLoading(false); }
  };

  useEffect(() => { fetch(page, search); }, [page]);

  const handleSearch = () => { setPage(1); fetch(1, search); };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">مشتریان</h1>
          <p className="text-slate-400 mt-1">{formatNumber(total)} مشتری</p>
        </div>
      </div>
      <div className="flex gap-3">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          placeholder="جستجو بر اساس نام، کد ملی، ایمیل..."
          className="flex-1 px-4 py-2.5 bg-slate-800/50 border border-slate-700/50 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500/50"
        />
        <button onClick={handleSearch} className="px-6 py-2.5 bg-brand-600 hover:bg-brand-700 text-white text-sm font-medium rounded-xl transition-all">
          جستجو
        </button>
      </div>
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-700/50">
              <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400">نام</th>
              <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400">کد ملی</th>
              <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400">ایمیل</th>
              <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400">استان</th>
              <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400">ریسک</th>
              <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400">درخواست‌ها</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={6} className="px-6 py-12 text-center text-slate-500">در حال بارگذاری...</td></tr>
            ) : customers.length === 0 ? (
              <tr><td colSpan={6} className="px-6 py-12 text-center text-slate-500">مشتری یافت نشد</td></tr>
            ) : customers.map((c) => (
              <tr key={c.id} onClick={() => router.push(`/customers/${c.id}`)} className="border-b border-slate-700/30 hover:bg-slate-700/30 cursor-pointer transition-colors">
                <td className="px-6 py-4 text-white font-medium">{c.first_name} {c.last_name}</td>
                <td className="px-6 py-4 text-slate-300 font-mono text-xs">{c.national_id || "-"}</td>
                <td className="px-6 py-4 text-slate-400 text-xs">{c.email || "-"}</td>
                <td className="px-6 py-4 text-slate-400 text-xs">{c.province || "-"}</td>
                <td className="px-6 py-4">
                  <span className={`inline-flex px-2.5 py-1 rounded-lg text-xs font-medium ${RISK_LEVEL_COLORS[c.overall_risk_level] || ""}`}>
                    {RISK_LEVEL_MAP[c.overall_risk_level] || c.overall_risk_level}
                  </span>
                </td>
                <td className="px-6 py-4 text-slate-300">{c.application_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {total > 20 && (
        <div className="flex items-center justify-center gap-2">
          <button disabled={page <= 1} onClick={() => setPage(page - 1)} className="px-3 py-1.5 text-sm bg-slate-800 border border-slate-700 rounded-lg text-slate-300 hover:bg-slate-700 disabled:opacity-40">قبلی</button>
          <span className="text-sm text-slate-400">صفحه {page} از {Math.ceil(total / 20)}</span>
          <button disabled={page >= Math.ceil(total / 20)} onClick={() => setPage(page + 1)} className="px-3 py-1.5 text-sm bg-slate-800 border border-slate-700 rounded-lg text-slate-300 hover:bg-slate-700 disabled:opacity-40">بعدی</button>
        </div>
      )}
    </div>
  );
}
