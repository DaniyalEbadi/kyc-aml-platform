import type {
  User, Customer, Application, ApplicationDetail, Case, CaseDetail,
  AnalyticsData, AuditEvent, Notification, Policy, SearchResult,
  Job, RiskAssessment, ScreeningResult, Verification, FaceVerification, Document
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiClient {
  private token: string | null = null;

  setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem("token", token);
    } else {
      localStorage.removeItem("token");
    }
  }

  getToken(): string | null {
    if (!this.token) {
      this.token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    }
    return this.token;
  }

  private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const token = this.getToken();
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string> || {}),
    };
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
    if (res.status === 401) {
      this.setToken(null);
      if (typeof window !== "undefined") {
        window.location.href = "/login";
      }
      throw new Error("Unauthorized");
    }
    if (!res.ok) {
      const err = await res.json().catch(() => ({ message: "خطای سرور" }));
      throw new Error(err.message || "خطای سرور");
    }
    return res.json();
  }

  async login(email: string, password: string) {
    return this.request<{ access_token: string; refresh_token: string; user: User }>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  }

  async getMe() {
    return this.request<User>("/api/v1/auth/me");
  }

  async getCustomers(params?: Record<string, string>) {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return this.request<{ items: Customer[]; total: number }>(`/api/v1/customers${qs}`);
  }

  async getCustomer(id: string) {
    return this.request<Customer>(`/api/v1/customers/${id}`);
  }

  async createCustomer(data: { first_name: string; last_name: string; national_id?: string; birth_date?: string; gender?: string; nationality?: string; email?: string; phone?: string; province?: string; city?: string; address?: string }) {
    return this.request<Customer>("/api/v1/customers", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getApplications(params?: Record<string, string>) {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return this.request<{ items: Application[]; total: number }>(`/api/v1/applications${qs}`);
  }

  async getApplication(id: string) {
    return this.request<ApplicationDetail>(`/api/v1/applications/${id}`);
  }

  async createApplication() {
    return this.request<{ id: string; application_number: string }>("/api/v1/applications", {
      method: "POST",
      body: JSON.stringify({}),
    });
  }

  async submitApplication(id: string) {
    return this.request<{ id: string; status: string }>(`/api/v1/applications/${id}/submit`, {
      method: "POST",
    });
  }

  async getCases(params?: Record<string, string>) {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return this.request<{ items: Case[]; total: number }>(`/api/v1/cases${qs}`);
  }

  async getCase(id: string) {
    return this.request<CaseDetail>(`/api/v1/cases/${id}`);
  }

  async reviewCase(id: string, action: string, reason: string) {
    return this.request<{ message: string }>(`/api/v1/cases/${id}/review`, {
      method: "POST",
      body: JSON.stringify({ action, reason }),
    });
  }

  async getAnalytics() {
    return this.request<AnalyticsData>("/api/v1/analytics");
  }

  async getAuditEvents(params?: Record<string, string>) {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return this.request<{ items: AuditEvent[]; total: number }>(`/api/v1/audit${qs}`);
  }

  async getNotifications(params?: Record<string, string>) {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return this.request<{ items: Notification[]; total: number; unread_count: number }>(`/api/v1/notifications${qs}`);
  }

  async markNotificationsRead(ids?: string[], markAll = false) {
    return this.request<{ message: string }>("/api/v1/notifications/read", {
      method: "POST",
      body: JSON.stringify({ notification_ids: ids || [], mark_all: markAll }),
    });
  }

  async getPolicies() {
    return this.request<Policy[]>("/api/v1/policies");
  }

  async searchPolicies(query: string) {
    return this.request<unknown[]>("/api/v1/policies/search", {
      method: "POST",
      body: JSON.stringify({ query, top_k: 5 }),
    });
  }

  async globalSearch(q: string) {
    return this.request<{ results: SearchResult[]; total: number }>(`/api/v1/search?q=${encodeURIComponent(q)}`);
  }

  async getJob(id: string) {
    return this.request<Job>(`/api/v1/jobs/${id}`);
  }

  async getRiskAssessment(appId: string) {
    return this.request<RiskAssessment | null>(`/api/v1/risk/${appId}`);
  }

  async getScreeningResults(appId: string) {
    return this.request<ScreeningResult[]>(`/api/v1/screening/${appId}`);
  }

  async getVerifications(appId: string) {
    return this.request<Verification[]>(`/api/v1/verification/${appId}`);
  }

  async getFaceVerification(appId: string) {
    return this.request<FaceVerification | null>(`/api/v1/verification/face/${appId}`);
  }

  async getDocument(id: string) {
    return this.request<Document>(`/api/v1/documents/${id}`);
  }

  async getDocuments(params?: Record<string, string>) {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return this.request<Document[]>(`/api/v1/documents${qs}`);
  }

  async uploadDocument(appId: string, docType: string, file: File) {
    const formData = new FormData();
    formData.append("app_id", appId);
    formData.append("doc_type", docType);
    formData.append("file", file);
    const token = this.getToken();
    const headers: Record<string, string> = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/api/v1/documents/upload`, {
      method: "POST",
      headers,
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ message: "خطای آپلود" }));
      throw new Error(err.message || "خطای آپلود");
    }
    return res.json();
  }
}

export const api = new ApiClient();
