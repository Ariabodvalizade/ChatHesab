// src/components/AccountManager.tsx
import React, { useState, useEffect } from 'react';
import moment from 'moment-jalaali';
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
  CardActions,
  Chip,
  IconButton,
  Alert,
  InputAdornment,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Collapse,
} from '@mui/material';
import {
  Add,
  Edit,
  Delete,
  AccountBalance,
  
  TrendingUp,
  TrendingDown,
  ExpandMore,
  ExpandLess,
  SwapHoriz,
} from '@mui/icons-material';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { AdapterDateFnsJalali } from '@mui/x-date-pickers/AdapterDateFnsJalali';
import { useAuth } from '../context/AuthContext';
import { API_CONFIG, getAuthHeaders } from '../config/api';

interface Transaction {
  transaction_id: number;
  type: string;
  amount: number;
  category: string;
  description: string;
  transaction_date: string;
}

interface Account {
  account_id: number;
  bank_name: string;
  account_name: string;
  initial_balance: number;
  current_balance: number;
  is_active: boolean;
  created_at: string;
}

export default function AccountManager() {
  const { token } = useAuth();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [transactionsDialogOpen, setTransactionsDialogOpen] = useState(false);
  const [selectedAccount, setSelectedAccount] = useState<Account | null>(null);
  const [transactions, setTransactions] = useState<any[]>([]);
  const [editTxDialogOpen, setEditTxDialogOpen] = useState(false);
  const [editTx, setEditTx] = useState<Transaction | null>(null);
  const [editTxDate, setEditTxDate] = useState<Date | null>(null);
  const [editTxHour, setEditTxHour] = useState<string>('');
  const [editTxMinute, setEditTxMinute] = useState<string>('');
  
  const [expandedAccount, setExpandedAccount] = useState<number | null>(null);
  const [accountTransactions, setAccountTransactions] = useState<{ [key: number]: Transaction[] }>({});
  
  const [formData, setFormData] = useState({
    bank_name: '',
    account_name: '',
    initial_balance: '',
  });

  useEffect(() => {
    try { moment.loadPersian({ usePersianDigits: true, dialect: 'persian-modern' }); } catch {}
    fetchAccounts();
  }, []);

  const fetchAccountTransactions = async (accountId: number) => {
    if (!token) return;
    
    try {
      const response = await fetch(
        `${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.TRANSACTIONS}?account_id=${accountId}&limit=50`,
        {
          headers: getAuthHeaders(token),
        }
      );

      if (response.ok) {
        const data = await response.json();
        setAccountTransactions(prev => ({
          ...prev,
          [accountId]: data
        }));
      } else {
        setError('خطا در دریافت تراکنش‌ها');
      }
    } catch (error) {
      console.error('Error fetching transactions:', error);
      setError('خطا در اتصال به سرور');
    }
  };

  const handleViewTransactions = async (accountId: number) => {
    if (expandedAccount === accountId) {
      setExpandedAccount(null);
    } else {
      setExpandedAccount(accountId);
      if (!accountTransactions[accountId]) {
        await fetchAccountTransactions(accountId);
      }
    }
  };

  const formatDate = (dateString: string) => {
    return moment(dateString).format('jYYYY/jMM/jDD HH:mm');
  };

  const getTransactionColor = (type: string) => {
    return type === 'income' ? 'success' : 'error';
  };

  const getTransactionTypeText = (type: string) => {
    return type === 'income' ? 'درآمد' : 'هزینه';
  };

  const fetchAccounts = async () => {
    if (!token) return;
    
    setLoading(true);
    try {
      const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.ACCOUNTS}`, {
        headers: getAuthHeaders(token),
      });

      if (response.ok) {
        const data = await response.json();
        setAccounts(data);
      } else {
        setError('خطا در دریافت حساب‌ها');
      }
    } catch (error) {
      console.error('Error fetching accounts:', error);
      setError('خطا در اتصال به سرور');
    } finally {
      setLoading(false);
    }
  };

  const handleAddAccount = async () => {
    if (!token || !formData.bank_name || !formData.account_name) {
      setError('لطفاً نام بانک و نام حساب را وارد کنید');
      return;
    }

    try {
      setLoading(true);
      const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.ACCOUNTS}`, {
        method: 'POST',
        headers: getAuthHeaders(token),
        body: JSON.stringify({
          bank_name: formData.bank_name,
          account_name: formData.account_name,
          initial_balance: parseFloat(formData.initial_balance) || 0,
        }),
      });

      if (response.ok) {
        setAddDialogOpen(false);
        setFormData({
          bank_name: '',
          account_name: '',
          initial_balance: '',
        });
        fetchAccounts(); // Refresh accounts
      } else {
        setError('خطا در ایجاد حساب');
      }
    } catch (error) {
      console.error('Error adding account:', error);
      setError('خطا در اتصال به سرور');
    } finally {
      setLoading(false);
    }
  };

  const formatAmount = (amount: number) => {
    return new Intl.NumberFormat('fa-IR').format(amount);
  };

  const getBalanceColor = (balance: number) => {
    if (balance > 0) return 'success';
    if (balance < 0) return 'error';
    return 'default';
  };

  const getBalanceIcon = (balance: number) => {
    if (balance > 0) return <TrendingUp />;
    if (balance < 0) return <TrendingDown />;
    return <AccountBalance />;
  };

  const totalBalance = accounts.reduce((sum, account) => sum + account.current_balance, 0);

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          مدیریت حساب‌های بانکی
        </Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => setAddDialogOpen(true)}
        >
          حساب جدید
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {/* Total Balance Summary */}
      <Paper sx={{ p: 3, mb: 4 }}>
        <Box display="flex" alignItems="center" justifyContent="center">
          <AccountBalance sx={{ fontSize: 40, mr: 2, color: 'primary.main' }} />
          <Box textAlign="center">
            <Typography variant="h6" color="textSecondary">
              موجودی کل حساب‌ها
            </Typography>
            <Typography variant="h4" component="div">
              <Chip
                icon={getBalanceIcon(totalBalance)}
                label={`${formatAmount(totalBalance)} تومان`}
                color={getBalanceColor(totalBalance)}
                size="medium"
                sx={{ fontSize: '1.2rem', p: 2 }}
              />
            </Typography>
          </Box>
        </Box>
      </Paper>

      {/* Accounts Grid */}
      <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
        {accounts.map((account) => (
          <Box key={account.account_id} sx={{ flex: '1 1 350px', minWidth: '350px' }}>
            <Card elevation={3}>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <AccountBalance color="primary" sx={{ mr: 2 }} />
                  <Box flex={1}>
                    <Typography variant="h6" component="div" noWrap>
                      {account.bank_name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" noWrap>
                      {account.account_name}
                    </Typography>
                  </Box>
                </Box>

                <Box mb={2}>
                  <Typography variant="body2" color="text.secondary">
                    موجودی فعلی
                  </Typography>
                  <Typography variant="h6" component="div">
                    <Chip
                      icon={getBalanceIcon(account.current_balance)}
                      label={`${formatAmount(account.current_balance)} تومان`}
                      color={getBalanceColor(account.current_balance)}
                      size="small"
                    />
                  </Typography>
                </Box>

                <Box mb={2}>
                  <Typography variant="body2" color="text.secondary">
                    موجودی اولیه
                  </Typography>
                  <Typography variant="body2">
                    {formatAmount(account.initial_balance)} تومان
                  </Typography>
                </Box>

                <Box>
                  <Typography variant="body2" color="text.secondary">
                    تاریخ ایجاد
                  </Typography>
                  <Typography variant="body2">
                    {new Date(account.created_at).toLocaleDateString('fa-IR')}
                  </Typography>
                </Box>
              </CardContent>

              <CardActions>
                <Button
                  size="small"
                  startIcon={expandedAccount === account.account_id ? <ExpandLess /> : <ExpandMore />}
                  onClick={() => handleViewTransactions(account.account_id)}
                >
                  {expandedAccount === account.account_id ? 'مخفی کردن' : 'مشاهده تراکنش‌ها'}
                </Button>
                <IconButton size="small" onClick={() => {/* Edit account */}}>
                  <Edit />
                </IconButton>
                <IconButton size="small" onClick={() => {/* Delete account */}}>
                  <Delete />
                </IconButton>
              </CardActions>
            </Card>
            
            {/* Transactions Collapse */}
            <Collapse in={expandedAccount === account.account_id}>
              <Card sx={{ mt: 1, bgcolor: 'grey.50' }}>
                <CardContent>
                  <Box display="flex" alignItems="center" mb={2}>
                    <SwapHoriz color="primary" sx={{ mr: 1 }} />
                    <Typography variant="h6">
                      تراکنش‌های {account.account_name}
                    </Typography>
                  </Box>
                  
                  {accountTransactions[account.account_id] && accountTransactions[account.account_id].length > 0 ? (
                    <TableContainer>
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>تاریخ</TableCell>
                            <TableCell>نوع</TableCell>
                            <TableCell>دسته‌بندی</TableCell>
                            <TableCell align="right">مبلغ</TableCell>
                            <TableCell>توضیحات</TableCell>
                            <TableCell>عملیات</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {accountTransactions[account.account_id].map((transaction) => (
                            <TableRow key={transaction.transaction_id}>
                              <TableCell>{formatDate(transaction.transaction_date)}</TableCell>
                              <TableCell>
                                <Chip
                                  label={getTransactionTypeText(transaction.type)}
                                  color={getTransactionColor(transaction.type)}
                                  size="small"
                                />
                              </TableCell>
                              <TableCell>{transaction.category}</TableCell>
                              <TableCell align="right">
                                <Typography
                                  color={transaction.type === 'income' ? 'success.main' : 'error.main'}
                                  fontWeight="bold"
                                >
                                  {transaction.type === 'income' ? '+' : '-'}{formatAmount(transaction.amount)} تومان
                                </Typography>
                              </TableCell>
                              <TableCell>{transaction.description || '-'}</TableCell>
                              <TableCell>
                                <IconButton size="small" onClick={() => {
                                  setEditTx(transaction);
                                  const d = new Date(transaction.transaction_date);
                                  setEditTxDate(d);
                                  setEditTxHour(String(d.getHours()).padStart(2, '0'));
                                  setEditTxMinute(String(d.getMinutes()).padStart(2, '0'));
                                  setEditTxDialogOpen(true);
                                }}>
                                  <Edit />
                                </IconButton>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  ) : (
                    <Box textAlign="center" py={3}>
                      <SwapHoriz sx={{ fontSize: 48, color: 'grey.400', mb: 1 }} />
                      <Typography color="textSecondary">
                        هیچ تراکنشی در این حساب ثبت نشده است
                      </Typography>
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Collapse>
          </Box>
        ))}

        {accounts.length === 0 && (
          <Box sx={{ width: '100%' }}>
            <Paper sx={{ p: 4, textAlign: 'center' }}>
              <AccountBalance sx={{ fontSize: 80, color: 'grey.400', mb: 2 }} />
              <Typography variant="h6" color="textSecondary" gutterBottom>
                هیچ حساب بانکی ثبت نشده است
              </Typography>
              <Typography variant="body2" color="textSecondary" mb={3}>
                برای شروع، اولین حساب بانکی خود را ثبت کنید
              </Typography>
              <Button
                variant="contained"
                startIcon={<Add />}
                onClick={() => setAddDialogOpen(true)}
              >
                ثبت اولین حساب
              </Button>
            </Paper>
          </Box>
        )}
      </Box>

  {/* Add Account Dialog */}
  <Dialog open={addDialogOpen} onClose={() => setAddDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>افزودن حساب بانکی جدید</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <TextField
              fullWidth
              label="نام بانک"
              placeholder="مثال: ملت، ملی، صادرات، پاسارگاد"
              value={formData.bank_name}
              onChange={(e) => setFormData({...formData, bank_name: e.target.value})}
              margin="normal"
              required
            />
            
            <TextField
              fullWidth
              label="نام حساب"
              placeholder="مثال: حساب جاری، پس‌انداز، ۱۲۳۴"
              value={formData.account_name}
              onChange={(e) => setFormData({...formData, account_name: e.target.value})}
              margin="normal"
              required
            />
            
            <TextField
              fullWidth
              label="موجودی اولیه"
              type="number"
              placeholder="0"
              value={formData.initial_balance}
              onChange={(e) => setFormData({...formData, initial_balance: e.target.value})}
              margin="normal"
              InputProps={{
                endAdornment: <InputAdornment position="end">تومان</InputAdornment>,
              }}
              helperText="موجودی فعلی حساب شما (اختیاری)"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddDialogOpen(false)}>انصراف</Button>
          <Button 
            onClick={handleAddAccount} 
            variant="contained"
            disabled={loading || !formData.bank_name || !formData.account_name}
          >
            ایجاد حساب
          </Button>
        </DialogActions>
  </Dialog>

  {/* Edit Transaction Dialog */}
  <Dialog open={editTxDialogOpen} onClose={() => setEditTxDialogOpen(false)} maxWidth="sm" fullWidth>
    <DialogTitle>ویرایش تراکنش</DialogTitle>
    <DialogContent>
      {editTx && (
        <Box sx={{ mt: 2 }}>
          <TextField
            fullWidth
            label="مبلغ (تومان)"
            type="number"
            value={editTx.amount}
            onChange={(e) => setEditTx({ ...editTx, amount: Number(e.target.value) })}
            margin="normal"
          />
          <TextField
            fullWidth
            label="دسته‌بندی"
            value={editTx.category}
            onChange={(e) => setEditTx({ ...editTx, category: e.target.value })}
            margin="normal"
          />
          <TextField
            fullWidth
            label="توضیحات"
            value={editTx.description || ''}
            onChange={(e) => setEditTx({ ...editTx, description: e.target.value })}
            margin="normal"
          />
          <LocalizationProvider dateAdapter={AdapterDateFnsJalali}>
            <DatePicker
              label="تاریخ (هجری شمسی)"
              value={editTxDate}
              onChange={(newValue) => setEditTxDate(newValue)}
              slotProps={{ textField: { fullWidth: true, margin: 'normal' }}}
            />
          </LocalizationProvider>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <TextField
              label="ساعت"
              type="number"
              inputProps={{ min: 0, max: 23 }}
              value={editTxHour}
              onChange={(e) => {
                const v = e.target.value;
                if (/^\d{0,2}$/.test(v)) setEditTxHour(v);
              }}
              sx={{ flex: 1 }}
            />
            <TextField
              label="دقیقه"
              type="number"
              inputProps={{ min: 0, max: 59 }}
              value={editTxMinute}
              onChange={(e) => {
                const v = e.target.value;
                if (/^\d{0,2}$/.test(v)) setEditTxMinute(v);
              }}
              sx={{ flex: 1 }}
            />
          </Box>
        </Box>
      )}
    </DialogContent>
    <DialogActions>
      <Button onClick={() => setEditTxDialogOpen(false)}>انصراف</Button>
      <Button 
        onClick={async () => {
          if (!token || !editTx) return;
          try {
            // Compose ISO datetime from selected date + hour/minute
            let isoDate: string | undefined = undefined;
            if (editTxDate) {
              const d = new Date(editTxDate);
              const h = Math.min(23, Math.max(0, parseInt(editTxHour || '0', 10)));
              const m = Math.min(59, Math.max(0, parseInt(editTxMinute || '0', 10)));
              d.setHours(h, m, 0, 0);
              isoDate = d.toISOString();
            }

            const resp = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.TRANSACTIONS}/${editTx.transaction_id}`, {
              method: 'PUT',
              headers: getAuthHeaders(token),
              body: JSON.stringify({
                amount: editTx.amount,
                category: editTx.category,
                description: editTx.description,
                transaction_date: isoDate ?? editTx.transaction_date,
                transaction_type: editTx.type,
              }),
            });
            if (resp.ok) {
              setEditTxDialogOpen(false);
              if (expandedAccount) await fetchAccountTransactions(expandedAccount);
            } else {
              const text = await resp.text();
              setError(text || 'خطا در ذخیره تغییرات تراکنش');
            }
          } catch (e) { console.error(e); }
        }} 
        variant="contained" color="success"
      >
        ذخیره تغییرات
      </Button>
    </DialogActions>
  </Dialog>
    </Container>
  );
}
