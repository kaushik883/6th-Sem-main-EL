import { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { login as apiLogin, logout as apiLogout, getMe } from '../api/client';
import type { UserRole, CompanyType } from '../api/types';

export interface AuthUser {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  company_id?: number;
  company_type?: CompanyType;
  company_name?: string;
  is_admin: boolean;
}

export interface AuthContextValue {
  user: AuthUser | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextValue>({
  user: null,
  loading: true,
  login: async () => {},
  logout: async () => {},
});

export function useAuth(): AuthContextValue {
  return useContext(AuthContext);
}

export function useAuthProvider(): AuthContextValue {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  // Check if user is logged in on mount
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('auth_token');
      if (token) {
        try {
          const userData = await getMe();
          setUser(userData);
        } catch (error) {
          // Token invalid, clear it
          localStorage.removeItem('auth_token');
          setUser(null);
        }
      }
      setLoading(false);
    };

    checkAuth();
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const { user: userData } = await apiLogin(email, password);
    setUser(userData);
  }, []);

  const logout = useCallback(async () => {
    await apiLogout();
    setUser(null);
  }, []);

  return { user, loading, login, logout };
}
