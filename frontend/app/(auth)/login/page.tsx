"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await api.login(email, password);
      localStorage.setItem("token", res.access_token);
      localStorage.setItem("user", JSON.stringify(res.user));
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "خطای ورود");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="w-full max-w-md p-8">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-brand-600/20 border border-brand-500/30 mb-4">
            <svg className="w-8 h-8 text-brand-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-white">پارس‌هویت</h1>
          <p className="text-slate-400 mt-2">سامانه احراز هویت و انطباق</p>
        </div>
        <div className="bg-slate-800/50 backdrop-blur-xl border border-slate-700/50 rounded-2xl p-8">
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">ایمیل</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600/50 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition-all"
                placeholder="email@example.com"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">گذرواژه</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600/50 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition-all"
                placeholder="••••••••"
                required
              />
            </div>
            {error && (
              <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm">{error}</div>
            )}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white font-medium rounded-xl transition-all duration-200 shadow-lg shadow-brand-600/25"
            >
              {loading ? "در حال ورود..." : "ورود"}
            </button>
          </form>
          <div className="mt-6 p-4 bg-slate-700/30 rounded-xl">
            <p className="text-xs text-slate-400 mb-2">حساب‌های نمونه:</p>
            <div className="space-y-1 text-xs text-slate-500">
              <p>admin@parsheid.ir / admin123</p>
              <p>analyst@parsheid.ir / analyst123</p>
              <p>reviewer@parsheid.ir / reviewer123</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
