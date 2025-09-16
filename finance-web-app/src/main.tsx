import { StrictMode, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { CacheProvider } from '@emotion/react';
import createCache from '@emotion/cache';
import { prefixer } from 'stylis';
import rtlPlugin from 'stylis-plugin-rtl';
import { CssBaseline, ThemeProvider } from '@mui/material';
import { createTheme, responsiveFontSizes } from '@mui/material/styles';
import App from './App';

const rtlCache = createCache({
  key: 'mui-rtl',
  stylisPlugins: [prefixer, rtlPlugin],
  prepend: true,
});

const theme = responsiveFontSizes(
  createTheme({
    direction: 'rtl',
    typography: {
      fontFamily: `'Vazirmatn', 'IRANSans', 'Roboto', 'Helvetica', 'Arial', sans-serif`,
    },
    palette: {
      mode: 'light',
      primary: {
        main: '#1976d2',
      },
      secondary: {
        main: '#9c27b0',
      },
      background: {
        default: '#f7f9fc',
        paper: '#ffffff',
      },
    },
    shape: {
      borderRadius: 16,
    },
    components: {
      MuiButton: {
        styleOverrides: {
          root: {
            borderRadius: 999,
          },
        },
      },
    },
  }),
);

const Root = (): JSX.Element => {
  useEffect(() => {
    document.body.setAttribute('dir', 'rtl');
    document.body.style.margin = '0';
  }, []);

  return (
    <CacheProvider value={rtlCache}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <App />
      </ThemeProvider>
    </CacheProvider>
  );
};

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <StrictMode>
    <Root />
  </StrictMode>,
);
