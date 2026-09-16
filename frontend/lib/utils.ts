import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const persianDigits = ["۰", "۱", "۲", "۳", "۴", "۵", "۶", "۷", "۸", "۹"];

export function toPersianDigits(num: number | string): string {
  return String(num).replace(/\d/g, (d) => persianDigits[parseInt(d)]);
}

export function formatNumber(num: number): string {
  return new Intl.NumberFormat("fa-IR").format(num);
}

export const STATUS_MAP: Record<string, string> = {
  draft: "پیش‌نویس",
  submitted: "ارسال‌شده",
  processing: "در حال پردازش",
  needs_resubmission: "نیاز به ارسال مجدد",
  in_review: "در انتظار بررسی",
  approved: "تأیید شده",
  rejected: "رد شده",
  escalated: "ارجاع‌شده",
  open: "باز",
  assigned: "اختصاص‌یافته",
  waiting_customer: "در انتظار مشتری",
  closed: "بسته‌شده",
};

export const RISK_LEVEL_MAP: Record<string, string> = {
  low: "ریسک پایین",
  medium: "ریسک متوسط",
  high: "ریسک بالا",
  critical: "ریسک بحرانی",
};

export const RISK_LEVEL_COLORS: Record<string, string> = {
  low: "text-emerald-400 bg-emerald-400/10",
  medium: "text-amber-400 bg-amber-400/10",
  high: "text-orange-400 bg-orange-400/10",
  critical: "text-red-400 bg-red-400/10",
};

export const PRIORITY_MAP: Record<string, string> = {
  low: "کم",
  normal: "عادی",
  high: "زیاد",
  critical: "بحرانی",
};

export const DOC_TYPE_MAP: Record<string, string> = {
  passport: "گذرنامه",
  national_id: "کارت ملی",
  driver_license: "گواهینامه",
  residence: "مدرک اقامت",
  proof_of_address: "مدرک نشانی",
  business: "مدارک کسب‌وکار",
  selfie: "سلفی",
};

export const SCREENING_KIND_MAP: Record<string, string> = {
  sanctions: "تحریم‌ها",
  pep: "اشخاص سیاسی",
  adverse_media: "رسانه نامطلوب",
  watchlist: "فهرست مراقبت",
};

export const ACTION_MAP: Record<string, string> = {
  approve: "تأیید",
  reject: "رد",
  resubmit: "ارسال مجدد",
  escalate: "ارجاع",
};
