// src/components/ChatInterface.tsx
import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Paper,
  TextField,
  IconButton,
  Typography,
  Avatar,
  Chip,
  Button,
  Card,
  CardContent,
  Divider,
  CircularProgress,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Send as SendIcon,
  Person as PersonIcon,
  SmartToy as BotIcon,
  CheckCircle as CheckIcon,
  Cancel as CancelIcon,
  Edit as EditIcon,
  AccountBalance as AccountIcon,
} from '@mui/icons-material';
import { useAuth } from '../context/AuthContext';
import { API_CONFIG, getAuthHeaders } from '../config/api';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  aiResult?: any;
}

interface TransactionConfirmation {
  show: boolean;
  data: any;
  editMode: boolean;
  editedAmount: string;
  editedAccountId: number;
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: 'سلام! من دستیار مالی هوشمند شما هستم. می‌توانید تراکنش‌های خود را به صورت طبیعی برایم بنویسید.\n\nمثال:\n• "50 هزار تومان قهوه خریدم"\n• "2 میلیون حقوق گرفتم"\n• "دیروز 200 تومان اتوبوس"',
      sender: 'bot',
      timestamp: new Date(),
    },
  ]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [confirmation, setConfirmation] = useState<TransactionConfirmation>({
    show: false,
    data: null,
    editMode: false,
    editedAmount: '',
    editedAccountId: 0,
  });
  
  interface AccountActionConfirmation {
    show: boolean;
    action: 'create' | 'update' | 'delete';
    bank_name?: string;
    account_name?: string;
    initial_balance?: number;
    account_id?: number;
    editMode?: boolean;
  }
  const [accountAction, setAccountAction] = useState<AccountActionConfirmation>({ show: false, action: 'create' });
  const [accounts, setAccounts] = useState<any[]>([]);
  const [accountBalance, setAccountBalance] = useState<number | null>(null);
  const [showNewAccountForm, setShowNewAccountForm] = useState(false);
  const [newAccount, setNewAccount] = useState({ bank_name: '', account_name: '', initial_balance: '' });
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { token } = useAuth();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load accounts on component mount
  useEffect(() => {
    const loadAccounts = async () => {
      if (!token) return;
      
      try {
        const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.ACCOUNTS}`, {
          headers: getAuthHeaders(token),
        });
        
        if (response.ok) {
          const accountsData = await response.json();
          setAccounts(accountsData);
        }
      } catch (error) {
        console.error('Error loading accounts:', error);
      }
    };

    loadAccounts();
  }, [token]);

  const handleSendMessage = async () => {
    if (!inputText.trim() || !token) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputText,
      sender: 'user',
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setLoading(true);

    try {
      // Process message with AI
      const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.AI_PROCESS}`, {
        method: 'POST',
        headers: getAuthHeaders(token),
        body: JSON.stringify({ message: inputText }),
      });

      if (response.ok) {
        const result = await response.json();
        
        // Create bot response message
        const botMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: result.response_message || 'پیام شما پردازش شد.',
          sender: 'bot',
          timestamp: new Date(),
          aiResult: result.success ? result : null,
        };

        setMessages(prev => [...prev, botMessage]);

        // If it's a transaction, show confirmation
        if (result.success && result.type === 'transaction') {
          setConfirmation({
            show: true,
            data: result,
            editMode: false,
            editedAmount: result.amount.toString(),
            editedAccountId: result.account_id,
          });
          // Load account balance
          if (result.account_id) await loadAccountBalance(result.account_id);
          if (result.suggest_new_account) {
            setShowNewAccountForm(true);
            setNewAccount({
              bank_name: result.suggest_new_account.bank_name || '',
              account_name: result.suggest_new_account.account_name || '',
              initial_balance: ''
            });
          } else {
            setShowNewAccountForm(false);
          }
        } else if (result.success && result.type === 'account') {
          // Handle account operations
          setAccountAction({
            show: true,
            action: result.action,
            bank_name: result.bank_name,
            account_name: result.account_name,
            initial_balance: result.initial_balance,
            account_id: result.account_id,
            editMode: false,
          });
        }
      } else {
        throw new Error('خطا در پردازش پیام');
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: 'متأسفانه خطایی رخ داد. لطفاً دوباره تلاش کنید.',
        sender: 'bot',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const loadAccountBalance = async (accountId: number) => {
    if (!token) return;
    
    try {
      const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.ACCOUNTS}`, {
        headers: getAuthHeaders(token),
      });
      
      if (response.ok) {
        const accountsData = await response.json();
        const account = accountsData.find((acc: any) => acc.account_id === accountId);
        if (account) {
          setAccountBalance(account.current_balance);
        }
      }
    } catch (error) {
      console.error('Error loading account balance:', error);
    }
  };

  const handleConfirmTransaction = async () => {
    if (!token || !confirmation.data) return;

    const finalAmount = confirmation.editMode 
      ? parseFloat(confirmation.editedAmount) 
      : confirmation.data.amount;
    
    const finalAccountId = confirmation.editMode 
      ? confirmation.editedAccountId 
      : confirmation.data.account_id;

    try {
      // Build payload to ensure precise timestamp from backend (omit date to let server set now)
      const payload: any = {
        account_id: finalAccountId,
        transaction_type: confirmation.data.transaction_type,
        amount: finalAmount,
        category: confirmation.data.category,
        description: confirmation.data.description,
      };
      const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.TRANSACTIONS}`, {
        method: 'POST',
        headers: getAuthHeaders(token),
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        // Calculate new balance
        const balanceChange = confirmation.data.transaction_type === 'income' 
          ? finalAmount 
          : -finalAmount;
        const newBalance = (accountBalance || 0) + balanceChange;
        
        const successMessage: Message = {
          id: Date.now().toString(),
          text: `✅ تراکنش با موفقیت ثبت شد!\n\n💰 موجودی جدید حساب: ${formatAmount(newBalance)}`,
          sender: 'bot',
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, successMessage]);
        setConfirmation({ show: false, data: null, editMode: false, editedAmount: '', editedAccountId: 0 });
        setAccountBalance(null);
      } else {
        const text = await response.text();
        const msg = text || 'خطا در ثبت تراکنش';
        throw new Error(msg);
      }
    } catch (error) {
      console.error('Error confirming transaction:', error);
      const message = (error instanceof Error) ? error.message : 'خطا در ثبت تراکنش';
      const errorMessage: Message = {
        id: Date.now().toString(),
        text: '❌ ' + message,
        sender: 'bot',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  const handleCancelTransaction = () => {
    setConfirmation({ show: false, data: null, editMode: false, editedAmount: '', editedAccountId: 0 });
    setAccountBalance(null);
    const cancelMessage: Message = {
      id: Date.now().toString(),
      text: 'تراکنش لغو شد. اگر اطلاعات اشتباه بود، می‌توانید دوباره بنویسید.',
      sender: 'bot',
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, cancelMessage]);
  };

  const handleEditTransaction = () => {
    setConfirmation(prev => ({
      ...prev,
      editMode: true,
    }));
  };

  const handleSaveEdit = () => {
    setConfirmation(prev => ({
      ...prev,
      editMode: false,
    }));
    // Reload account balance for the new account
    loadAccountBalance(confirmation.editedAccountId);
  };

  const getSelectedAccount = () => {
    const accountId = confirmation.editMode ? confirmation.editedAccountId : confirmation.data?.account_id;
    return accounts.find(acc => acc.account_id === accountId);
  };

  const calculateNewBalance = () => {
    if (accountBalance === null || !confirmation.data) return null;
    
    const amount = confirmation.editMode 
      ? parseFloat(confirmation.editedAmount) || 0 
      : confirmation.data.amount;
    
    const balanceChange = confirmation.data.transaction_type === 'income' ? amount : -amount;
    return accountBalance + balanceChange;
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const formatAmount = (amount: number) => {
    return new Intl.NumberFormat('fa-IR').format(amount) + ' تومان';
  };

  const getTransactionTypeColor = (type: string) => {
    return type === 'income' ? 'success' : 'error';
  };

  const getTransactionTypeText = (type: string) => {
    return type === 'income' ? 'درآمد' : 'هزینه';
  };

  const confirmAccountAction = async () => {
    if (!token || !accountAction.show) return;
    try {
      if (accountAction.action === 'create') {
        const body = {
          bank_name: accountAction.bank_name || 'بانک',
          account_name: accountAction.account_name || 'حساب جدید',
          initial_balance: accountAction.initial_balance || 0,
        };
        const resp = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.ACCOUNTS}`, {
          method: 'POST',
          headers: getAuthHeaders(token),
          body: JSON.stringify(body),
        });
        if (resp.ok) {
          setMessages(prev => [...prev, {
            id: Date.now().toString(),
            text: '✅ حساب با موفقیت ساخته شد.',
            sender: 'bot',
            timestamp: new Date(),
          }]);
          setAccountAction({ show: false, action: 'create' });
          // Reload accounts
          const accountsResponse = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.ACCOUNTS}`, { headers: getAuthHeaders(token) });
          if (accountsResponse.ok) setAccounts(await accountsResponse.json());
          return;
        }
        throw new Error('Create account failed');
      } else if (accountAction.action === 'update') {
        if (!accountAction.account_id) throw new Error('account_id required');
        const payload: any = {};
        if (accountAction.bank_name) payload.bank_name = accountAction.bank_name;
        if (accountAction.account_name) payload.account_name = accountAction.account_name;
        if (typeof accountAction.initial_balance === 'number') payload.initial_balance = accountAction.initial_balance;
        const resp = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.ACCOUNTS}/${accountAction.account_id}`, {
          method: 'PUT',
          headers: getAuthHeaders(token),
          body: JSON.stringify(payload),
        });
        if (resp.ok) {
          setMessages(prev => [...prev, { id: Date.now().toString(), text: '✏️ حساب با موفقیت ویرایش شد.', sender: 'bot', timestamp: new Date() }]);
          setAccountAction({ show: false, action: 'create' });
          const accountsResponse = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.ACCOUNTS}`, { headers: getAuthHeaders(token) });
          if (accountsResponse.ok) setAccounts(await accountsResponse.json());
          return;
        }
        throw new Error('Update account failed');
      } else if (accountAction.action === 'delete') {
        if (!accountAction.account_id) throw new Error('account_id required');
        const resp = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.ACCOUNTS}/${accountAction.account_id}`, {
          method: 'DELETE',
          headers: getAuthHeaders(token),
        });
        if (resp.ok) {
          setMessages(prev => [...prev, { id: Date.now().toString(), text: '🗑️ حساب حذف شد.', sender: 'bot', timestamp: new Date() }]);
          setAccountAction({ show: false, action: 'create' });
          const accountsResponse = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.ACCOUNTS}`, { headers: getAuthHeaders(token) });
          if (accountsResponse.ok) setAccounts(await accountsResponse.json());
          return;
        }
        throw new Error('Delete account failed');
      }
    } catch (e) {
      console.error('Account action error:', e);
      setMessages(prev => [...prev, { id: Date.now().toString(), text: '❌ انجام عملیات حساب ناموفق بود.', sender: 'bot', timestamp: new Date() }]);
    }
  };

  const cancelAccountAction = () => {
    setAccountAction({ show: false, action: 'create' });
  }

  return (
    <Box sx={{ minHeight: '70vh', display: 'flex', flexDirection: 'column', mb: { xs: 8, md: 2 } }}>
      {/* Chat Header */}
      <Paper sx={{ p: 2, mb: 1 }}>
        <Box display="flex" alignItems="center" gap={2}>
          <BotIcon color="primary" />
          <Typography variant="h6">
            💬 چت با دستیار مالی هوشمند
          </Typography>
        </Box>
      </Paper>

      {/* Messages Container */}
      <Paper 
        sx={{ 
          flex: 1, 
          p: 2, 
          overflow: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: 2,
        }}
      >
        {messages.map((message) => (
          <Box
            key={message.id}
            sx={{
              display: 'flex',
              justifyContent: message.sender === 'user' ? 'flex-end' : 'flex-start',
              alignItems: 'flex-start',
              gap: 1,
            }}
          >
            {message.sender === 'bot' && (
              <Avatar sx={{ bgcolor: 'primary.main', width: 32, height: 32 }}>
                <BotIcon fontSize="small" />
              </Avatar>
            )}
            
            <Box sx={{ maxWidth: '70%' }}>
              <Paper
                sx={{
                  p: 2,
                  bgcolor: message.sender === 'user' ? 'primary.main' : 'grey.100',
                  color: message.sender === 'user' ? 'white' : 'text.primary',
                }}
              >
                <Typography variant="body1" sx={{ whiteSpace: 'pre-line' }}>
                  {message.text}
                </Typography>
              </Paper>

              {/* Show transaction details if available */}
              {message.aiResult && message.aiResult.type === 'transaction' && (
                <Card sx={{ mt: 1, border: 1, borderColor: 'divider' }}>
                  <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                    <Typography variant="subtitle2" gutterBottom>
                      جزئیات تراکنش:
                    </Typography>
                    <Box display="flex" flexWrap="wrap" gap={1}>
                      <Chip
                        label={getTransactionTypeText(message.aiResult.transaction_type)}
                        color={getTransactionTypeColor(message.aiResult.transaction_type)}
                        size="small"
                      />
                      <Chip
                        label={formatAmount(message.aiResult.amount)}
                        variant="outlined"
                        size="small"
                      />
                      <Chip
                        label={message.aiResult.category}
                        variant="outlined"
                        size="small"
                      />
                    </Box>
                  </CardContent>
                </Card>
              )}

              <Typography 
                variant="caption" 
                color="text.secondary" 
                sx={{ display: 'block', mt: 0.5, textAlign: message.sender === 'user' ? 'right' : 'left' }}
              >
                {message.timestamp.toLocaleTimeString('fa-IR', { 
                  hour: '2-digit', 
                  minute: '2-digit' 
                })}
              </Typography>
            </Box>

            {message.sender === 'user' && (
              <Avatar sx={{ bgcolor: 'secondary.main', width: 32, height: 32 }}>
                <PersonIcon fontSize="small" />
              </Avatar>
            )}
          </Box>
        ))}

        {loading && (
          <Box display="flex" justifyContent="flex-start" alignItems="center" gap={1}>
            <Avatar sx={{ bgcolor: 'primary.main', width: 32, height: 32 }}>
              <BotIcon fontSize="small" />
            </Avatar>
            <Paper sx={{ p: 2, bgcolor: 'grey.100' }}>
              <Box display="flex" alignItems="center" gap={1}>
                <CircularProgress size={16} />
                <Typography variant="body2">در حال پردازش...</Typography>
              </Box>
            </Paper>
          </Box>
        )}

        <div ref={messagesEndRef} />
      </Paper>

      {/* Transaction Confirmation Dialog */}
      {confirmation.show && confirmation.data && (
        <Paper sx={{ p: 2, mt: 1, border: 1, borderColor: 'warning.main' }}>
          <Alert severity="info" sx={{ mb: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              {confirmation.editMode ? 'ویرایش تراکنش:' : 'آیا می‌خواهید این تراکنش را ثبت کنید؟'}
            </Typography>
            
            {!confirmation.editMode ? (
              // Display Mode
              <>
                <Box display="flex" flexWrap="wrap" gap={1} mt={1}>
                  <Chip
                    label={getTransactionTypeText(confirmation.data.transaction_type)}
                    color={getTransactionTypeColor(confirmation.data.transaction_type)}
                    size="small"
                  />
                  <Chip
                    label={formatAmount(confirmation.data.amount)}
                    variant="outlined"
                    size="small"
                  />
                  <Chip
                    label={confirmation.data.category}
                    variant="outlined"
                    size="small"
                  />
                  {confirmation.data.account_name && (
                    <Chip
                      label={confirmation.data.account_name}
                      variant="outlined"
                      size="small"
                      icon={<AccountIcon />}
                    />
                  )}
                </Box>
                
                {/* Current Balance */}
                {accountBalance !== null && (
                  <Box sx={{ mt: 2, p: 1, bgcolor: 'grey.50', borderRadius: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      💰 موجودی فعلی: {formatAmount(accountBalance)}
                    </Typography>
                    <Typography variant="body2" color={confirmation.data.transaction_type === 'income' ? 'success.main' : 'error.main'}>
                      🔄 موجودی جدید: {calculateNewBalance() !== null ? formatAmount(calculateNewBalance()!) : 'در حال محاسبه...'}
                    </Typography>
                  </Box>
                )}
              </>
            ) : (
              // Edit Mode
              <Box sx={{ mt: 2 }}>
                <Box display="flex" gap={2} mb={2}>
                  <FormControl size="small" sx={{ minWidth: 200 }}>
                    <InputLabel>حساب</InputLabel>
                    <Select
                      value={confirmation.editedAccountId}
                      label="حساب"
                      onChange={(e) => {
                        if (e.target.value === 'new') {
                          setShowNewAccountForm(true);
                        } else {
                          setShowNewAccountForm(false);
                          setConfirmation(prev => ({ ...prev, editedAccountId: Number(e.target.value) }));
                        }
                      }}
                    >
                      <MenuItem value={'new'}>➕ افزودن حساب جدید…</MenuItem>
                      {accounts.map((account) => (
                        <MenuItem key={account.account_id} value={account.account_id}>
                          {account.bank_name} - {account.account_name}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                  
                  <TextField
                    size="small"
                    label="مبلغ (تومان)"
                    type="number"
                    value={confirmation.editedAmount}
                    onChange={(e) => setConfirmation(prev => ({ ...prev, editedAmount: e.target.value }))}
                    sx={{ minWidth: 150 }}
                  />
                </Box>
                
                <Box display="flex" flexWrap="wrap" gap={1} mb={2}>
                  <Chip
                    label={getTransactionTypeText(confirmation.data.transaction_type)}
                    color={getTransactionTypeColor(confirmation.data.transaction_type)}
                    size="small"
                  />
                  <Chip
                    label={confirmation.data.category}
                    variant="outlined"
                    size="small"
                  />
                </Box>
                
                {/* New account inline form */}
                {showNewAccountForm && (
                  <Box sx={{ mt: 2, p: 1, border: '1px dashed', borderColor: 'divider', borderRadius: 1 }}>
                    <Typography variant="body2" sx={{ mb: 1 }}>افزودن حساب جدید</Typography>
                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                      <TextField size="small" label="نام بانک" value={newAccount.bank_name} onChange={(e) => setNewAccount({ ...newAccount, bank_name: e.target.value })} />
                      <TextField size="small" label="نام حساب" value={newAccount.account_name} onChange={(e) => setNewAccount({ ...newAccount, account_name: e.target.value })} />
                      <TextField size="small" label="موجودی اولیه" type="number" value={newAccount.initial_balance} onChange={(e) => setNewAccount({ ...newAccount, initial_balance: e.target.value })} />
                      <Button
                        variant="outlined"
                        onClick={async () => {
                          if (!token) return;
                          const resp = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.ACCOUNTS}`, {
                            method: 'POST',
                            headers: getAuthHeaders(token),
                            body: JSON.stringify({ bank_name: newAccount.bank_name || 'بانک', account_name: newAccount.account_name || 'حساب', initial_balance: parseFloat(newAccount.initial_balance || '0') || 0 })
                          });
                          if (resp.ok) {
                            const r = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.ACCOUNTS}`, { headers: getAuthHeaders(token) });
                            const list = await r.json();
                            setAccounts(list);
                            const last = list[list.length - 1];
                            setConfirmation(prev => ({ ...prev, editedAccountId: last.account_id }));
                            setShowNewAccountForm(false);
                          }
                        }}
                      >
                        ایجاد و انتخاب
                      </Button>
                    </Box>
                  </Box>
                )}

                {/* Balance Preview for Selected Account */}
                {accountBalance !== null && (
                  <Box sx={{ p: 1, bgcolor: 'grey.50', borderRadius: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      💰 موجودی فعلی: {formatAmount(accountBalance)}
                    </Typography>
                    <Typography variant="body2" color={confirmation.data.transaction_type === 'income' ? 'success.main' : 'error.main'}>
                      🔄 موجودی جدید: {calculateNewBalance() !== null ? formatAmount(calculateNewBalance()!) : 'در حال محاسبه...'}
                    </Typography>
                  </Box>
                )}
              </Box>
            )}
          </Alert>
          
          <Box display="flex" gap={2} justifyContent="center" flexWrap="wrap">
            {!confirmation.editMode ? (
              <>
                <Button
                  variant="contained"
                  color="success"
                  startIcon={<CheckIcon />}
                  onClick={handleConfirmTransaction}
                  disabled={!confirmation.data.account_id}
                >
                  تأیید و ثبت
                </Button>
                <Button
                  variant="outlined"
                  color="primary"
                  startIcon={<EditIcon />}
                  onClick={handleEditTransaction}
                >
                  ویرایش
                </Button>
                <Button
                  variant="outlined"
                  color="error"
                  startIcon={<CancelIcon />}
                  onClick={handleCancelTransaction}
                >
                  لغو
                </Button>
              </>
            ) : (
              <>
                <Button
                  variant="contained"
                  color="success"
                  startIcon={<CheckIcon />}
                  onClick={handleSaveEdit}
                >
                  ذخیره
                </Button>
                <Button
                  variant="outlined"
                  color="primary"
                  startIcon={<CheckIcon />}
                  onClick={handleConfirmTransaction}
                >
                  تأیید و ثبت
                </Button>
                <Button
                  variant="outlined"
                  color="error"
                  startIcon={<CancelIcon />}
                  onClick={handleCancelTransaction}
                >
                  لغو
                </Button>
              </>
            )}
          </Box>
        </Paper>
      )}

      {/* Account Action Confirmation */}
      {accountAction.show && (
        <Paper sx={{ p: 2, mt: 1, border: 1, borderColor: 'info.main' }}>
          <Alert severity="info" sx={{ mb: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              {accountAction.action === 'create' ? 'ایجاد حساب جدید' : accountAction.action === 'update' ? 'ویرایش حساب' : 'حذف حساب'}
            </Typography>
            <Box display="flex" flexWrap="wrap" gap={1} mt={1}>
              {accountAction.bank_name && <Chip label={`بانک: ${accountAction.bank_name}`} variant="outlined" size="small" />}
              {accountAction.account_name && <Chip label={`نام حساب: ${accountAction.account_name}`} variant="outlined" size="small" />}
              {typeof accountAction.initial_balance === 'number' && (
                <Chip label={`موجودی اولیه: ${formatAmount(accountAction.initial_balance)}`} variant="outlined" size="small" />
              )}
            </Box>
          </Alert>
          <Box display="flex" gap={2} justifyContent="center" flexWrap="wrap">
            <Button variant="contained" color={accountAction.action === 'delete' ? 'error' : 'success'} onClick={confirmAccountAction}>
              تایید
            </Button>
            <Button variant="outlined" color="inherit" onClick={cancelAccountAction}>
              لغو
            </Button>
          </Box>
        </Paper>
      )}

      {/* Input Area */}
      <Paper sx={{ p: 2, mt: 1 }}>
        <Box display="flex" gap={1} alignItems="flex-end">
          <TextField
            fullWidth
            multiline
            maxRows={3}
            placeholder="پیام خود را بنویسید..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={loading}
          />
          <IconButton
            color="primary"
            onClick={handleSendMessage}
            disabled={!inputText.trim() || loading}
            sx={{ p: 1 }}
          >
            <SendIcon />
          </IconButton>
        </Box>
      </Paper>
    </Box>
  );
}
