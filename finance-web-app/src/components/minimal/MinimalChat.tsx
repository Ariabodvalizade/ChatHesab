import React, { useEffect, useRef, useState } from 'react';
import { Box, Button, TextField, Typography } from '@mui/material';
import { useAuth } from '../../context/AuthContext';
import { API_CONFIG, getAuthHeaders } from '../../config/api';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
}

export default function MinimalChat() {
  const { token } = useAuth();
  const [messages, setMessages] = useState<Message[]>([
    { id: 'intro', text: 'سلام، پیام مالی‌ات را بنویس.', sender: 'bot' },
  ]);
  const [input, setInput] = useState('');
  const [pendingAction, setPendingAction] = useState<any>(null); // transaction/account action payload
  const endRef = useRef<HTMLDivElement>(null);

  const scrollToEnd = () => endRef.current?.scrollIntoView({ behavior: 'smooth' });
  useEffect(scrollToEnd, [messages, pendingAction]);

  const sendMessage = async () => {
    if (!input.trim() || !token) return;
    const m: Message = { id: Date.now().toString(), text: input.trim(), sender: 'user' };
    setMessages((prev) => [...prev, m]);
    setInput('');
    try {
      const resp = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.AI_PROCESS}`, {
        method: 'POST',
        headers: getAuthHeaders(token),
        body: JSON.stringify({ message: m.text }),
      });
      if (!resp.ok) throw new Error('fail');
      const result = await resp.json();
      setMessages((prev) => [
        ...prev,
        { id: Date.now().toString(), text: result.response_message || 'انجام شد.', sender: 'bot' },
      ]);
      if (result.success && (result.type === 'transaction' || result.type === 'account')) {
        setPendingAction(result);
      }
    } catch (e) {
      setMessages((prev) => [...prev, { id: Date.now().toString(), text: 'خطا در پردازش.', sender: 'bot' }]);
    }
  };

  const confirmAction = async () => {
    if (!token || !pendingAction) return;
    try {
      if (pendingAction.type === 'transaction') {
        const payload: any = {
          account_id: pendingAction.account_id,
          transaction_type: pendingAction.transaction_type,
          amount: pendingAction.amount,
          category: pendingAction.category,
          description: pendingAction.description,
        };
        const resp = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.TRANSACTIONS}`, {
          method: 'POST', headers: getAuthHeaders(token), body: JSON.stringify(payload),
        });
        if (!resp.ok) throw new Error('tx');
        setMessages((p) => [...p, { id: Date.now().toString(), text: '✅ تراکنش ثبت شد.', sender: 'bot' }]);
      } else if (pendingAction.type === 'account') {
        if (pendingAction.action === 'create') {
          const body = {
            bank_name: pendingAction.bank_name || 'بانک',
            account_name: pendingAction.account_name || 'حساب',
            initial_balance: pendingAction.initial_balance || 0,
          };
          const resp = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.ACCOUNTS}`, {
            method: 'POST', headers: getAuthHeaders(token), body: JSON.stringify(body),
          });
          if (!resp.ok) throw new Error('acc');
          setMessages((p) => [...p, { id: Date.now().toString(), text: '✅ حساب ایجاد شد.', sender: 'bot' }]);
        } else if (pendingAction.action === 'update') {
          const payload: any = {};
          if (pendingAction.bank_name) payload.bank_name = pendingAction.bank_name;
          if (pendingAction.account_name) payload.account_name = pendingAction.account_name;
          if (typeof pendingAction.initial_balance === 'number') payload.initial_balance = pendingAction.initial_balance;
          const resp = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.ACCOUNTS}/${pendingAction.account_id}`, {
            method: 'PUT', headers: getAuthHeaders(token), body: JSON.stringify(payload),
          });
          if (!resp.ok) throw new Error('accu');
          setMessages((p) => [...p, { id: Date.now().toString(), text: '✏️ حساب ویرایش شد.', sender: 'bot' }]);
        } else if (pendingAction.action === 'delete') {
          const resp = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.ACCOUNTS}/${pendingAction.account_id}`, {
            method: 'DELETE', headers: getAuthHeaders(token),
          });
          if (!resp.ok) throw new Error('accd');
          setMessages((p) => [...p, { id: Date.now().toString(), text: '🗑️ حساب حذف شد.', sender: 'bot' }]);
        }
      }
    } catch (e) {
      setMessages((p) => [...p, { id: Date.now().toString(), text: '❌ خطا در انجام عملیات.', sender: 'bot' }]);
    } finally {
      setPendingAction(null);
    }
  };

  return (
    <Box sx={{ maxWidth: 900, mx: 'auto', p: 2 }}>
      <Box sx={{ border: '1px solid #e5e7eb', borderRadius: 8, p: 2, minHeight: '60vh' }}>
        {messages.map((m) => (
          <Box key={m.id} sx={{ display: 'flex', justifyContent: m.sender === 'user' ? 'flex-end' : 'flex-start', mb: 1 }}>
            <Box sx={{
              bgcolor: m.sender === 'user' ? '#0ea5e9' : '#f3f4f6',
              color: m.sender === 'user' ? '#fff' : '#0f172a',
              px: 1.5, py: 1, borderRadius: 6, maxWidth: '80%'
            }}>
              <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>{m.text}</Typography>
            </Box>
          </Box>
        ))}

        {pendingAction && (
          <Box sx={{ mt: 1, p: 1, border: '1px dashed #e5e7eb', borderRadius: 6 }}>
            <Typography variant="body2" sx={{ mb: 1 }}>
              {pendingAction.type === 'transaction'
                ? `تأیید تراکنش: ${pendingAction.category} - ${pendingAction.amount} تومان`
                : pendingAction.action === 'create'
                  ? `تأیید ایجاد حساب: ${pendingAction.bank_name || ''} ${pendingAction.account_name || ''}`
                  : pendingAction.action === 'update'
                    ? `تأیید ویرایش حساب`
                    : `تأیید حذف حساب`}
            </Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button size="small" variant="contained" onClick={confirmAction}>تأیید</Button>
              <Button size="small" variant="outlined" onClick={() => setPendingAction(null)}>انصراف</Button>
            </Box>
          </Box>
        )}

        <div ref={endRef} />
      </Box>

      <Box component="form" onSubmit={(e) => { e.preventDefault(); sendMessage(); }} sx={{ display: 'flex', gap: 1, mt: 2 }}>
        <TextField
          fullWidth size="small" placeholder="پیامت را بنویس..."
          value={input} onChange={(e) => setInput(e.target.value)}
        />
        <Button type="submit" variant="contained">ارسال</Button>
      </Box>
    </Box>
  );
}

