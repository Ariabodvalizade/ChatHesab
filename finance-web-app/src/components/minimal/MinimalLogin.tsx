import React, { useState } from 'react';
import { Box, Button, TextField, Typography } from '@mui/material';
import { useAuth } from '../../context/AuthContext';

export default function MinimalLogin() {
  const { login, loading } = useAuth();
  const [telegramId, setTelegramId] = useState('');
  const [error, setError] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (!telegramId || isNaN(Number(telegramId))) {
      setError('شناسه تلگرام نامعتبر است');
      return;
    }
    const ok = await login(Number(telegramId), {
      first_name: 'کاربر',
      last_name: 'ساده',
      username: `user_${telegramId}`,
    });
    if (!ok) setError('ورود ناموفق بود');
  };

  return (
    <Box sx={{ maxWidth: 400, mx: 'auto', mt: 8, px: 2 }}>
      <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
        ورود
      </Typography>
      <form onSubmit={handleLogin}>
        <TextField
          fullWidth
          size="small"
          label="شناسه تلگرام"
          value={telegramId}
          onChange={(e) => setTelegramId(e.target.value)}
          type="number"
          autoFocus
        />
        {error && (
          <Typography color="error" variant="body2" sx={{ mt: 1 }}>
            {error}
          </Typography>
        )}
        <Button type="submit" variant="contained" fullWidth disabled={loading} sx={{ mt: 2 }}>
          ورود
        </Button>
      </form>
    </Box>
  );
}

