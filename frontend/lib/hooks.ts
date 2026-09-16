"use client";
import { useState, useEffect, useCallback } from "react";
import { api } from "./api";
import type { User, Notification } from "@/types";

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = api.getToken();
    if (!token) {
      setLoading(false);
      return;
    }
    api.getMe().then(setUser).catch(() => api.setToken(null)).finally(() => setLoading(false));
  }, []);

  const login = async (email: string, password: string) => {
    const res = await api.login(email, password);
    api.setToken(res.access_token);
    setUser(res.user);
    return res;
  };

  const logout = () => {
    api.setToken(null);
    setUser(null);
  };

  return { user, loading, login, logout };
}

export function useNotifications() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);

  const fetch = useCallback(async () => {
    try {
      const res = await api.getNotifications({ page_size: "20" });
      setNotifications(res.items);
      setUnreadCount(res.unread_count);
    } catch {}
  }, []);

  useEffect(() => { fetch(); }, [fetch]);

  const markRead = async (ids?: string[], all = false) => {
    await api.markNotificationsRead(ids, all);
    fetch();
  };

  return { notifications, unreadCount, markRead, refresh: fetch };
}
