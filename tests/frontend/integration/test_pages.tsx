"""
Frontend integration tests for pages and API client
"""
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { ReactNode } from 'react';

// Test wrapper
const createTestWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/']}>
        <Routes>
          <Route path="/*" element={children} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
};

// Mock API
jest.mock('@/lib/api', () => ({
  api: {
    getAnalytics: jest.fn(),
    getCustomers: jest.fn(),
    getApplications: jest.fn(),
    getApplication: jest.fn(),
    getCases: jest.fn(),
    getCase: jest.fn(),
    getPolicies: jest.fn(),
    getAuditEvents: jest.fn(),
    getNotifications: jest.fn(),
    markNotificationsRead: jest.fn(),
    getDocuments: jest.fn(),
    getRiskAssessment: jest.fn(),
    getScreeningResults: jest.fn(),
    getVerifications: jest.fn(),
    getFaceVerification: jest.fn(),
    globalSearch: jest.fn(),
  },
}));

import { api } from '@/lib/api';

// Import pages
import DashboardPage from '@/app/(dashboard)/dashboard/page';
import CustomersPage from '@/app/(dashboard)/customers/page';
import ApplicationsPage from '@/app/(dashboard)/applications/page';
import CasesPage from '@/app/(dashboard)/cases/page';
import AnalyticsPage from '@/app/(dashboard)/analytics/page';
import AuditPage from '@/app/(dashboard)/audit/page';
import PoliciesPage from '@/app/(dashboard)/policies/page';
import NotificationsPage from '@/app/(dashboard)/notifications/page';

describe('Dashboard Page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    api.getAnalytics.mockResolvedValue({
      kpis: {
        total_applications: 100,
        new_applications: 10,
        approved_count: 60,
        rejected_count: 10,
        in_review_count: 20,
        approval_rate: 60,
        rejection_rate: 10,
        human_review_rate: 20,
        avg_processing_hours: 24,
        avg_review_hours: 48,
        high_risk_count: 15,
        critical_count: 5,
        total_customers: 80,
        total_cases: 25,
        open_cases: 20,
      },
      applications_over_time: Array(30).fill(0).map((_, i) => ({
        date: new Date(Date.now() - (29 - i) * 86400000).toISOString().split('T')[0],
        value: Math.floor(Math.random() * 5),
      })),
      risk_distribution: [
        { label: 'low', value: 40 },
        { label: 'medium', value: 30 },
        { label: 'high', value: 20 },
        { label: 'critical', value: 10 },
      ],
      verification_funnel: [
        { step: 'درخواست', count: 100, percentage: 100 },
        { step: 'مدارک', count: 80, percentage: 80 },
        { step: 'OCR', count: 75, percentage: 75 },
        { step: 'چهره', count: 70, percentage: 70 },
        { step: 'ریسک', count: 65, percentage: 65 },
        { step: 'بررسی', count: 20, percentage: 20 },
        { step: 'تأیید', count: 60, percentage: 60 },
      ],
      document_type_distribution: [
        { label: 'passport', value: 20 },
        { label: 'national_id', value: 50 },
        { label: 'driver_license', value: 10 },
        { label: 'proof_of_address', value: 15 },
        { label: 'selfie', value: 5 },
      ],
      status_distribution: [
        { label: 'draft', value: 10 },
        { label: 'submitted', value: 20 },
        { label: 'processing', value: 5 },
        { label: 'in_review', value: 15 },
        { label: 'approved', value: 40 },
        { label: 'rejected', value: 5 },
        { label: 'needs_resubmission', value: 3 },
        { label: 'escalated', value: 2 },
      ],
    });
    api.getNotifications.mockResolvedValue({ items: [], total: 0, unread_count: 0 });
  });

  it('should render dashboard with KPIs', async () => {
    render(<DashboardPage />, { wrapper: createTestWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('داشبورد')).toBeInTheDocument();
      expect(screen.getByText('۱۰۰')).toBeInTheDocument(); // total applications
      expect(screen.getByText('۶۰')).toBeInTheDocument(); // approved
    });
  });

  it('should display charts', async () => {
    render(<DashboardPage />, { wrapper: createTestWrapper() });
    
    await waitFor(() => {
      // Charts should be rendered
      expect(screen.getByText('روند درخواست‌ها (۳۰ روز اخیر)')).toBeInTheDocument();
      expect(screen.getByText('توزیع ریسک')).toBeInTheDocument();
    });
  });

  it('should show verification funnel', async () => {
    render(<DashboardPage />, { wrapper: createTestWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('قیف احراز هویت')).toBeInTheDocument();
      expect(screen.getByText('درخواست')).toBeInTheDocument();
      expect(screen.getByText('تأیید')).toBeInTheDocument();
    });
  });
});

