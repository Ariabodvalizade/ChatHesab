import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  direction: 'rtl',
  typography: {
    fontFamily: 'Vazirmatn',
  },
  palette: {
    mode: 'light',
    primary: { main: '#0ea5e9' },
    background: { default: '#ffffff', paper: '#ffffff' },
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: { direction: 'rtl' },
      },
    },
    MuiButton: {
      defaultProps: { disableElevation: true },
      styleOverrides: { root: { textTransform: 'none' } },
    },
  },
});

export default theme;
