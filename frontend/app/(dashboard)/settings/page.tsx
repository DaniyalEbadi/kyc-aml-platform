"use client";
import { useState } from "react";
import { useAuth } from "@/lib/hooks";

export default function SettingsPage() {
  const { logout } = useAuth();
  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold text-white">تنظیمات</h1>
        <p className="text-slate-400 mt-1">مدیریت حساب کاربری</p>
      </div>
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6">
        <button onClick={logout} className="px-6 py-2.5 bg-red-600 hover:bg-red-700 text-white rounded-xl">
          خروج
        </button>
      </div>
    </div>
  );
}