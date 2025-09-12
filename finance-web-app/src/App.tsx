import React from 'react';
import { CssBaseline, Box } from '@mui/material';
import { ThemeProvider } from '@mui/material/styles';
import { AuthProvider, useAuth } from './context/AuthContext';
import MinimalLogin from './components/minimal/MinimalLogin';
import MainApp from './components/MainApp';
import theme from './theme';

function AppContent() {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">در حال بارگذاری...</Box>
    );
  }

  return (
    <Box sx={{ minHeight: '100vh' }}>
      {isAuthenticated ? <MainApp /> : <MinimalLogin />}
    </Box>
  );
}

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
