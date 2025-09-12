// src/config/api.ts
export const API_CONFIG = {
  BASE_URL: 'http://localhost:8001',
  ENDPOINTS: {
    USERS: '/api/users',
    ACCOUNTS: '/api/accounts',
    TRANSACTIONS: '/api/transactions',
    CHECKS: '/api/checks',
    SAVINGS_PLANS: '/api/savings-plans',
    AI_PROCESS: '/api/ai/process-message',
    AI_ADVISOR_USAGE: '/api/ai/advisor/usage-limit',
    AI_ADVISOR_ANALYZE: '/api/ai/advisor/analyze',
    AI_CHAT_ENHANCED: '/api/ai/chat/process',
    CATEGORIES: '/api/categories',
  }
};

export const getAuthHeaders = (token: string) => ({
  'Authorization': `Bearer ${token}`,
  'Content-Type': 'application/json',
});