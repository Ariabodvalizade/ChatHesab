// src/components/Navigation.tsx
import React, { useState } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  useMediaQuery,
  useTheme,
  BottomNavigation,
  BottomNavigationAction,
  Paper,
} from '@mui/material';
import {
  Menu,
  Dashboard,
  AccountBalance,
  SwapHoriz,
  Receipt,
  Savings,
  Analytics,
  ExitToApp,
  Chat,
} from '@mui/icons-material';
import { useAuth } from '../context/AuthContext';

interface NavigationProps {
  currentPage: string;
  onPageChange: (page: string) => void;
}

export default function Navigation({ currentPage, onPageChange }: NavigationProps) {
  const { user, logout } = useAuth();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const menuItems = [
    { id: 'dashboard', label: 'داشبورد', icon: <Dashboard /> },
    { id: 'accounts', label: 'حساب‌های بانکی', icon: <AccountBalance /> },
    { id: 'transactions', label: 'تراکنش‌ها', icon: <SwapHoriz /> },
    { id: 'chat', label: '💬 چت هوشمند', icon: <Chat /> },
    { id: 'advisor', label: '🧠 مشاوره هوشمند مالی', icon: <Analytics /> },
    { id: 'checks', label: 'چک‌ها', icon: <Receipt /> },
    { id: 'savings', label: 'پس‌انداز', icon: <Savings /> },
    { id: 'reports', label: 'گزارش‌ها', icon: <Analytics /> },
  ];

  const handlePageChange = (pageId: string) => {
    onPageChange(pageId);
    if (isMobile) {
      setDrawerOpen(false);
    }
  };

  const renderMenuItems = () => (
    <List>
      {menuItems.map((item) => (
        <ListItem
          button
          key={item.id}
          selected={currentPage === item.id}
          onClick={() => handlePageChange(item.id)}
        >
          <ListItemIcon>{item.icon}</ListItemIcon>
          <ListItemText primary={item.label} />
        </ListItem>
      ))}
    </List>
  );

  return (
    <>
      <AppBar position="sticky">
        <Toolbar sx={{ minHeight: 64 }}>
          {isMobile && (
            <IconButton
              edge="start"
              color="inherit"
              onClick={() => setDrawerOpen(true)}
              sx={{ mr: 1 }}
            >
              <Menu />
            </IconButton>
          )}

          <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 600 }}>
            دستیار مالی
          </Typography>

          <Box display="flex" alignItems="center" gap={2}>
            <Typography variant="body2" color="text.secondary">
              {user?.first_name} {user?.last_name}
            </Typography>
            <Button variant="outlined" onClick={logout} startIcon={<ExitToApp />} sx={{ '& .MuiButton-startIcon': { ml: 1 } }}>
              خروج
            </Button>
          </Box>
        </Toolbar>
      </AppBar>

      {/* Desktop Navigation */}
      {!isMobile && (
        <Box display="flex" sx={{ borderBottom: 1, borderColor: 'divider', bgcolor: 'background.paper' }}>
          {menuItems.map((item) => (
            <Button
              key={item.id}
              startIcon={item.icon}
              onClick={() => handlePageChange(item.id)}
              sx={{
                minWidth: 120,
                py: 1.5,
                color: currentPage === item.id ? 'primary.main' : 'text.primary',
                backgroundColor: currentPage === item.id ? 'rgba(14,165,233,0.08)' : 'transparent',
                borderRadius: 0,
                '& .MuiButton-startIcon': { ml: 1 },
              }}
            >
              {item.label}
            </Button>
          ))}
        </Box>
      )}

      {/* Mobile Drawer */}
      <Drawer anchor="right" open={drawerOpen} onClose={() => setDrawerOpen(false)}>
        <Box sx={{ width: 280 }}>
          <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>منوی اصلی</Typography>
          </Box>
          <List>
            {menuItems.map((item) => (
              <ListItem
                button
                key={item.id}
                selected={currentPage === item.id}
                onClick={() => handlePageChange(item.id)}
              >
                <ListItemIcon sx={{ minWidth: 36, ml: 1 }}>{item.icon}</ListItemIcon>
                <ListItemText primary={item.label} />
              </ListItem>
            ))}
          </List>
        </Box>
      </Drawer>

      {/* Bottom Navigation for mobile */}
      {isMobile && (
        <Paper elevation={3} sx={{ position: 'fixed', right: 0, left: 0, bottom: 0, zIndex: 1200 }}>
          <BottomNavigation
            showLabels
            value={menuItems.findIndex(m => m.id === currentPage)}
            onChange={(_, newIndex) => handlePageChange(menuItems[newIndex].id)}
          >
            {menuItems.slice(0, 4).map((item) => (
              <BottomNavigationAction key={item.id} label={item.label} icon={item.icon} />
            ))}
          </BottomNavigation>
        </Paper>
      )}
    </>
  );
}