describe('Customers Page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    api.getCustomers.mockResolvedValue({
      items: [
        { id: '1', first_name: 'محمد', last_name: 'احمدی', national_id: '0012345679', email: 'm@test.com', phone: '09123456789', province: 'تهران', city: 'تهران', overall_risk_level: 'low', overall_risk_score: 15, application_count: 2, created_at: '2024-01-01T00:00:00Z' },
        { id: '2', first_name: 'علی', last_name: 'رضایی', national_id: '0012345678', email: 'a@test.com', phone: '09123456788', province: 'اصفهان', city: 'اصفهان', overall_risk_level: 'medium', overall_risk_score: 45, application_count: 1, created_at: '2024-01-02T00:00:00Z' },
      ],
      total: 2,
      page: 1,
      page_size: 20,
    });
  });

  it('should render customers table', async () => {
    render(<CustomersPage />, { wrapper: createTestWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('مشتریان')).toBeInTheDocument();
      expect(screen.getByText('محمد احمدی')).toBeInTheDocument();
      expect(screen.getByText('علی رضایی')).toBeInTheDocument();
    });
  });

  it('should show risk badges', async () => {
    render(<CustomersPage />, { wrapper: createTestWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('ریسک پایین')).toBeInTheDocument();
      expect(screen.getByText('ریسک متوسط')).toBeInTheDocument();
    });
  });

  it('should handle search', async () => {
    render(<CustomersPage />, { wrapper: createTestWrapper() });
    
    const searchInput = screen.getByPlaceholderText(/جستجو/);
    fireEvent.change(searchInput, { target: { value: 'محمد' } });
    fireEvent.keyDown(searchInput, { key: 'Enter' });
    
    await waitFor(() => {
      expect(api.getCustomers).toHaveBeenCalledWith(
        expect.objectContaining({ search: 'محمد', page: '1' })
      );
    });
  });

  it('should handle pagination', async () => {
    api.getCustomers.mockResolvedValue({
      items: [],
      total: 50,
      page: 2,
      page_size: 20,
    });
    
    render(<CustomersPage />, { wrapper: createTestWrapper() });
    
    await waitFor(() => {
      const nextButton = screen.getByText('بعدی');
      fireEvent.click(nextButton);
      
      expect(api.getCustomers).toHaveBeenCalledWith(
        expect.objectContaining({ page: '2' })
      );
    });
  });
});

