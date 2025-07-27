import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import { ThemeProvider } from "./components/ui/theme-provider";

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);
root.render(
  <React.StrictMode>
    <ThemeProvider defaultTheme="dark" storageKey="app-theme">
      <App />
    </ThemeProvider>
  </React.StrictMode>
); 