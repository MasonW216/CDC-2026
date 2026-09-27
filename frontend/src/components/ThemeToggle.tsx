/**
 * Light/dark mode switch.
 *
 * Defaults to light regardless of OS preference (styles.css otherwise follows
 * prefers-color-scheme), and remembers the explicit choice in localStorage so
 * it survives a reload. Applies the theme by setting data-theme on <html>,
 * which styles.css's :root[data-theme='dark'] block already defines.
 */
import { useEffect, useState } from 'react';

const STORAGE_KEY = 'stormroute-theme';
type Theme = 'light' | 'dark';

function readStoredTheme(): Theme {
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    return stored === 'dark' ? 'dark' : 'light';
  } catch {
    return 'light';
  }
}

export default function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>(readStoredTheme);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try {
      window.localStorage.setItem(STORAGE_KEY, theme);
    } catch {
      // Private browsing or blocked storage: theme still applies for this
      // load, it just won't persist across a reload.
    }
  }, [theme]);

  const isDark = theme === 'dark';

  return (
    <button
      type="button"
      role="switch"
      aria-checked={isDark}
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      className="theme-toggle"
      onClick={() => setTheme(isDark ? 'light' : 'dark')}
    >
      <span className="theme-toggle__icon" aria-hidden="true">
        {'☀'}
      </span>
      <span className="theme-toggle__thumb" aria-hidden="true" />
      <span className="theme-toggle__icon" aria-hidden="true">
        {'☽'}
      </span>
    </button>
  );
}
