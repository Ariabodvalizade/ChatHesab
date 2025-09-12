// src/context/AuthContext.tsx
import React, { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import { API_CONFIG, getAuthHeaders } from '../config/api';

interface User {
  user_id: number;
  telegram_id?: number;
  phone_number?: string;
  username?: string;
  first_name?: string;
  last_name?: string;
  is_active: boolean;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (telegramId: number, userData?: Partial<User>) => Promise<boolean>;
  phoneLogin: (token: string, userData: any) => Promise<boolean>;
  logout: () => void;
  isAuthenticated: boolean;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(
    localStorage.getItem('finance_bot_token')
  );
  const [loading, setLoading] = useState(true);

  const login = async (telegramId: number, userData?: Partial<User>): Promise<boolean> => {
    try {
      setLoading(true);
      console.log('Starting login process for telegram_id:', telegramId);
      
      // First try to create/login user
      const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.USERS}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          telegram_id: telegramId,
          username: userData?.username || `user_${telegramId}`,
          first_name: userData?.first_name || 'کاربر',
          last_name: userData?.last_name || 'تست',
        }),
      });

      console.log('User creation response status:', response.status);

      if (response.ok) {
        const data = await response.json();
        console.log('User creation response data:', data);
        const newToken = data.token;
        
        if (!newToken) {
          console.error('No token received from server');
          return false;
        }
        
        // Store token
        localStorage.setItem('finance_bot_token', newToken);
        setToken(newToken);

        // Get user info with a small delay to ensure token is set
        await new Promise(resolve => setTimeout(resolve, 100));
        
        const userResponse = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.USERS}/me`, {
          headers: getAuthHeaders(newToken),
        });

        console.log('User info response status:', userResponse.status);

        if (userResponse.ok) {
          const userInfo = await userResponse.json();
          console.log('User info received:', userInfo);
          setUser(userInfo);
          console.log('Login completed successfully');
          return true;
        } else {
          console.error('Failed to get user info');
          const errorText = await userResponse.text();
          console.error('User info error:', errorText);
        }
      } else {
        console.error('Failed to create/login user');
        const errorText = await response.text();
        console.error('Login error response:', errorText);
      }
      
      return false;
    } catch (error) {
      console.error('Login error:', error);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const phoneLogin = async (authToken: string, userData: any): Promise<boolean> => {
    try {
      setLoading(true);
      console.log('Phone login with token:', authToken);
      
      // Store token
      localStorage.setItem('finance_bot_token', authToken);
      setToken(authToken);
      
      // Set user data
      setUser(userData.user);
      return true;
      
    } catch (error) {
      console.error('Phone login error:', error);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('finance_bot_token');
    setToken(null);
    setUser(null);
  };

  // Check existing token on app start
  useEffect(() => {
    const checkAuth = async () => {
      console.log('Checking existing auth, token:', token);
      if (token) {
        try {
          const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.USERS}/me`, {
            headers: getAuthHeaders(token),
          });

          console.log('Auth check response status:', response.status);
          if (response.ok) {
            const userData = await response.json();
            console.log('Existing token valid, user data:', userData);
            setUser(userData);
          } else {
            // Token invalid
            console.log('Token invalid, logging out');
            logout();
          }
        } catch (error) {
          console.error('Auth check error:', error);
          logout();
        }
      } else {
        console.log('No existing token found');
      }
      setLoading(false);
    };

    checkAuth();
  }, [token]);

  const value = {
    user,
    token,
    login,
    phoneLogin,
    logout,
    isAuthenticated: !!user && !!token,
    loading,
  };

  // Debug authentication state changes
  useEffect(() => {
    console.log('Auth state changed:', { 
      user: user?.telegram_id, 
      hasToken: !!token, 
      isAuthenticated: !!user && !!token, 
      loading,
      userName: user?.first_name 
    });
    
    // If user just logged in, prevent any potential page refresh
    if (user && token && !loading) {
      console.log('User successfully authenticated, preventing page refresh');
      window.history.replaceState(null, '', window.location.pathname);
    }
  }, [user, token, loading]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}