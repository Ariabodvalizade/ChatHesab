import { CacheProvider } from '@emotion/react';
import createCache from '@emotion/cache';
import { prefixer } from 'stylis';
import rtlPlugin from 'stylis-plugin-rtl';
import React, { useEffect } from 'react';

const cacheRtl = createCache({
  key: 'mui-rtl',
  stylisPlugins: [rtlPlugin, prefixer],
});

export function RTL({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    if (typeof document !== 'undefined') {
      document.documentElement.setAttribute('dir', 'rtl');
      document.documentElement.setAttribute('lang', 'fa');
    }
  }, []);

  return <CacheProvider value={cacheRtl}>{children}</CacheProvider>;
}

