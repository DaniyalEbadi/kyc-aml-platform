import type { Metadata } from "next";
import { Vazirmatn } from "next/font/google";
import "./globals.css";

const vazir = Vazirmatn({
  subsets: ["arabic"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
  variable: "--font-vazir",
});

export const metadata: Metadata = {
  title: "پارس‌هویت | سامانه احراز هویت و انطباق",
  description: "سامانه جامع احراز هویت، مبارزه با پولشویی و مدیریت ریسک",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fa" dir="rtl" suppressHydrationWarning>
      <body className={`${vazir.variable} antialiased`} style={{ fontFamily: "var(--font-vazir), system-ui, sans-serif" }}>
        {children}
      </body>
    </html>
  );
}
