import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.tsx'

// Global styles — retro dark theme
const style = document.createElement('style');
style.textContent = `
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    background: #050510;
    color: #cccccc;
    font-family: monospace;
  }
  button {
    background: #1a1a2e;
    color: #00ff88;
    border: 1px solid #333;
    padding: 4px 12px;
    border-radius: 3px;
    font-family: monospace;
    font-size: 13px;
    cursor: pointer;
    transition: background 0.15s;
  }
  button:hover {
    background: #2a2a4e;
    border-color: #00ff88;
  }
  button:active {
    background: #0a3a0a;
  }
  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: #0a0a14; }
  ::-webkit-scrollbar-thumb { background: #333; border-radius: 3px; }
`;
document.head.appendChild(style);

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
