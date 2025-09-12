// src/components/MainApp.tsx
import React, { useState } from 'react';
import { Box, Container } from '@mui/material';
import Navigation from './Navigation';
import Dashboard from './Dashboard';
import AccountManager from './AccountManager';
import TransactionManager from './TransactionManager';
import ChatInterface from './ChatInterface';
import AIFinancialAdvisor from './AIFinancialAdvisor';

// Placeholder components for other features
import CheckManager from './CheckManager';
import SavingsPlans from './SavingsPlans';
import Reports from './Reports';

export default function MainApp() {
  const [currentPage, setCurrentPage] = useState('dashboard');

  const renderCurrentPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <Dashboard />;
      case 'accounts':
        return <AccountManager />;
      case 'transactions':
        return <TransactionManager />;
      case 'chat':
        return <ChatInterface />;
      case 'advisor':
        return <AIFinancialAdvisor />;
      case 'checks':
        return <CheckManager />;
      case 'savings':
        return <SavingsPlans />;
      case 'reports':
        return <Reports />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <Box>
      <Navigation currentPage={currentPage} onPageChange={setCurrentPage} />
      <Box component="main" sx={{ pb: { xs: 10, md: 2 }, pt: { xs: 2, md: 3 } }}>
        <Container maxWidth="lg">
          {renderCurrentPage()}
        </Container>
      </Box>
    </Box>
  );
}
