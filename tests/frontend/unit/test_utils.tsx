"""
Frontend unit tests for components, hooks, and utilities
"""
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';

// Test utilities
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

// Mock API
jest.mock('@/lib/api', () => ({
  api: {
    getMe: jest.fn(),
    login: jest.fn(),
    getCustomers: jest.fn(),
    getApplications: jest.fn(),
    getApplication: jest.fn(),
    getAnalytics: jest.fn(),
    getCases: jest.fn(),
    getNotifications: jest.fn(),
    markNotificationsRead: jest.fn(),
    getPolicies: jest.fn(),
    globalSearch: jest.fn(),
    getRiskAssessment: jest.fn(),
    getScreeningResults: jest.fn(),
    getVerifications: jest.fn(),
    getFaceVerification: jest.fn(),
    getDocument: jest.fn(),
    changePassword: jest.fn(),
  },
}));

import { api } from '@/lib/api';

// Import components to test
import { cn } from '@/lib/utils';
import { useAuth } from '@/lib/hooks';

describe('Utility Functions', () => {
  describe('cn (classnames utility)', () => {
    it('should merge classnames correctly', () => {
      expect(cn('base', 'extra')).toBe('base extra');
    });

    it('should handle conditional classes', () => {
      expect(cn('base', true && 'conditional')).toBe('base conditional');
      expect(cn('base', false && 'conditional')).toBe('base');
    });

    it('should handle tailwind conflicts', () => {
      expect(cn('p-4', 'p-2')).toBe('p-2'); // p-2 should override p-4
    });
  });

  describe('Persian digit conversion', () => {
    it('should convert English digits to Persian', () => {
      const { toPersianDigits } = require('@/lib/utils');
      expect(toPersianDigits(123)).toBe('۱۲۳');
      expect(toPersianDigits('456')).toBe('۴۵۶');
    });

    it('should handle mixed strings', () => {
      const { toPersianDigits } = require('@/lib/utils');
      expect(toPersianDigits('Test 123')).toBe('Test ۱۲۳');
    });
  });

  describe('Number formatting', () => {
    it('should format numbers with Persian locale', () => {
      const { formatNumber } = require('@/lib/utils');
      expect(formatNumber(1000)).toBe('۱٬۰۰۰');
      expect(formatNumber(1234567)).toBe('۱٬۲۳۴٬۵۶۷');
    });
  });

  describe('Status mapping', () => {
    it('should map statuses to Persian', () => {
      const { STATUS_MAP } = require('@/lib/utils');
      expect(STATUS_MAP['draft']).toBe('پیش‌نویس');
      expect(STATUS_MAP['approved']).toBe('تأیید شده');
      expect(STATUS_MAP['rejected']).toBe('رد شده');
    });
  });

  describe('Risk level mapping', () => {
    it('should map risk levels to Persian', () => {
      const { RISK_LEVEL_MAP } = require('@/lib/utils');
      expect(RISK_LEVEL_MAP['low']).toBe('ریسک پایین');
      expect(RISK_LEVEL_MAP['critical']).toBe('ریسک بحرانی');
    });
  });
});

describe('API Client', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  describe('login', () => {
    it('should call login endpoint and store tokens', async () => {
      const mockResponse = {
        access_token: 'access-123',
        refresh_token: 'refresh-123',
        user: { id: '1', email: 'test@test.com', full_name: 'Test', role: 'applicant' },
      };
      api.login.mockResolvedValue(mockResponse);

      const result = await api.login('test@test.com', 'password');
      
      expect(api.login).toHaveBeenCalledWith('test@test.com', 'password');
      expect(result).toEqual(mockResponse);
      expect(localStorage.getItem('token')).toBe('access-123');
    });

    it('should handle login error', async () => {
      api.login.mockRejectedValue(new Error('Invalid credentials'));
      
      await expect(api.login('test@test.com', 'wrong')).rejects.toThrow('Invalid credentials');
    });
  });

  describe('getMe', () => {
    it('should fetch current user', async () => {
      const mockUser = { id: '1', email: 'test@test.com', full_name: 'Test', role: 'applicant' };
      api.getMe.mockResolvedValue(mockUser);

      const result = await api.getMe();
      
      expect(result).toEqual(mockUser);
    });

    it('should clear token on 401', async () => {
      api.getMe.mockRejectedValue(new Error('Unauthorized'));
      localStorage.setItem('token', 'old-token');

      await expect(api.getMe()).rejects.toThrow();
      expect(localStorage.getItem('token')).toBeNull();
    });
  });

  describe('Token management', () => {
    it('should get token from localStorage', () => {
      localStorage.setItem('token', 'stored-token');
      expect(api.getToken()).toBe('stored-token');
    });

    it('should set token in localStorage', () => {
      api.setToken('new-token');
      expect(localStorage.getItem('token')).toBe('new-token');
    });

    it('should clear token', () => {
      localStorage.setItem('token', 'old-token');
      api.setToken(null);
      expect(localStorage.getItem('token')).toBeNull();
    });
  });
});

