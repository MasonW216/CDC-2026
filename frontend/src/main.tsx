/**
 * React entry point.
 *
 * Mounts <App /> into #root and installs the router. Nothing else belongs here:
 * no data fetching, no layout, no providers that could be tested in isolation.
 *
 */
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';

import App from './App';
import './styles.css';

const root = document.getElementById('root');
if (!root) throw new Error('index.html is missing the #root element');

createRoot(root).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
);
