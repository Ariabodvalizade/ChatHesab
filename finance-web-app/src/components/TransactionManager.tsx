// src/components/TransactionManager.tsx
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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Card,
  CardContent,
  Fab,
} from '@mui/material';
import {
  Add,
  Edit,
  Delete,
  Mic,
  Send,
  TrendingUp,
  TrendingDown,
} from '@mui/icons-material';
import { useAuth } from '../context/AuthContext';
import { API_CONFIG, getAuthHeaders } from '../config/api';

interface Transaction {
  transaction_id: number;
  type: 'income' | 'expense';
  amount: number;
  category: string;
  description: string;
  transaction_date: string;
  account_name: string;
  bank_name: string;
}

interface Account {
  account_id: number;
  bank_name: string;
  account_name: string;
  current_balance: number;
}

interface Category {
  name: string;
  icon: string;
}

export default function TransactionManager() {
  const { token } = useAuth();
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [categories, setCategories] = useState<{expense: Category[], income: Category[]}>({expense: [], income: []});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  // Dialog states
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [aiDialogOpen, setAiDialogOpen] = useState(false);
  const [aiMessage, setAiMessage] = useState('');
  const [aiResult, setAiResult] = useState<any>(null);
  
  // Form states
  const [formData, setFormData] = useState({
    account_id: '',
    transaction_type: 'expense' as 'income' | 'expense',
    amount: '',
    category: '',
    description: '',
    transaction_date: '',
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    if (!token) return;
    
    setLoading(true);
    try {
      // Fetch all data in parallel
      const [transactionsRes, accountsRes, categoriesRes] = await Promise.all([
        fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.TRANSACTIONS}?limit=50`, {
          headers: getAuthHeaders(token),
        }),
        fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.ACCOUNTS}`, {
          headers: getAuthHeaders(token),
        }),
        fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.CATEGORIES}`, {
          headers: getAuthHeaders(token),
        }),
      ]);

      if (transactionsRes.ok && accountsRes.ok && categoriesRes.ok) {
        const [transactionsData, accountsData, categoriesData] = await Promise.all([
          transactionsRes.json(),
          accountsRes.json(),
          categoriesRes.json(),
        ]);

        setTransactions(transactionsData);
        setAccounts(accountsData);
        setCategories(categoriesData);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
      setError('خطا در دریافت اطلاعات');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    try { moment.loadPersian({ usePersianDigits: true, dialect: 'persian-modern' }); } catch {}
    setFormData((f) => ({ ...f, transaction_date: moment().format('jYYYY/jMM/jDD HH:mm') }));
  }, []);

  const handleAddTransaction = async () => {
    if (!token || !formData.account_id || !formData.amount || !formData.category) {
      setError('لطفاً تمام فیلدهای اجباری را پر کنید');
      return;
    }

    try {
      const m = moment(formData.transaction_date, 'jYYYY/jMM/jDD HH:mm');
      const isoDate = m.isValid() ? m.toDate().toISOString() : undefined;
      const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.TRANSACTIONS}`, {
        method: 'POST',
        headers: getAuthHeaders(token),
        body: JSON.stringify({
          account_id: parseInt(formData.account_id),
          transaction_type: formData.transaction_type,
          amount: parseFloat(formData.amount),
          category: formData.category,
          description: formData.description,
          transaction_date: isoDate,
        }),
      });

      if (response.ok) {
        setAddDialogOpen(false);
        setFormData({
          account_id: '',
          transaction_type: 'expense',
          amount: '',
          category: '',
          description: '',
          transaction_date: moment().format('jYYYY/jMM/jDD HH:mm'),
        });
        fetchData(); // Refresh data
      } else {
        const text = await response.text();
        setError(text || 'خطا در ثبت تراکنش');
      }
    } catch (error) {
      console.error('Error adding transaction:', error);
      setError('خطا در اتصال به سرور');
    }
  };

  const handleAiProcess = async () => {
    if (!token || !aiMessage.trim()) return;

    try {
      setLoading(true);
      const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.AI_PROCESS}`, {
        method: 'POST',
        headers: getAuthHeaders(token),
        body: JSON.stringify({ message: aiMessage }),
      });

      if (response.ok) {
        const result = await response.json();
        setAiResult(result);
      } else {
        setError('خطا در پردازش پیام');
      }
    } catch (error) {
      console.error('Error processing AI message:', error);
      setError('خطا در پردازش هوشمند');
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmAiTransaction = async () => {
    if (!token || !aiResult) return;

    try {
      const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.TRANSACTIONS}`, {
        method: 'POST',
        headers: getAuthHeaders(token),
        body: JSON.stringify({
          account_id: aiResult.account_id,
          transaction_type: aiResult.transaction_type,
          amount: aiResult.amount,
          category: aiResult.category,
          description: aiResult.description,
        }),
      });

      if (response.ok) {
        setAiDialogOpen(false);
        setAiMessage('');
        setAiResult(null);
        fetchData(); // Refresh data
      } else {
        setError('خطا در ثبت تراکنش');
      }
    } catch (error) {
      console.error('Error confirming AI transaction:', error);
      setError('خطا در تأیید تراکنش');
    }
  };

  const formatAmount = (amount: number) => {
    return new Intl.NumberFormat('fa-IR').format(amount) + ' تومان';
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('fa-IR');
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          مدیریت تراکنش‌ها
        </Typography>
        <Box>
          <Button
            variant="outlined"
            startIcon={<Mic />}
            onClick={() => setAiDialogOpen(true)}
            sx={{ mr: 2 }}
          >
            پیام هوشمند
          </Button>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => setAddDialogOpen(true)}
          >
            تراکنش جدید
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {/* Quick Stats */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <TrendingUp color="success" sx={{ mr: 2, fontSize: 40 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    کل درآمد
                  </Typography>
                  <Typography variant="h6" color="success.main">
                    {formatAmount(
                      transactions
                        .filter(t => t.type === 'income')
                        .reduce((sum, t) => sum + t.amount, 0)
                    )}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center">
                <TrendingDown color="error" sx={{ mr: 2, fontSize: 40 }} />
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    کل هزینه
                  </Typography>
                  <Typography variant="h6" color="error.main">
                    {formatAmount(
                      transactions
                        .filter(t => t.type === 'expense')
                        .reduce((sum, t) => sum + t.amount, 0)
                    )}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Transactions Table */}
      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>تاریخ</TableCell>
                <TableCell>نوع</TableCell>
                <TableCell>مبلغ</TableCell>
                <TableCell>دسته‌بندی</TableCell>
                <TableCell>توضیحات</TableCell>
                <TableCell>حساب</TableCell>
                <TableCell>عملیات</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {transactions.map((transaction) => (
                <TableRow key={transaction.transaction_id}>
                  <TableCell>{formatDate(transaction.transaction_date)}</TableCell>
                  <TableCell>
                    <Chip
                      icon={transaction.type === 'income' ? <TrendingUp /> : <TrendingDown />}
                      label={transaction.type === 'income' ? 'درآمد' : 'هزینه'}
                      color={transaction.type === 'income' ? 'success' : 'error'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>{formatAmount(transaction.amount)}</TableCell>
                  <TableCell>{transaction.category}</TableCell>
                  <TableCell>{transaction.description}</TableCell>
                  <TableCell>{transaction.bank_name} - {transaction.account_name}</TableCell>
                  <TableCell>
                    <IconButton size="small" onClick={() => {/* Edit logic */}}>
                      <Edit />
                    </IconButton>
                    <IconButton size="small" onClick={() => {/* Delete logic */}}>
                      <Delete />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
              {transactions.length === 0 && (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    <Typography color="textSecondary">
                      هیچ تراکنشی ثبت نشده است
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* Add Transaction Dialog */}
      <Dialog open={addDialogOpen} onClose={() => setAddDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>افزودن تراکنش جدید</DialogTitle>
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
                <InputLabel>نوع تراکنش</InputLabel>
                <Select
                  value={formData.transaction_type}
                  onChange={(e) => setFormData({...formData, transaction_type: e.target.value as 'income' | 'expense', category: ''})}
                >
                  <MenuItem value="expense">هزینه</MenuItem>
                  <MenuItem value="income">درآمد</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                label="مبلغ (تومان)"
                type="number"
                value={formData.amount}
                onChange={(e) => setFormData({...formData, amount: e.target.value})}
              />
            </Grid>

            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>دسته‌بندی</InputLabel>
                <Select
                  value={formData.category}
                  onChange={(e) => setFormData({...formData, category: e.target.value})}
                >
                  {categories[formData.transaction_type]?.map((category) => (
                    <MenuItem key={category.name} value={category.name}>
                      {category.icon} {category.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
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

            <Grid item xs={12}>
              <TextField
                fullWidth
                label="تاریخ (هجری شمسی)"
                placeholder="1403/06/20 14:30"
                value={formData.transaction_date}
                onChange={(e) => setFormData({...formData, transaction_date: e.target.value})}
                helperText="فرمت: jYYYY/jMM/jDD HH:mm"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddDialogOpen(false)}>انصراف</Button>
          <Button onClick={handleAddTransaction} variant="contained">
            ثبت تراکنش
          </Button>
        </DialogActions>
      </Dialog>

      {/* AI Message Dialog */}
      <Dialog open={aiDialogOpen} onClose={() => setAiDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>پردازش پیام هوشمند</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            multiline
            rows={4}
            placeholder="مثال: دیروز ۱۵۰ هزار تومان قهوه از حساب ملت خریدم"
            value={aiMessage}
            onChange={(e) => setAiMessage(e.target.value)}
            sx={{ mt: 2 }}
          />
          
          {aiResult && (
            <Box mt={3} p={2} bgcolor="grey.100" borderRadius={1}>
              <Typography variant="h6" gutterBottom>نتیجه پردازش:</Typography>
              <Typography><strong>نوع:</strong> {aiResult.transaction_type === 'income' ? 'درآمد' : 'هزینه'}</Typography>
              <Typography><strong>مبلغ:</strong> {formatAmount(aiResult.amount)}</Typography>
              <Typography><strong>دسته‌بندی:</strong> {aiResult.category}</Typography>
              <Typography><strong>توضیحات:</strong> {aiResult.description}</Typography>
              {aiResult.account_name && (
                <Typography><strong>حساب:</strong> {aiResult.account_name}</Typography>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAiDialogOpen(false)}>انصراف</Button>
          {!aiResult ? (
            <Button 
              onClick={handleAiProcess} 
              variant="contained" 
              startIcon={<Send />}
              disabled={loading || !aiMessage.trim()}
            >
              پردازش
            </Button>
          ) : (
            <Button onClick={handleConfirmAiTransaction} variant="contained" color="success">
              تأیید و ثبت
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Container>
  );
}