describe('Applications Page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    api.getApplications.mockResolvedValue({
      items: [
        { id: '1', application_number: 'APP-1001', customer_name: 'محمد احمدی', status: 'submitted', risk_level: 'low', risk_score: 20, source: 'web', created_at: '2024-01-01T00:00:00Z' },
        { id: '2', application_number: 'APP-1002', customer_name: 'علی رضایی', status: 'in_review', risk_level: 'high', risk_score: 70, source: 'mobile', created_at: '2024-01-02T00:00:00Z' },
      ],
      total: 2,
      page: 1,
      page_size: 20,
    });
  });

  it('should render applications table', async () => {
    render(<ApplicationsPage />, { wrapper: createTestWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('درخواست‌ها')).toBeInTheDocument();
      expect(screen.getByText('APP-1001')).toBeInTheDocument();
      expect(screen.getByText('APP-1002')).toBeInTheDocument();
    });
  });

  it('should show status badges', async () => {
    render(<ApplicationsPage />, { wrapper: createTestWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('ارسال‌شده')).toBeInTheDocument();
      expect(screen.getByText('در انتظار بررسی')).toBeInTheDocument();
    });
  });

  it('should filter by status', async () => {
    render(<ApplicationsPage />, { wrapper: createTestWrapper() });
    
    const statusSelect = screen.getByRole('combobox');
    fireEvent.change(statusSelect, { target: { value: 'submitted' } });
    
    await waitFor(() => {
      expect(api.getApplications).toHaveBeenCalledWith(
        expect.objectContaining({ status: 'submitted' })
      );
    });
  });
});

describe('Cases Page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    api.getCases.mockResolvedValue({
      items: [
        { id: '1', case_number: 'CASE-00001', customer_name: 'محمد احمدی', application_number: 'APP-1001', status: 'open', priority: 'high', risk_level: 'high', sla_hours: 24, sla_due_at: '2024-01-02T00:00:00Z', created_at: '2024-01-01T00:00:00Z' },
        { id: '2', case_number: 'CASE-00002', customer_name: 'علی رضایی', application_number: 'APP-1002', status: 'in_review', priority: 'critical', risk_level: 'critical', sla_hours: 24, sla_due_at: '2024-01-02T00:00:00Z', created_at: '2024-01-01T00:00:00Z' },
      ],
      total: 2,
      page: 1,
      page_size: 20,
    });
  });

  it('should render cases grid', async () => {
    render(<CasesPage />, { wrapper: createTestWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('پرونده‌ها')).toBeInTheDocument();
      expect(screen.getByText('CASE-00001')).toBeInTheDocument();
      expect(screen.getByText('CASE-00002')).toBeInTheDocument();
    });
  });

  it('should show priority badges', async () => {
    render(<CasesPage />, { wrapper: createTestWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('زیاد')).toBeInTheDocument();
      expect(screen.getByText('بحرانی')).toBeInTheDocument();
    });
  });
});

describe('Analytics Page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    api.getAnalytics.mockResolvedValue({
      kpis: {
        total_applications: 500,
        new_applications: 50,
        approved_count: 300,
        rejected_count: 50,
        in_review_count: 100,
        approval_rate: 60,
        rejection_rate: 10,
        human_review_rate: 20,
        avg_processing_hours: 24,
        avg_review_hours: 48,
        high_risk_count: 75,
        critical_count: 25,
        total_customers: 400,
        total_cases: 150,
        open_cases: 100,
      },
      applications_over_time: [],
      risk_distribution: [
        { label: 'low', value: 200 },
        { label: 'medium', value: 150 },
        { label: 'high', value: 100 },
        { label: 'critical', value: 50 },
      ],
      verification_funnel: [],
      document_type_distribution: [],
      status_distribution: [],
    });
  });

  it('should render analytics dashboard', async () => {
    render(<AnalyticsPage />, { wrapper: createTestWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('تحلیل‌ها')).toBeInTheDocument();
      expect(screen.getByText('۵۰۰')).toBeInTheDocument(); // total applications
    });
  });

  it('should show risk distribution chart', async () => {
    render(<AnalyticsPage />, { wrapper: createTestWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('توزیع ریسک')).toBeInTheDocument();
    });
  });
});

