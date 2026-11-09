import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import { getToken, setToken } from "@/lib/api";
import { authApi } from "@/services/endpoints";
import type { User } from "@/types";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (values: { email: string; username: string; password: string; full_name?: string }) => Promise<void>;
  logout: () => void;
  refresh: () => Promise<void>;
  setUser: (user: User) => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUserState] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    if (!getToken()) {
      setUserState(null);
      setLoading(false);
      return;
    }
    try {
      const me = await authApi.me();
      setUserState(me);
    } catch {
      setToken(null);
      setUserState(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const login = useCallback(async (email: string, password: string) => {
    const res = await authApi.login({ email, password });
    setToken(res.access_token);
    setUserState(res.user);
  }, []);

  const signup = useCallback(
    async (values: { email: string; username: string; password: string; full_name?: string }) => {
      const res = await authApi.signup(values);
      setToken(res.access_token);
      setUserState(res.user);
    },
    [],
  );

  const logout = useCallback(() => {
    setToken(null);
    setUserState(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      loading,
      isAuthenticated: Boolean(user),
      login,
      signup,
      logout,
      refresh,
      setUser: setUserState,
    }),
    [user, loading, login, signup, logout, refresh],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
