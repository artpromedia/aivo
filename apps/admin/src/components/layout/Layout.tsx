import { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';

import BannerDisplay from '../common/BannerDisplay';

import { Sidebar } from './Sidebar';

export function Layout() {
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    // Check for saved theme preference or default to light mode
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia(
      '(prefers-color-scheme: dark)'
    ).matches;

    if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
      setIsDark(true);
      document.documentElement.classList.add('dark');
    }
  }, []);

  const toggleTheme = () => {
    const newTheme = !isDark;
    setIsDark(newTheme);

    if (newTheme) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  };

  return (
    <div className='min-h-screen bg-background'>
      <div className='flex'>
        <Sidebar onThemeToggle={toggleTheme} isDark={isDark} />

        {/* Main content */}
        <div className='flex-1 lg:ml-0'>
          <main className='p-6 lg:p-8'>
            <BannerDisplay audience='admins' />
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  );
}
