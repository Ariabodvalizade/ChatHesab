// src/components/Dashboard.tsx
import React, { useState, useEffect } from 'react';
import moment from 'moment-jalaali';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  AccountBalance,
  TrendingUp,
  TrendingDown,
  Savings,
  Receipt,
  Analytics,
} from '@mui/icons-material';
import { useAuth } from '../context/AuthContext';
import { API_CONFIG, getAuthHeaders } from '../config/api';

interface DashboardStats {
  totalBalance: number;
  monthlyIncome: number;
  monthlyExpense: number;
  accountsCount: number;
  transactionsCount: number;
  checksCount: number;
  savingsPlansCount: number;
}

export default function Dashboard() {
  const { user, token, logout } = useAuth();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Load Persian calendar and digits once
  useEffect(() => {
    try {
      moment.loadPersian({ usePersianDigits: true, dialect: 'persian-modern' });
    } catch {}
  }, []);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    if (!token) return;

    try {
      setLoading(true);
      
      // Fetch accounts
      const accountsResponse = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.ACCOUNTS}`, {
        headers: getAuthHeaders(token),
      });
      
      // Fetch transactions summary
      const summaryResponse = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.TRANSACTIONS}/summary`, {
        headers: getAuthHeaders(token),
      });
      
      // Fetch checks
      const checksResponse = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.CHECKS}`, {
        headers: getAuthHeaders(token),
      });
      
      // Fetch savings plans
      const savingsResponse = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.SAVINGS_PLANS}`, {
        headers: getAuthHeaders(token),
      });

      if (accountsResponse.ok && summaryResponse.ok && checksResponse.ok && savingsResponse.ok) {
        const accounts = await accountsResponse.json();
        const summary = await summaryResponse.json();
        const checks = await checksResponse.json();
        const savings = await savingsResponse.json();

        const totalBalance = accounts.reduce((sum: number, acc: any) => sum + (acc.current_balance || 0), 0);

        setStats({
          totalBalance,
          monthlyIncome: summary.income?.total || 0,
          monthlyExpense: summary.expense?.total || 0,
          accountsCount: accounts.length,
          transactionsCount: (summary.income?.count || 0) + (summary.expense?.count || 0),
          checksCount: checks.length,
          savingsPlansCount: savings.length,
        });
      } else {
        setError('خطا در دریافت اطلاعات');
      }
    } catch (error) {
      console.error('Dashboard error:', error);
      setError('خطا در اتصال به سرور');
    } finally {
      setLoading(false);
    }
  };

  const formatAmount = (amount: number) => {
    return new Intl.NumberFormat('fa-IR').format(amount) + ' تومان';
  };

  const getBalanceColor = (balance: number) => {
    if (balance > 0) return 'success';
    if (balance < 0) return 'error';
    return 'default';
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, textAlign: 'center' }}>
        <CircularProgress />
        <Typography>در حال بارگذاری...</Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" flexWrap="wrap" gap={2} mb={3}>
        <Box>
          <Typography variant="h4" component="h1">
            داشبورد مالی
          </Typography>
          <Typography variant="body2" color="text.secondary">
            امروز: {moment().format('jYYYY/jMM/jDD dddd')}
          </Typography>
        </Box>
        <Box display="flex" alignItems="center" gap={1}>
          <Chip 
            label={`${user?.first_name} ${user?.last_name}`} 
            color="primary" 
            sx={{ mr: 0 }}
          />
          <Button variant="outlined" onClick={logout}>
            خروج
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Stats Cards */}
      <Grid container spacing={3} mb={4} alignItems="stretch">
        <Grid item xs={3} sm={3} md={3} lg={3} xl={3}>
          <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <CardContent>
              <Box display="flex" alignItems="center">
                <AccountBalance color="primary" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    موجودی کل
                  </Typography>
                  <Typography variant="h6">
                    <Chip 
                      label={formatAmount(stats?.totalBalance || 0)}
                      color={getBalanceColor(stats?.totalBalance || 0)}
                      size="small"
                    />
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={3} sm={3} md={3} lg={3} xl={3}>
          <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <CardContent>
              <Box display="flex" alignItems="center">
                <TrendingUp color="success" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    درآمد این ماه
                  </Typography>
                  <Typography variant="h6" color="success.main">
                    {formatAmount(stats?.monthlyIncome || 0)}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={3} sm={3} md={3} lg={3} xl={3}>
          <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <CardContent>
              <Box display="flex" alignItems="center">
                <TrendingDown color="error" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    هزینه این ماه
                  </Typography>
                  <Typography variant="h6" color="error.main">
                    {formatAmount(stats?.monthlyExpense || 0)}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={3} sm={3} md={3} lg={3} xl={3}>
          <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <CardContent>
              <Box display="flex" alignItems="center">
                <Analytics color="info" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    تراز
                  </Typography>
                  <Typography variant="h6">
                    <Chip 
                      label={formatAmount((stats?.monthlyIncome || 0) - (stats?.monthlyExpense || 0))}
                      color={getBalanceColor((stats?.monthlyIncome || 0) - (stats?.monthlyExpense || 0))}
                      size="small"
                    />
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Quick Actions */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              حساب‌های بانکی
            </Typography>
            <Typography variant="body2" color="textSecondary" mb={2}>
              {stats?.accountsCount} حساب ثبت شده
            </Typography>
            <Button variant="contained" fullWidth>
              مدیریت حساب‌ها
            </Button>
          </Paper>
        </Grid>

        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              تراکنش‌ها
            </Typography>
            <Typography variant="body2" color="textSecondary" mb={2}>
              {stats?.transactionsCount} تراکنش ثبت شده
            </Typography>
            <Button variant="contained" fullWidth>
              مشاهده تراکنش‌ها
            </Button>
          </Paper>
        </Grid>

        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              چک‌ها
            </Typography>
            <Typography variant="body2" color="textSecondary" mb={2}>
              {stats?.checksCount} چک ثبت شده
            </Typography>
            <Button variant="contained" fullWidth>
              مدیریت چک‌ها
            </Button>
          </Paper>
        </Grid>
      </Grid>

      {/* Welcome Message for New Users */}
      {stats?.accountsCount === 0 && (
        <Alert severity="info" sx={{ mt: 3 }}>
          <Typography variant="h6" gutterBottom>
            🎉 خوش آمدید!
          </Typography>
          <Typography>
            برای شروع، ابتدا حساب‌های بانکی خود را ثبت کنید و سپس تراکنش‌های مالی خود را وارد نمایید.
            می‌توانید از قابلیت پردازش متن فارسی برای ثبت سریع تراکنش‌ها استفاده کنید.
          </Typography>
          <Box mt={2}>
            <Button variant="contained" color="primary">
              ثبت اولین حساب
            </Button>
          </Box>
        </Alert>
      )}
    </Container>
  );
}
