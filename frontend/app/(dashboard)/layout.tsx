"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Sidebar } from "@/components/navigation/sidebar";
import { Header } from "@/components/navigation/header";
import { api } from "@/lib/api";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const token = api.getToken();
    if (!token) {
      router.push("/login");
    } else {
      setChecking(false);
    }
  }, [router]);

  if (checking) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950">
        <div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950">
      <Sidebar />
      <div className="mr-64">
        <Header />
        <main className="p-6">{children}</main>
      </div>
    </div>
  );
}
