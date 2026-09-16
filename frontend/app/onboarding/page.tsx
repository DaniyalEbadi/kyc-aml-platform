"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/hooks";

const STEPS = [
  { key: "personal", label: "۱. اطلاعات شخصی", fields: ["first_name", "last_name", "national_id", "birth_date", "gender"] },
  { key: "contact", label: "۲. اطلاعات تماس", fields: ["phone", "email", "province", "city", "address"] },
  { key: "id_upload", label: "۳. بارگذاری مدرک هویتی", fields: ["id_document"] },
  { key: "quality", label: "۴. بررسی کیفیت مدرک", fields: [] },
  { key: "extraction", label: "۵. استخراج اطلاعات", fields: [] },
  { key: "confirm_fields", label: "۶. تأیید اطلاعات استخراج‌شده", fields: [] },
  { key: "selfie", label: "۷. سلفی / تطبیق چهره", fields: [] },
  { key: "additional", label: "۸. اطلاعات تکمیلی", fields: ["occupation", "declared_income", "source_of_funds", "expected_volume"] },
  { key: "review", label: "۹. بررسی نهایی", fields: [] },
  { key: "submit", label: "۱۰. ارسال درخواست", fields: [] },
];

export default function OnboardingPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [stepIndex, setStepIndex] = useState(0);
  const [formData, setFormData] = useState<Record<string, any>>({});
  const [appId, setAppId] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const currentStep = STEPS[stepIndex];
  const progress = ((stepIndex + 1) / STEPS.length) * 100;

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleNext = async () => {
    if (stepIndex === 0 && !appId) {
      setSubmitting(true);
      try {
        const res = await api.createApplication();
        setAppId(res.id);
      } catch (err: any) {
        setError(err.message);
        setSubmitting(false);
        return;
      }
    }
    if (stepIndex === STEPS.length - 1) {
      await handleSubmit();
      return;
    }
    setSubmitting(false);
    setStepIndex(prev => Math.min(prev + 1, STEPS.length - 1));
  };

  const handleBack = () => {
    setStepIndex(prev => Math.max(prev - 1, 0));
  };

  const handleSubmit = async () => {
    if (!appId) return;
    setSubmitting(true);
    try {
      await api.submitApplication(appId);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950">
      <div className="max-w-3xl mx-auto px-4 py-8">
        {/* Progress */}
        <div className="mb-8">
          <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
            <div className="h-full bg-brand-500 rounded-full transition-all duration-500" style={{ width: `${progress}%` }} />
          </div>
          <div className="flex justify-between mt-3 text-xs text-slate-400">
            {STEPS.map((s, i) => (
              <span key={s.key} className={i === stepIndex ? "text-brand-400 font-medium" : ""}>{s.label}</span>
            ))}
          </div>
        </div>

        {/* Step Content */}
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-8">
          <h2 className="text-xl font-bold text-white mb-2">{currentStep.label}</h2>
          <p className="text-slate-400 mb-6">مرحله {stepIndex + 1} از {STEPS.length}</p>

          {error && <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm">{error}</div>}

          {stepIndex === 0 && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <Input label="نام" value={formData.first_name} onChange={handleInputChange} name="first_name" required />
                <Input label="نام خانوادگی" value={formData.last_name} onChange={handleInputChange} name="last_name" required />
              </div>
              <Input label="کد ملی" value={formData.national_id} onChange={handleInputChange} name="national_id" type="text" maxLength={10} required />
              <div className="grid grid-cols-2 gap-4">
                <Input label="تاریخ تولد (شمسی)" value={formData.birth_date} onChange={handleInputChange} name="birth_date" type="text" placeholder="۱۳۷۰/۰۱/۰۱" required />
                <select value={formData.gender} onChange={(e) => handleInputChange("gender", e.target.value)} className="w-full px-4 py-2.5 bg-slate-700/50 border border-slate-600/50 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-brand-500/50" required>
                  <option value="">جنسیت</option>
                  <option value="مرد">مرد</option>
                  <option value="زن">زن</option>
                </select>
              </div>
            </div>
          )}

          {stepIndex === 1 && (
            <div className="space-y-4">
              <Input label="تلفن" value={formData.phone} onChange={handleInputChange} name="phone" type="tel" placeholder="۰۹۱۲۳۴۵۶۷۸۹" required />
              <Input label="ایمیل" value={formData.email} onChange={handleInputChange} name="email" type="email" required />
              <div className="grid grid-cols-2 gap-4">
                <Input label="استان" value={formData.province} onChange={handleInputChange} name="province" required />
                <Input label="شهر" value={formData.city} onChange={handleInputChange} name="city" required />
              </div>
              <div>
                <label className="block text-sm text-slate-300 mb-2">آدرس کامل</label>
                <textarea value={formData.address} onChange={(e) => handleInputChange("address", e.target.value)} rows={3}
                  className="w-full px-4 py-2.5 bg-slate-700/50 border border-slate-600/50 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500/50" required />
              </div>
            </div>
          )}

          {stepIndex === 2 && (
            <div className="space-y-4">
              <p className="text-slate-400">بارگذاری کارت ملی یا پاسپورت</p>
              <div className="border-2 border-dashed border-slate-700 rounded-xl p-8 text-center hover:border-brand-500/50 transition-colors">
                <input type="file" accept="image/*,.pdf" className="hidden" id="id-doc" onChange={async (e) => { const file = e.target.files?.[0]; if (file) { const formData = new FormData(); formData.append("file", file); formData.append("doc_type", "national_id"); formData.append("app_id", appId || ""); /* upload */ } }} />
                <label htmlFor="id-doc" className="cursor-pointer">
                  <svg className="w-12 h-12 mx-auto text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  <p className="mt-2 text-slate-300">فایل را بکشید یا کلیک کنید</p>
                  <p className="text-xs text-slate-500 mt-1">JPG, PNG, PDF - حداکثر ۱۲ مگابایت</p>
                </label>
              </div>
            </div>
          )}

          {stepIndex === 3 && (
            <div className="text-center py-8">
              <svg className="w-16 h-16 mx-auto text-brand-500 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="mt-4 text-slate-300">بررسی کیفیت تصویر در حال انجام...</p>
              <p className="text-slate-500 text-sm mt-2">لطفاً صبر کنید</p>
            </div>
          )}

          {stepIndex === 4 && (
            <div className="text-center py-8">
              <svg className="w-16 h-16 mx-auto text-blue-500 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <p className="mt-4 text-slate-300">استخراج اطلاعات از مدرک...</p>
            </div>
          )}

          {stepIndex === 5 && (
            <div className="space-y-4">
              <p className="text-slate-400">اطلاعات استخراج‌شده را بررسی و تأیید کنید</p>
              <div className="grid grid-cols-2 gap-4">
                {["first_name", "last_name", "national_id", "birth_date", "expiry_date"].map((field) => (
                  <div key={field} className="p-3 bg-slate-700/30 rounded-xl">
                    <label className="text-xs text-slate-400">{field}</label>
                    <input type="text" value={formData[field] || ""} onChange={(e) => handleInputChange(field, e.target.value)}
                      className="w-full mt-1 px-3 py-2 bg-slate-600/50 border border-slate-500/50 rounded-lg text-white" />
                  </div>
                ))}
              </div>
            </div>
          )}

          {stepIndex === 6 && (
            <div className="space-y-4">
              <p className="text-slate-400">بارگذاری سلفی برای تطبیق چهره</p>
              <div className="border-2 border-dashed border-slate-700 rounded-xl p-8 text-center hover:border-brand-500/50 transition-colors">
                <input type="file" accept="image/*" className="hidden" id="selfie-doc" />
                <label htmlFor="selfie-doc" className="cursor-pointer">
                  <svg className="w-12 h-12 mx-auto text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  <p className="mt-2 text-slate-300">سلفی را بارگذاری کنید</p>
                </label>
              </div>
            </div>
          )}

          {stepIndex === 7 && (
            <div className="space-y-4">
              <Input label="شغل" value={formData.occupation} onChange={handleInputChange} name="occupation" />
              <Input label="درآمد اعلامی" value={formData.declared_income} onChange={handleInputChange} name="declared_income" />
              <Input label="منبع وجوه" value={formData.source_of_funds} onChange={handleInputChange} name="source_of_funds" />
              <select value={formData.expected_volume} onChange={(e) => handleInputChange("expected_volume", e.target.value)} className="w-full px-4 py-2.5 bg-slate-700/50 border border-slate-600/50 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-brand-500/50">
                <option value="">حجم تراکنش مورد انتظار</option>
                <option value="پایین">پایین</option>
                <option value="متوسط">متوسط</option>
                <option value="بالا">بالا</option>
              </select>
            </div>
          )}

          {stepIndex === 8 && (
            <div className="space-y-4">
              <p className="text-slate-400">مجموعه اطلاعات را بررسی کنید</p>
              <div className="space-y-2">
                {Object.entries(formData).map(([k, v]) => (
                  <div key={k} className="flex justify-between py-2 border-b border-slate-700/30">
                    <span className="text-slate-400">{k}</span>
                    <span className="text-white">{String(v)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {stepIndex === 9 && (
            <div className="text-center py-8">
              <svg className="w-16 h-16 mx-auto text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <h3 className="mt-4 text-lg font-semibold text-white">درخواست شما آماده ارسال است</h3>
              <p className="text-slate-400 mt-2">با کلیک روی ارسال، درخواست برای بررسی ارسال می‌شود.</p>
            </div>
          )}

          {/* Navigation */}
          <div className="flex justify-between mt-8 pt-6 border-t border-slate-700/30">
            {stepIndex > 0 && (
              <button onClick={handleBack} className="px-6 py-2.5 bg-slate-700 hover:bg-slate-600 text-white text-sm font-medium rounded-xl transition-all">
                بازگشت
              </button>
            )}
            <button onClick={handleNext} disabled={submitting} className="px-6 py-2.5 bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white text-sm font-medium rounded-xl transition-all">
              {submitting ? "در حال پردازش..." : stepIndex === STEPS.length - 1 ? "ارسال نهایی" : "ادامه"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function Input({ label, value, onChange, name, type = "text", required, maxLength, placeholder }: any) {
  return (
    <div>
      <label className="block text-sm text-slate-300 mb-2">{label}{required && <span className="text-red-400 ml-1">*</span>}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(name, e.target.value)}
        maxLength={maxLength}
        placeholder={placeholder}
        className="w-full px-4 py-2.5 bg-slate-700/50 border border-slate-600/50 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-brand-500/50"
        required={required}
      />
    </div>
  );
}