import { AppBar, Box, Container, Toolbar, Typography } from '@mui/material';
import { PropsWithChildren } from 'react';

const Layout = ({ children }: PropsWithChildren): JSX.Element => {
  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        bgcolor: 'background.default',
      }}
    >
      <AppBar position="static" color="primary" elevation={1}>
        <Toolbar sx={{ justifyContent: 'space-between' }}>
          <Typography component="h1" variant="h6" sx={{ fontWeight: 600 }}>
            چت حساب
          </Typography>
          <Typography variant="body2" color="inherit">
            مدیریت مالی هوشمند
          </Typography>
        </Toolbar>
      </AppBar>

      <Container component="main" maxWidth="md" sx={{ flexGrow: 1, py: 4, width: '100%' }}>
        {children}
      </Container>

      <Box component="footer" sx={{ py: 2, textAlign: 'center', bgcolor: 'background.paper' }}>
        <Typography variant="caption" color="text.secondary">
          تمامی حقوق محفوظ است © {new Date().getFullYear()}
        </Typography>
      </Box>
    </Box>
  );
};

export default Layout;
