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
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({ first_name: "", last_name: "", national_id: "", birth_date: "", gender: "", email: "", phone: "", province: "", city: "" });
  const [error, setError] = useState("");

  const fetchData = async (p: number, q: string) => {
    setLoading(true);
    try {
      const res = await api.getCustomers({ page: String(p), page_size: "20", search: q });
      setCustomers(res.items);
      setTotal(res.total);
    } catch {} finally { setLoading(false); }
  };

  useEffect(() => { fetchData(page, search); }, [page]);

  const handleSearch = () => { setPage(1); fetchData(1, search); };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.first_name || !form.last_name) { setError("نام و نام خانوادگی الزامی است"); return; }
    setCreating(true);
    setError("");
    try {
      const customer = await api.createCustomer({
        first_name: form.first_name,
        last_name: form.last_name,
        national_id: form.national_id || undefined,
        birth_date: form.birth_date || undefined,
        gender: form.gender || undefined,
        email: form.email || undefined,
        phone: form.phone || undefined,
        province: form.province || undefined,
        city: form.city || undefined,
      });
      setShowCreate(false);
      setForm({ first_name: "", last_name: "", national_id: "", birth_date: "", gender: "", email: "", phone: "", province: "", city: "" });
      router.push(`/customers/${customer.id}`);
    } catch (err: any) {
      setError(err.message || "خطا در ایجاد مشتری");
    } finally { setCreating(false); }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">مشتریان</h1>
          <p className="text-slate-400 mt-1">{formatNumber(total)} مشتری</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="px-4 py-2.5 bg-brand-600 hover:bg-brand-700 text-white text-sm font-medium rounded-xl transition-all flex items-center gap-2">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
          مشتری جدید
        </button>
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

      {/* Create Customer Modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" onClick={() => setShowCreate(false)}>
          <div className="bg-slate-800 border border-slate-700 rounded-2xl w-full max-w-lg p-6" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-bold text-white">مشتری جدید</h2>
              <button onClick={() => setShowCreate(false)} className="text-slate-400 hover:text-white">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
              </button>
            </div>
            <form onSubmit={handleCreate} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">نام *</label>
                  <input type="text" value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500/50" placeholder="نام" required />
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">نام خانوادگی *</label>
                  <input type="text" value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500/50" placeholder="نام خانوادگی" required />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">کد ملی</label>
                  <input type="text" value={form.national_id} onChange={(e) => setForm({ ...form, national_id: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500/50" placeholder="۱۰ رقم" maxLength={10} dir="ltr" />
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">تاریخ تولد</label>
                  <input type="text" value={form.birth_date} onChange={(e) => setForm({ ...form, birth_date: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500/50" placeholder="1990-01-15" dir="ltr" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">جنسیت</label>
                  <select value={form.gender} onChange={(e) => setForm({ ...form, gender: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-xl text-sm text-white focus:outline-none focus:ring-2 focus:ring-brand-500/50">
                    <option value="">انتخاب...</option>
                    <option value="male">مرد</option>
                    <option value="female">زن</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">استان</label>
                  <input type="text" value={form.province} onChange={(e) => setForm({ ...form, province: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500/50" placeholder="تهران" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">ایمیل</label>
                  <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500/50" placeholder="email@example.com" dir="ltr" />
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">تلفن</label>
                  <input type="text" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-700/50 border border-slate-600/50 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500/50" placeholder="0912..." dir="ltr" />
                </div>
              </div>
              {error && <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm">{error}</div>}
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowCreate(false)} className="flex-1 py-2.5 bg-slate-700 hover:bg-slate-600 text-white text-sm font-medium rounded-xl transition-all">انصراف</button>
                <button type="submit" disabled={creating} className="flex-1 py-2.5 bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white text-sm font-medium rounded-xl transition-all">{creating ? "در حال ایجاد..." : "ایجاد مشتری"}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
