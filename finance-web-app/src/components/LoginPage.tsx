// src/components/LoginPage.tsx
import React, { useState } from 'react';
import {
  Container,
  Paper,
  TextField,
  Button,
  Typography,
  Box,
  Alert,
  CircularProgress,
  Stack,
} from '@mui/material';
import { useAuth } from '../context/AuthContext';

export default function LoginPage() {
  const [telegramId, setTelegramId] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [username, setUsername] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const { login, loading } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Form submitted, preventing default');
    setError('');
    setSuccess('');

    if (!telegramId || isNaN(Number(telegramId))) {
      setError('لطفاً شناسه تلگرام معتبر وارد کنید');
      return;
    }

    console.log('Attempting login with telegram_id:', telegramId);
    try {
      const success = await login(Number(telegramId), {
        first_name: firstName || 'کاربر',
        last_name: lastName || 'تست',
        username: username || `user_${telegramId}`,
      });

      console.log('Login result:', success);
      if (success) {
        setSuccess('ورود با موفقیت انجام شد... در حال انتقال');
      } else {
        setError('خطا در ورود. لطفاً دوباره تلاش کنید.');
      }
      // Note: Navigation will happen automatically via AuthContext state change
    } catch (error) {
      console.error('Login error:', error);
      setError('خطا در ورود. لطفاً دوباره تلاش کنید.');
    }
  };

  // Quick demo login options
  const handleDemoLogin = async (demoId: number, name: string) => {
    console.log('Demo login clicked for:', demoId, name);
    setError('');
    setSuccess('');
    try {
      const success = await login(demoId, {
        first_name: name,
        last_name: 'تست',
        username: `demo_${demoId}`,
      });

      console.log('Demo login result:', success);
      if (success) {
        setSuccess(`ورود ${name} با موفقیت انجام شد... در حال انتقال`);
      } else {
        setError('خطا در ورود دمو');
      }
      // Note: Navigation will happen automatically via AuthContext state change
    } catch (error) {
      console.error('Demo login error:', error);
      setError('خطا در ورود دمو');
    }
  };

  return (
    <Container maxWidth="sm">
      <Paper sx={{ p: { xs: 2, md: 3 } }}>
        <Box textAlign="center" mb={2}>
          <Typography variant="h6" component="h1" sx={{ fontWeight: 600 }}>
            ورود با تلگرام
          </Typography>
          <Typography variant="body2" color="text.secondary">
            اطلاعات خود را وارد کنید
          </Typography>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        {success && (
          <Alert severity="success" sx={{ mb: 2 }}>
            {success}
          </Alert>
        )}

        <form onSubmit={handleSubmit}>
          <Stack spacing={1.5}>
            <TextField
              fullWidth
              size="small"
              label="شناسه تلگرام"
              value={telegramId}
              onChange={(e) => setTelegramId(e.target.value)}
              required
              type="number"
              helperText="شناسه عددی حساب تلگرام شما"
            />
            <TextField
              fullWidth
              size="small"
              label="نام"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
            />
            <TextField
              fullWidth
              size="small"
              label="نام خانوادگی"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
            />
            <TextField
              fullWidth
              size="small"
              label="نام کاربری (اختیاری)"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />

            <Button type="submit" fullWidth variant="contained" disabled={loading} sx={{ mt: 1 }}>
              {loading ? <CircularProgress size={20} /> : 'ورود'}
            </Button>
          </Stack>
        </form>

        <Box mt={3}>
          <Typography variant="subtitle2" gutterBottom textAlign="center">
            ورود سریع (دمو)
          </Typography>
          <Stack spacing={1}>
            <Box display="flex" gap={1}>
              <Button variant="outlined" onClick={() => handleDemoLogin(12345, 'احمد')} disabled={loading} sx={{ flex: 1 }}>
                احمد (12345)
              </Button>
              <Button variant="outlined" onClick={() => handleDemoLogin(67890, 'سارا')} disabled={loading} sx={{ flex: 1 }}>
                سارا (67890)
              </Button>
            </Box>
            <Button variant="contained" color="secondary" onClick={() => handleDemoLogin(5153051620, 'آریا ادمین')} disabled={loading} fullWidth>
              🔑 ورود ادمین - آریا (5153051620)
            </Button>
          </Stack>
        </Box>
      </Paper>
    </Container>
  );
}