describe('useAuth Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  it('should return user when token exists', async () => {
    const mockUser = { id: '1', email: 'test@test.com', full_name: 'Test', role: 'applicant' };
    api.getMe.mockResolvedValue(mockUser);
    localStorage.setItem('token', 'valid-token');

    const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() });
    
    await waitFor(() => expect(result.current.loading).toBe(false));
    
    expect(result.current.user).toEqual(mockUser);
  });

  it('should return null user when no token', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() });
    
    await waitFor(() => expect(result.current.loading).toBe(false));
    
    expect(result.current.user).toBeNull();
  });

  it('should login and set user', async () => {
    const mockResponse = {
      access_token: 'access-123',
      refresh_token: 'refresh-123',
      user: { id: '1', email: 'test@test.com', full_name: 'Test', role: 'applicant' },
    };
    api.login.mockResolvedValue(mockResponse);

    const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() });
    
    await result.current.login('test@test.com', 'password');
    
    expect(result.current.user).toEqual(mockResponse.user);
    expect(localStorage.getItem('token')).toBe('access-123');
  });

  it('should logout and clear user', async () => {
    const mockUser = { id: '1', email: 'test@test.com', full_name: 'Test', role: 'applicant' };
    api.getMe.mockResolvedValue(mockUser);
    localStorage.setItem('token', 'valid-token');

    const { result } = renderHook(() => useAuth(), { wrapper: createWrapper() });
    
    await waitFor(() => expect(result.current.user).toEqual(mockUser));
    
    result.current.logout();
    
    expect(result.current.user).toBeNull();
    expect(localStorage.getItem('token')).toBeNull();
  });
});

describe('useNotifications Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch notifications on mount', async () => {
    const mockNotifications = [
      { id: '1', title: 'Test', body: 'Body', kind: 'new_case', read: false },
    ];
    api.getNotifications.mockResolvedValue({ items: mockNotifications, unread_count: 1, total: 1 });

    const { result } = renderHook(() => useNotifications(), { wrapper: createWrapper() });
    
    await waitFor(() => expect(result.current.notifications).toEqual(mockNotifications));
    expect(result.current.unreadCount).toBe(1);
  });

  it('should mark notifications as read', async () => {
    api.getNotifications.mockResolvedValue({ items: [], unread_count: 0, total: 0 });
    api.markNotificationsRead.mockResolvedValue({ message: 'OK' });

    const { result } = renderHook(() => useNotifications(), { wrapper: createWrapper() });
    
    await waitFor(() => expect(result.current.notifications).toEqual([]));
    
    await result.current.markRead(['1']);
    
    expect(api.markNotificationsRead).toHaveBeenCalledWith(['1'], false);
  });

  it('should mark all as read', async () => {
    api.getNotifications.mockResolvedValue({ items: [], unread_count: 0, total: 0 });
    api.markNotificationsRead.mockResolvedValue({ message: 'OK' });

    const { result } = renderHook(() => useNotifications(), { wrapper: createWrapper() });
    
    await result.current.markRead([], true);
    
    expect(api.markNotificationsRead).toHaveBeenCalledWith([], true);
  });
});

// Import renderHook for testing hooks
import { renderHook } from '@testing-library/react';