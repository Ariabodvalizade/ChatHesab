// src/components/Reports.tsx
import React, { useState, useEffect } from 'react';
import { PieChart as RPieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import {
  Container,
  Paper,
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  LinearProgress,
  ToggleButton,
  ToggleButtonGroup,
  Divider,
} from '@mui/material';
import {
  Analytics,
  TrendingUp,
  TrendingDown,
  PieChart,
  BarChart,
  Timeline,
  AccountBalance,
  Savings,
} from '@mui/icons-material';
import { useAuth } from '../context/AuthContext';
import { API_CONFIG, getAuthHeaders } from '../config/api';

interface TransactionSummary {
  income: { count: number; total: number };
  expense: { count: number; total: number };
  balance: number;
}

interface CategorySummary {
  [category: string]: {
    count: number;
    total: number;
  };
}

export default function Reports() {
  const { token } = useAuth();
  const [summary, setSummary] = useState<TransactionSummary | null>(null);
  const [expenseCategories, setExpenseCategories] = useState<CategorySummary>({});
  const [incomeCategories, setIncomeCategories] = useState<CategorySummary>({});
  const [dateRange, setDateRange] = useState('last-30-days');
  const [viewMode, setViewMode] = useState('table'); // 'table' or 'chart'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchReports();
  }, [dateRange]);

  const fetchReports = async () => {
    if (!token) return;

    setLoading(true);
    try {
      const today = new Date();
      let startDate: string;
      let endDate = today.toISOString().split('T')[0];

      switch (dateRange) {
        case 'last-7-days':
          startDate = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
          break;
        case 'last-30-days':
          startDate = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
          break;
        case 'last-90-days':
          startDate = new Date(today.getTime() - 90 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
          break;
        case 'this-month':
          startDate = new Date(today.getFullYear(), today.getMonth(), 1).toISOString().split('T')[0];
          break;
        case 'last-month':
          const lastMonth = new Date(today.getFullYear(), today.getMonth() - 1, 1);
          startDate = lastMonth.toISOString().split('T')[0];
          endDate = new Date(today.getFullYear(), today.getMonth(), 0).toISOString().split('T')[0];
          break;
        default:
          startDate = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
      }

      const [summaryRes, expenseCategoriesRes, incomeCategoriesRes] = await Promise.all([
        fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.TRANSACTIONS}/summary?start_date=${startDate}&end_date=${endDate}`, {
          headers: getAuthHeaders(token),
        }),
        fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.TRANSACTIONS}/categories?transaction_type=expense&start_date=${startDate}&end_date=${endDate}`, {
          headers: getAuthHeaders(token),
        }),
        fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.TRANSACTIONS}/categories?transaction_type=income&start_date=${startDate}&end_date=${endDate}`, {
          headers: getAuthHeaders(token),
        }),
      ]);

      if (summaryRes.ok && expenseCategoriesRes.ok && incomeCategoriesRes.ok) {
        const [summaryData, expenseData, incomeData] = await Promise.all([
          summaryRes.json(),
          expenseCategoriesRes.json(),
          incomeCategoriesRes.json(),
        ]);

        setSummary(summaryData);
        setExpenseCategories(expenseData);
        setIncomeCategories(incomeData);
      } else {
        setError('خطا در دریافت گزارش‌ها');
      }
    } catch (error) {
      console.error('Error fetching reports:', error);
      setError('خطا در اتصال به سرور');
    } finally {
      setLoading(false);
    }
  };

  const formatAmount = (amount: number) => {
    return new Intl.NumberFormat('fa-IR').format(amount);
  };

  const getDateRangeLabel = (range: string) => {
    switch (range) {
      case 'last-7-days':
        return '۷ روز گذشته';
      case 'last-30-days':
        return '۳۰ روز گذشته';
      case 'last-90-days':
        return '۳ ماه گذشته';
      case 'this-month':
        return 'این ماه';
      case 'last-month':
        return 'ماه گذشته';
      default:
        return range;
    }
  };

  const calculatePercentage = (amount: number, total: number) => {
    return total > 0 ? ((amount / total) * 100).toFixed(1) : '0';
  };

  const sortedExpenseCategories = Object.entries(expenseCategories)
    .sort(([, a], [, b]) => b.total - a.total);

  const sortedIncomeCategories = Object.entries(incomeCategories)
    .sort(([, a], [, b]) => b.total - a.total);

  const chartColors = ['#0ea5e9', '#22c55e', '#f59e0b', '#ef4444', '#a855f7', '#06b6d4', '#84cc16', '#fb7185'];

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          📈 گزارش‌های مالی تفصیلی
        </Typography>
        <Box display="flex" gap={2} alignItems="center">
          <ToggleButtonGroup
            value={viewMode}
            exclusive
            onChange={(e, newMode) => newMode && setViewMode(newMode)}
            size="small"
          >
            <ToggleButton value="table">
              <Timeline sx={{ mr: 0.5 }} /> جدولی
            </ToggleButton>
            <ToggleButton value="chart">
              <BarChart sx={{ mr: 0.5 }} /> نموداری
            </ToggleButton>
          </ToggleButtonGroup>
          <FormControl sx={{ minWidth: 200 }}>
            <InputLabel>بازه زمانی</InputLabel>
            <Select
              value={dateRange}
              onChange={(e) => setDateRange(e.target.value)}
              label="بازه زمانی"
            >
              <MenuItem value="last-7-days">۷ روز گذشته</MenuItem>
              <MenuItem value="last-30-days">۳۰ روز گذشته</MenuItem>
              <MenuItem value="last-90-days">۳ ماه گذشته</MenuItem>
              <MenuItem value="this-month">این ماه</MenuItem>
              <MenuItem value="last-month">ماه گذشته</MenuItem>
            </Select>
          </FormControl>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      <Typography variant="h6" gutterBottom>
        گزارش {getDateRangeLabel(dateRange)}
      </Typography>

      {/* Summary Cards */}
      {summary && (
        <Grid container spacing={3} mb={4}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center">
                  <TrendingUp color="success" sx={{ mr: 2 }} />
                  <Box>
                    <Typography color="textSecondary" gutterBottom>
                      کل درآمد
                    </Typography>
                    <Typography variant="h6" color="success.main">
                      {formatAmount(summary.income.total)} تومان
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      {summary.income.count} تراکنش
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center">
                  <TrendingDown color="error" sx={{ mr: 2 }} />
                  <Box>
                    <Typography color="textSecondary" gutterBottom>
                      کل هزینه
                    </Typography>
                    <Typography variant="h6" color="error.main">
                      {formatAmount(summary.expense.total)} تومان
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      {summary.expense.count} تراکنش
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center">
                  <Analytics color="primary" sx={{ mr: 2 }} />
                  <Box>
                    <Typography color="textSecondary" gutterBottom>
                      خالص (تراز)
                    </Typography>
                    <Typography 
                      variant="h6" 
                      color={summary.balance >= 0 ? 'success.main' : 'error.main'}
                    >
                      {formatAmount(summary.balance)} تومان
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      {summary.income.count + summary.expense.count} کل تراکنش
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center">
                  <PieChart color="info" sx={{ mr: 2 }} />
                  <Box>
                    <Typography color="textSecondary" gutterBottom>
                      نرخ پس‌انداز
                    </Typography>
                    <Typography variant="h6" color="info.main">
                      {summary.income.total > 0 
                        ? ((summary.balance / summary.income.total) * 100).toFixed(1)
                        : '0'
                      }%
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      از کل درآمد
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Category Breakdown */}
      <Grid container spacing={3}>
        {/* Expense Categories */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Box display="flex" alignItems="center" mb={2}>
              <TrendingDown color="error" sx={{ mr: 2 }} />
              <Typography variant="h6">تحلیل هزینه‌ها بر اساس دسته‌بندی</Typography>
            </Box>
            {viewMode === 'table' ? (
              sortedExpenseCategories.length > 0 ? (
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>دسته‌بندی</TableCell>
                        <TableCell align="right">مبلغ</TableCell>
                        <TableCell align="right">درصد</TableCell>
                        <TableCell align="right">تعداد</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {sortedExpenseCategories.map(([category, data]) => (
                        <TableRow key={category}>
                          <TableCell>{category}</TableCell>
                          <TableCell align="right">{formatAmount(data.total)} تومان</TableCell>
                          <TableCell align="right">{calculatePercentage(data.total, summary?.expense.total || 0)}%</TableCell>
                          <TableCell align="right">{data.count}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                <Typography color="textSecondary" textAlign="center">هیچ هزینه‌ای در این بازه ثبت نشده است</Typography>
              )
            ) : (
              <Box sx={{ height: 320 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <RPieChart>
                    <Pie
                      data={sortedExpenseCategories.map(([category, data]) => ({
                        name: category,
                        value: Number(calculatePercentage(data.total, summary?.expense.total || 0)),
                      }))}
                      dataKey="value"
                      nameKey="name"
                      innerRadius={60}
                      outerRadius={100}
                      paddingAngle={2}
                    >
                      {sortedExpenseCategories.map((_, idx) => (
                        <Cell key={`cell-${idx}`} fill={chartColors[idx % chartColors.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value: any) => `${value}%`} />
                    <Legend />
                  </RPieChart>
                </ResponsiveContainer>
              </Box>
            )}
          </Paper>
        </Grid>

        {/* Income Categories */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Box display="flex" alignItems="center" mb={2}>
              <TrendingUp color="success" sx={{ mr: 2 }} />
              <Typography variant="h6">تحلیل درآمدها بر اساس دسته‌بندی</Typography>
            </Box>
            
            {viewMode === 'table' ? (
              sortedIncomeCategories.length > 0 ? (
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>دسته‌بندی</TableCell>
                        <TableCell align="right">مبلغ</TableCell>
                        <TableCell align="right">درصد</TableCell>
                        <TableCell align="right">تعداد</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {sortedIncomeCategories.map(([category, data]) => (
                        <TableRow key={category}>
                          <TableCell>{category}</TableCell>
                          <TableCell align="right">{formatAmount(data.total)} تومان</TableCell>
                          <TableCell align="right">{calculatePercentage(data.total, summary?.income.total || 0)}%</TableCell>
                          <TableCell align="right">{data.count}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                <Typography color="textSecondary" textAlign="center">هیچ درآمدی در این بازه ثبت نشده است</Typography>
              )
            ) : (
              <Box sx={{ height: 320 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <RPieChart>
                    <Pie
                      data={sortedIncomeCategories.map(([category, data]) => ({
                        name: category,
                        value: Number(calculatePercentage(data.total, summary?.income.total || 0)),
                      }))}
                      dataKey="value"
                      nameKey="name"
                      innerRadius={60}
                      outerRadius={100}
                      paddingAngle={2}
                    >
                      {sortedIncomeCategories.map((_, idx) => (
                        <Cell key={`cell-i-${idx}`} fill={chartColors[idx % chartColors.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value: any) => `${value}%`} />
                    <Legend />
                  </RPieChart>
                </ResponsiveContainer>
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
}
