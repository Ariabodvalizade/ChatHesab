import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import './dateFnsJalaliShim'
import App from './App.tsx'
import { RTL } from './rtl'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <RTL>
      <App />
    </RTL>
  </StrictMode>,
)