describe('Policies Page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    api.getPolicies.mockResolvedValue([
      { id: '1', code: 'KYC-001', title: 'KYC Policy', created_at: '2024-01-01T00:00:00Z', versions: [{ id: 'v1', version: '1.0', is_active: true, chunk_count: 10 }] },
    ]);
  });

  it('should render policies list', async () => {
    render(<PoliciesPage />, { wrapper: createTestWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('سیاست‌ها')).toBeInTheDocument();
      expect(screen.getByText('KYC Policy')).toBeInTheDocument();
      expect(screen.getByText('KYC-001')).toBeInTheDocument();
    });
  });

  it('should search policies', async () => {
    api.searchPolicies.mockResolvedValue([
      { clause: '1.1', section: 'Identity', text: 'Documents must be valid', policy_version: '1.0' },
    ]);
    
    render(<PoliciesPage />, { wrapper: createTestWrapper() });
    
    const searchInput = screen.getByPlaceholderText(/جستجو/);
    fireEvent.change(searchInput, { target: { value: 'identity' } });
    
    await waitFor(() => {
      expect(api.searchPolicies).toHaveBeenCalledWith('identity');
    });
  });
});

describe('Notifications Page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    api.getNotifications.mockResolvedValue({
      items: [
        { id: '1', title: 'New Case', body: 'New case assigned', kind: 'new_case', read: false, created_at: '2024-01-01T10:00:00Z' },
        { id: '2', title: 'High Risk', body: 'High risk case', kind: 'high_risk', read: true, created_at: '2024-01-01T09:00:00Z' },
      ],
      total: 2,
      unread_count: 1,
      page: 1,
      page_size: 20,
    });
    api.markNotificationsRead.mockResolvedValue({ message: 'OK' });
  });

  it('should render notifications list', async () => {
    render(<NotificationsPage />, { wrapper: createTestWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('اعلانات')).toBeInTheDocument();
      expect(screen.getByText('New Case')).toBeInTheDocument();
      expect(screen.getByText('High Risk')).toBeInTheDocument();
    });
  });

  it('should show unread count', async () => {
    render(<NotificationsPage />, { wrapper: createTestWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('۱ خوانده‌نشده')).toBeInTheDocument();
    });
  });

  it('should mark notification as read', async () => {
    render(<NotificationsPage />, { wrapper: createTestWrapper() });
    
    const readButton = screen.getByText('خواندن');
    fireEvent.click(readButton);
    
    await waitFor(() => {
      expect(api.markNotificationsRead).toHaveBeenCalledWith(['1'], false);
    });
  });

  it('should mark all as read', async () => {
    render(<NotificationsPage />, { wrapper: createTestWrapper() });
    
    const markAllButton = screen.getByText('علامت‌گذاری همه به عنوان خوانده');
    fireEvent.click(markAllButton);
    
    await waitFor(() => {
      expect(api.markNotificationsRead).toHaveBeenCalledWith([], true);
    });
  });
});

describe('Audit Page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    api.getAuditEvents.mockResolvedValue({
      items: [
        { id: '1', action: 'application.create', entity: 'application', entity_id: 'app-1', actor_role: 'applicant', reason: 'Application created', created_at: '2024-01-01T10:00:00Z' },
        { id: '2', action: 'engine.decision', entity: 'application', entity_id: 'app-1', actor_role: 'system', reason: 'Auto approved', created_at: '2024-01-01T11:00:00Z' },
      ],
      total: 2,
      page: 1,
      page_size: 50,
    });
  });

  it('should render audit log', async () => {
    render(<AuditPage />, { wrapper: createTestWrapper() });
    
    await waitFor(() => {
      expect(screen.getByText('گزارش رویدادها')).toBeInTheDocument();
      expect(screen.getByText('ایجاد درخواست')).toBeInTheDocument();
      expect(screen.getByText('تصمیم موتور')).toBeInTheDocument();
    });
  });

  it('should filter by entity', async () => {
    render(<AuditPage />, { wrapper: createTestWrapper() });
    
    const entitySelect = screen.getByRole('combobox');
    fireEvent.change(entitySelect, { target: { value: 'case' } });
    
    await waitFor(() => {
      expect(api.getAuditEvents).toHaveBeenCalledWith(
        expect.objectContaining({ entity: 'case' })
      );
    });
  });
});