// src/components/SavingsPlans.tsx
import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Button,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Card,
  CardContent,
  Grid,
  LinearProgress,
  Chip,
  Alert,
} from '@mui/material';
import {
  Add,
  Savings,
  TrendingUp,
  Flag,
} from '@mui/icons-material';
import { useAuth } from '../context/AuthContext';
import { API_CONFIG, getAuthHeaders } from '../config/api';

interface SavingsPlan {
  plan_id: number;
  plan_name: string;
  plan_type: string;
  target_amount: number;
  current_amount: number;
  monthly_contribution: number;
  start_date: string;
  end_date: string;
  status: 'active' | 'completed' | 'cancelled' | 'paused';
}

export default function SavingsPlans() {
  const { token } = useAuth();
  const [plans, setPlans] = useState<SavingsPlan[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  
  const [formData, setFormData] = useState({
    plan_name: '',
    plan_type: '',
    target_amount: '',
    monthly_contribution: '',
    end_date: '',
  });

  useEffect(() => {
    fetchPlans();
  }, []);

  const fetchPlans = async () => {
    if (!token) return;
    
    setLoading(true);
    try {
      const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.SAVINGS_PLANS}`, {
        headers: getAuthHeaders(token),
      });

      if (response.ok) {
        const data = await response.json();
        setPlans(data);
      } else {
        setError('خطا در دریافت طرح‌های پس‌انداز');
      }
    } catch (error) {
      console.error('Error fetching savings plans:', error);
      setError('خطا در اتصال به سرور');
    } finally {
      setLoading(false);
    }
  };

  const handleAddPlan = async () => {
    if (!token || !formData.plan_name || !formData.target_amount) {
      setError('لطفاً نام طرح و مبلغ هدف را وارد کنید');
      return;
    }

    try {
      setLoading(true);
      const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.SAVINGS_PLANS}`, {
        method: 'POST',
        headers: getAuthHeaders(token),
        body: JSON.stringify({
          plan_name: formData.plan_name,
          plan_type: formData.plan_type,
          target_amount: parseFloat(formData.target_amount),
          monthly_contribution: formData.monthly_contribution ? parseFloat(formData.monthly_contribution) : null,
          end_date: formData.end_date || null,
        }),
      });

      if (response.ok) {
        setAddDialogOpen(false);
        setFormData({
          plan_name: '',
          plan_type: '',
          target_amount: '',
          monthly_contribution: '',
          end_date: '',
        });
        fetchPlans();
      } else {
        setError('خطا در ایجاد طرح پس‌انداز');
      }
    } catch (error) {
      console.error('Error adding savings plan:', error);
      setError('خطا در اتصال به سرور');
    } finally {
      setLoading(false);
    }
  };

  const formatAmount = (amount: number) => {
    return new Intl.NumberFormat('fa-IR').format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('fa-IR');
  };

  const calculateProgress = (current: number, target: number) => {
    return target > 0 ? Math.min((current / target) * 100, 100) : 0;
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'active':
        return 'فعال';
      case 'completed':
        return 'تکمیل شده';
      case 'cancelled':
        return 'لغو شده';
      case 'paused':
        return 'متوقف';
      default:
        return status;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'primary';
      case 'completed':
        return 'success';
      case 'cancelled':
        return 'error';
      case 'paused':
        return 'warning';
      default:
        return 'default';
    }
  };

  const totalSavings = plans.reduce((sum, plan) => sum + plan.current_amount, 0);
  const totalTargets = plans.reduce((sum, plan) => sum + plan.target_amount, 0);
  const activePlans = plans.filter(p => p.status === 'active');

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          طرح‌های پس‌انداز
        </Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => setAddDialogOpen(true)}
        >
          طرح جدید
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {/* Summary Cards */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <Savings color="primary" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    کل پس‌انداز
                  </Typography>
                  <Typography variant="h6">
                    {formatAmount(totalSavings)} تومان
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
                <Flag color="warning" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    هدف کل
                  </Typography>
                  <Typography variant="h6">
                    {formatAmount(totalTargets)} تومان
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
                <TrendingUp color="success" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    طرح‌های فعال
                  </Typography>
                  <Typography variant="h6" color="success.main">
                    {activePlans.length}
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
                <Savings color="info" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    پیشرفت کل
                  </Typography>
                  <Typography variant="h6">
                    {totalTargets > 0 ? Math.round((totalSavings / totalTargets) * 100) : 0}%
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Savings Plans Grid */}
      <Grid container spacing={3}>
        {plans.map((plan) => {
          const progress = calculateProgress(plan.current_amount, plan.target_amount);
          const remaining = Math.max(plan.target_amount - plan.current_amount, 0);
          
          return (
            <Grid item xs={12} sm={6} md={4} key={plan.plan_id}>
              <Card elevation={3}>
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                    <Typography variant="h6" component="div" noWrap>
                      {plan.plan_name}
                    </Typography>
                    <Chip
                      label={getStatusLabel(plan.status)}
                      color={getStatusColor(plan.status) as any}
                      size="small"
                    />
                  </Box>

                  {plan.plan_type && (
                    <Typography variant="body2" color="text.secondary" mb={2}>
                      نوع طرح: {plan.plan_type}
                    </Typography>
                  )}

                  <Box mb={2}>
                    <Typography variant="body2" color="text.secondary">
                      پیشرفت: {progress.toFixed(1)}%
                    </Typography>
                    <LinearProgress 
                      variant="determinate" 
                      value={progress} 
                      sx={{ mt: 1, mb: 1 }}
                    />
                    <Typography variant="body2">
                      {formatAmount(plan.current_amount)} از {formatAmount(plan.target_amount)} تومان
                    </Typography>
                  </Box>

                  {remaining > 0 && (
                    <Box mb={2}>
                      <Typography variant="body2" color="text.secondary">
                        مانده: {formatAmount(remaining)} تومان
                      </Typography>
                    </Box>
                  )}

                  {plan.monthly_contribution && (
                    <Box mb={2}>
                      <Typography variant="body2" color="text.secondary">
                        واریز ماهانه: {formatAmount(plan.monthly_contribution)} تومان
                      </Typography>
                    </Box>
                  )}

                  <Box mb={2}>
                    <Typography variant="body2" color="text.secondary">
                      شروع: {formatDate(plan.start_date)}
                    </Typography>
                    {plan.end_date && (
                      <Typography variant="body2" color="text.secondary">
                        پایان: {formatDate(plan.end_date)}
                      </Typography>
                    )}
                  </Box>

                  <Box display="flex" gap={1}>
                    <Button size="small" variant="outlined">
                      واریز
                    </Button>
                    <Button size="small" variant="outlined">
                      ویرایش
                    </Button>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          );
        })}

        {plans.length === 0 && (
          <Grid item xs={12}>
            <Paper sx={{ p: 4, textAlign: 'center' }}>
              <Savings sx={{ fontSize: 80, color: 'grey.400', mb: 2 }} />
              <Typography variant="h6" color="textSecondary" gutterBottom>
                هیچ طرح پس‌انداز ثبت نشده است
              </Typography>
              <Typography variant="body2" color="textSecondary" mb={3}>
                برای شروع، اولین طرح پس‌انداز خود را ایجاد کنید
              </Typography>
              <Button
                variant="contained"
                startIcon={<Add />}
                onClick={() => setAddDialogOpen(true)}
              >
                ایجاد طرح جدید
              </Button>
            </Paper>
          </Grid>
        )}
      </Grid>

      {/* Add Savings Plan Dialog */}
      <Dialog open={addDialogOpen} onClose={() => setAddDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>ایجاد طرح پس‌انداز جدید</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <TextField
              fullWidth
              label="نام طرح"
              placeholder="مثال: خرید خانه، سفر، ضروری"
              value={formData.plan_name}
              onChange={(e) => setFormData({...formData, plan_name: e.target.value})}
              margin="normal"
              required
            />
            
            <TextField
              fullWidth
              label="نوع طرح"
              placeholder="مثال: کوتاه‌مدت، بلندمدت، اضطراری"
              value={formData.plan_type}
              onChange={(e) => setFormData({...formData, plan_type: e.target.value})}
              margin="normal"
            />
            
            <TextField
              fullWidth
              label="مبلغ هدف (تومان)"
              type="number"
              value={formData.target_amount}
              onChange={(e) => setFormData({...formData, target_amount: e.target.value})}
              margin="normal"
              required
            />
            
            <TextField
              fullWidth
              label="واریز ماهانه (اختیاری)"
              type="number"
              placeholder="مثال: 500000"
              value={formData.monthly_contribution}
              onChange={(e) => setFormData({...formData, monthly_contribution: e.target.value})}
              margin="normal"
              helperText="مبلغی که قصد دارید هر ماه واریز کنید"
            />
            
            <TextField
              fullWidth
              label="تاریخ هدف (اختیاری)"
              type="date"
              value={formData.end_date}
              onChange={(e) => setFormData({...formData, end_date: e.target.value})}
              margin="normal"
              InputLabelProps={{ shrink: true }}
              helperText="تاریخی که می‌خواهید به هدف برسید"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddDialogOpen(false)}>انصراف</Button>
          <Button 
            onClick={handleAddPlan} 
            variant="contained"
            disabled={loading || !formData.plan_name || !formData.target_amount}
          >
            ایجاد طرح
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}