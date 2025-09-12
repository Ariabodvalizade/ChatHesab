// src/components/CheckManager.tsx
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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Grid,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
} from '@mui/material';
import {
  Add,
  Receipt,
  CheckCircle,
  Warning,
  Cancel,
} from '@mui/icons-material';
import { useAuth } from '../context/AuthContext';
import { API_CONFIG, getAuthHeaders } from '../config/api';

interface Check {
  check_id: number;
  type: 'issued' | 'received';
  amount: number;
  due_date: string;
  recipient_issuer: string;
  description: string;
  status: 'pending' | 'cleared' | 'bounced' | 'cancelled';
  account_name: string;
  bank_name: string;
}

interface Account {
  account_id: number;
  bank_name: string;
  account_name: string;
}

export default function CheckManager() {
  const { token } = useAuth();
  const [checks, setChecks] = useState<Check[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  
  const [formData, setFormData] = useState({
    account_id: '',
    type: 'issued' as 'issued' | 'received',
    amount: '',
    due_date: '',
    recipient_issuer: '',
    description: '',
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    if (!token) return;
    
    setLoading(true);
    try {
      const [checksRes, accountsRes] = await Promise.all([
        fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.CHECKS}`, {
          headers: getAuthHeaders(token),
        }),
        fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.ACCOUNTS}`, {
          headers: getAuthHeaders(token),
        }),
      ]);

      if (checksRes.ok && accountsRes.ok) {
        const [checksData, accountsData] = await Promise.all([
          checksRes.json(),
          accountsRes.json(),
        ]);

        setChecks(checksData);
        setAccounts(accountsData);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
      setError('خطا در دریافت اطلاعات');
    } finally {
      setLoading(false);
    }
  };

  const handleAddCheck = async () => {
    if (!token || !formData.account_id || !formData.amount || !formData.due_date) {
      setError('لطفاً تمام فیلدهای اجباری را پر کنید');
      return;
    }

    try {
      const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.CHECKS}`, {
        method: 'POST',
        headers: getAuthHeaders(token),
        body: JSON.stringify({
          account_id: parseInt(formData.account_id),
          type: formData.type,
          amount: parseFloat(formData.amount),
          due_date: formData.due_date,
          recipient_issuer: formData.recipient_issuer,
          description: formData.description,
        }),
      });

      if (response.ok) {
        setAddDialogOpen(false);
        setFormData({
          account_id: '',
          type: 'issued',
          amount: '',
          due_date: '',
          recipient_issuer: '',
          description: '',
        });
        fetchData();
      } else {
        setError('خطا در ثبت چک');
      }
    } catch (error) {
      console.error('Error adding check:', error);
      setError('خطا در اتصال به سرور');
    }
  };

  const formatAmount = (amount: number) => {
    return new Intl.NumberFormat('fa-IR').format(amount) + ' تومان';
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('fa-IR');
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'cleared':
        return <CheckCircle color="success" />;
      case 'bounced':
        return <Cancel color="error" />;
      case 'cancelled':
        return <Cancel color="warning" />;
      default:
        return <Warning color="warning" />;
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'pending':
        return 'در انتظار';
      case 'cleared':
        return 'پاس شده';
      case 'bounced':
        return 'برگشتی';
      case 'cancelled':
        return 'لغو شده';
      default:
        return status;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'cleared':
        return 'success';
      case 'bounced':
        return 'error';
      case 'cancelled':
        return 'warning';
      default:
        return 'default';
    }
  };

  const isOverdue = (dueDate: string, status: string) => {
    if (status !== 'pending') return false;
    return new Date(dueDate) < new Date();
  };

  const pendingChecks = checks.filter(c => c.status === 'pending');
  const overdueChecks = pendingChecks.filter(c => isOverdue(c.due_date, c.status));

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          مدیریت چک‌ها
        </Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => setAddDialogOpen(true)}
        >
          چک جدید
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
                <Receipt color="primary" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    کل چک‌ها
                  </Typography>
                  <Typography variant="h6">
                    {checks.length}
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
                <Warning color="warning" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    در انتظار
                  </Typography>
                  <Typography variant="h6" color="warning.main">
                    {pendingChecks.length}
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
                <Cancel color="error" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    سررسید گذشته
                  </Typography>
                  <Typography variant="h6" color="error.main">
                    {overdueChecks.length}
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
                <CheckCircle color="success" sx={{ mr: 2 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    پاس شده
                  </Typography>
                  <Typography variant="h6" color="success.main">
                    {checks.filter(c => c.status === 'cleared').length}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Checks Table */}
      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>نوع</TableCell>
                <TableCell>مبلغ</TableCell>
                <TableCell>تاریخ سررسید</TableCell>
                <TableCell>صادرکننده/دریافت‌کننده</TableCell>
                <TableCell>وضعیت</TableCell>
                <TableCell>حساب</TableCell>
                <TableCell>توضیحات</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {checks.map((check) => (
                <TableRow 
                  key={check.check_id}
                  sx={{
                    backgroundColor: isOverdue(check.due_date, check.status) ? 'error.50' : 'inherit'
                  }}
                >
                  <TableCell>
                    <Chip
                      label={check.type === 'issued' ? 'صادر شده' : 'دریافتی'}
                      color={check.type === 'issued' ? 'warning' : 'info'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>{formatAmount(check.amount)}</TableCell>
                  <TableCell>
                    <Box display="flex" alignItems="center">
                      {formatDate(check.due_date)}
                      {isOverdue(check.due_date, check.status) && (
                        <Warning color="error" sx={{ ml: 1, fontSize: 16 }} />
                      )}
                    </Box>
                  </TableCell>
                  <TableCell>{check.recipient_issuer}</TableCell>
                  <TableCell>
                    <Chip
                      icon={getStatusIcon(check.status)}
                      label={getStatusLabel(check.status)}
                      color={getStatusColor(check.status) as any}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>{check.bank_name} - {check.account_name}</TableCell>
                  <TableCell>{check.description}</TableCell>
                </TableRow>
              ))}
              {checks.length === 0 && (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    <Typography color="textSecondary">
                      هیچ چکی ثبت نشده است
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* Add Check Dialog */}
      <Dialog open={addDialogOpen} onClose={() => setAddDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>افزودن چک جدید</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>حساب بانکی</InputLabel>
                <Select
                  value={formData.account_id}
                  onChange={(e) => setFormData({...formData, account_id: e.target.value})}
                >
                  {accounts.map((account) => (
                    <MenuItem key={account.account_id} value={account.account_id}>
                      {account.bank_name} - {account.account_name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>نوع چک</InputLabel>
                <Select
                  value={formData.type}
                  onChange={(e) => setFormData({...formData, type: e.target.value as 'issued' | 'received'})}
                >
                  <MenuItem value="issued">صادر شده (پرداختی)</MenuItem>
                  <MenuItem value="received">دریافتی</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={6}>
              <TextField
                fullWidth
                label="مبلغ (تومان)"
                type="number"
                value={formData.amount}
                onChange={(e) => setFormData({...formData, amount: e.target.value})}
              />
            </Grid>

            <Grid item xs={6}>
              <TextField
                fullWidth
                label="تاریخ سررسید"
                type="date"
                value={formData.due_date}
                onChange={(e) => setFormData({...formData, due_date: e.target.value})}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                label={formData.type === 'issued' ? 'دریافت‌کننده' : 'صادرکننده'}
                value={formData.recipient_issuer}
                onChange={(e) => setFormData({...formData, recipient_issuer: e.target.value})}
              />
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                label="توضیحات"
                multiline
                rows={2}
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddDialogOpen(false)}>انصراف</Button>
          <Button onClick={handleAddCheck} variant="contained">
            ثبت چک
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}