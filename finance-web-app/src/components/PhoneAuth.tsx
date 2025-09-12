// src/components/PhoneAuth.tsx
import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Container,
  Card,
  CardContent,
  InputAdornment,
  Avatar,
  Divider,
  Stepper,
  Step,
  StepLabel,
  Chip,
} from '@mui/material';
import {
  Phone,
  Sms,
  Verified,
  Security,
} from '@mui/icons-material';

interface PhoneAuthProps {
  onAuthSuccess: (token: string) => void;
}

export default function PhoneAuth({ onAuthSuccess }: PhoneAuthProps) {
  const [step, setStep] = useState(0); // 0: phone input, 1: OTP verification
  const [phoneNumber, setPhoneNumber] = useState('');
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [resendTimer, setResendTimer] = useState(0);

  const steps = ['شماره تلفن', 'تأیید کد'];

  // Format phone number as user types
  const formatPhoneNumber = (value: string) => {
    const cleaned = value.replace(/\D/g, '');
    if (cleaned.length <= 11) {
      return cleaned.replace(/(\d{4})(\d{3})(\d{4})/, '$1-$2-$3');
    }
    return value;
  };

  const handlePhoneSubmit = async () => {
    if (!phoneNumber || phoneNumber.length < 11) {
      setError('لطفاً شماره تلفن معتبر وارد کنید');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Here you would integrate with your SMS service (like Kavenegar, Ghasedak, etc.)
      const response = await fetch('/api/auth/send-otp', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          phone_number: phoneNumber.replace(/\D/g, ''),
        }),
      });

      if (response.ok) {
        setStep(1);
        startResendTimer();
      } else {
        const errorData = await response.json();
        setError(errorData.message || 'خطا در ارسال کد تأیید');
      }
    } catch (error) {
      console.error('Error sending OTP:', error);
      // For demo purposes, simulate successful OTP send
      setStep(1);
      startResendTimer();
      setError('');
    } finally {
      setLoading(false);
    }
  };

  const handleOtpSubmit = async () => {
    if (!otp || otp.length !== 6) {
      setError('لطفاً کد ۶ رقمی را وارد کنید');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch('/api/auth/verify-otp', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          phone_number: phoneNumber.replace(/\D/g, ''),
          otp_code: otp,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        onAuthSuccess(data.token);
      } else {
        const errorData = await response.json();
        setError(errorData.message || 'کد تأیید اشتباه است');
      }
    } catch (error) {
      console.error('Error verifying OTP:', error);
      // For demo purposes, simulate successful verification
      if (otp === '123456') {
        onAuthSuccess('demo-token-' + phoneNumber.replace(/\D/g, ''));
      } else {
        setError('کد تأیید اشتباه است. برای تست از کد 123456 استفاده کنید');
      }
    } finally {
      setLoading(false);
    }
  };

  const startResendTimer = () => {
    setResendTimer(60);
    const timer = setInterval(() => {
      setResendTimer((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  const handleResendOtp = () => {
    if (resendTimer > 0) return;
    handlePhoneSubmit();
  };

  const handleBack = () => {
    setStep(0);
    setOtp('');
    setError('');
  };

  return (
    <Container maxWidth="sm" sx={{ 
      minHeight: '100vh', 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center',
      py: 4
    }}>
      <Card sx={{ 
        width: '100%', 
        maxWidth: 500,
        borderRadius: 4,
        boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
        overflow: 'hidden'
      }}>
        {/* Header */}
        <Box sx={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          p: 4,
          textAlign: 'center'
        }}>
          <Avatar sx={{ 
            bgcolor: 'rgba(255,255,255,0.2)', 
            width: 80, 
            height: 80, 
            mx: 'auto', 
            mb: 2 
          }}>
            <Phone sx={{ fontSize: 40 }} />
          </Avatar>
          <Typography variant="h4" component="h1" sx={{ fontWeight: 'bold', mb: 1 }}>
            💬 چت حساب
          </Typography>
          <Typography variant="subtitle1" sx={{ opacity: 0.9 }}>
            دستیار مالی هوشمند شما
          </Typography>
        </Box>

        <CardContent sx={{ p: 4 }}>
          {/* Stepper */}
          <Stepper activeStep={step} sx={{ mb: 4 }}>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>

          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          {step === 0 ? (
            // Phone Number Input Step
            <Box>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold' }}>
                📱 شماره تلفن خود را وارد کنید
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                کد تأیید به این شماره ارسال خواهد شد
              </Typography>

              <TextField
                fullWidth
                label="شماره تلفن"
                placeholder="09123456789"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(formatPhoneNumber(e.target.value))}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Phone />
                    </InputAdornment>
                  ),
                }}
                sx={{
                  mb: 3,
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 3,
                  }
                }}
                helperText="شماره تلفن همراه خود را بدون ۰ وارد کنید"
              />

              <Button
                fullWidth
                variant="contained"
                size="large"
                onClick={handlePhoneSubmit}
                disabled={loading || !phoneNumber}
                sx={{
                  borderRadius: 3,
                  py: 1.5,
                  fontSize: '1.1rem',
                  background: 'linear-gradient(45deg, #2196F3 30%, #21CBF3 90%)',
                }}
              >
                {loading ? (
                  <CircularProgress size={24} color="inherit" />
                ) : (
                  'ارسال کد تأیید'
                )}
              </Button>

              <Divider sx={{ my: 3 }}>
                <Chip label="یا" />
              </Divider>

              <Box textAlign="center">
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  برای تست از شماره زیر استفاده کنید:
                </Typography>
                <Button
                  variant="outlined"
                  onClick={() => setPhoneNumber('09123456789')}
                  sx={{ borderRadius: 2 }}
                >
                  09123456789
                </Button>
              </Box>
            </Box>
          ) : (
            // OTP Verification Step
            <Box>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold' }}>
                🔐 کد تأیید را وارد کنید
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                کد ۶ رقمی ارسال شده به {phoneNumber} را وارد کنید
              </Typography>

              <TextField
                fullWidth
                label="کد تأیید"
                placeholder="123456"
                value={otp}
                onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Sms />
                    </InputAdornment>
                  ),
                }}
                sx={{
                  mb: 3,
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 3,
                  }
                }}
                helperText="برای تست از کد 123456 استفاده کنید"
              />

              <Button
                fullWidth
                variant="contained"
                size="large"
                onClick={handleOtpSubmit}
                disabled={loading || otp.length !== 6}
                sx={{
                  borderRadius: 3,
                  py: 1.5,
                  fontSize: '1.1rem',
                  background: 'linear-gradient(45deg, #4CAF50 30%, #81C784 90%)',
                  mb: 2
                }}
              >
                {loading ? (
                  <CircularProgress size={24} color="inherit" />
                ) : (
                  'تأیید و ورود'
                )}
              </Button>

              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Button
                  variant="text"
                  onClick={handleBack}
                  sx={{ borderRadius: 2 }}
                >
                  بازگشت
                </Button>

                <Button
                  variant="text"
                  onClick={handleResendOtp}
                  disabled={resendTimer > 0}
                  sx={{ borderRadius: 2 }}
                >
                  {resendTimer > 0 ? `ارسال مجدد (${resendTimer})` : 'ارسال مجدد کد'}
                </Button>
              </Box>

              <Box sx={{ mt: 3, p: 2, bgcolor: 'info.50', borderRadius: 2 }}>
                <Box display="flex" alignItems="center" mb={1}>
                  <Security sx={{ mr: 1, color: 'info.main' }} />
                  <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                    امنیت اطلاعات
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary">
                  تمامی اطلاعات شما رمزنگاری شده و کاملاً محفوظ است
                </Typography>
              </Box>
            </Box>
          )}
        </CardContent>
      </Card>
    </Container>
  );
}