import {
  LayoutDashboard,
  Users,
  CreditCard,
  FileText,
  Server,
  HelpCircle,
  Moon,
  Sun,
  Menu,
  X,
  Smartphone,
  Shield,
  Download,
  Pen,
  AlertTriangle,
  Megaphone,
  Bell,
  Eye,
  Activity,
  Beaker,
  Plug,
  Search,
  Command,
} from 'lucide-react';
import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';

import { Button } from '@/components/ui/button';

interface SidebarProps {
  onThemeToggle: () => void;
  isDark: boolean;
  onSearchOpen?: () => void;
}

const navigationItems = [
  {
    name: 'Dashboard',
    href: '/',
    icon: LayoutDashboard,
  },
  {
    name: 'Users & Licenses',
    href: '/users',
    icon: Users,
  },
  {
    name: 'Device Management',
    href: '/devices',
    icon: Smartphone,
  },
  {
    name: 'Fleet Health & Alerts',
    href: '/fleet-health',
    icon: Activity,
  },
  {
    name: 'Device Policies',
    href: '/device-policies',
    icon: Shield,
  },
  {
    name: 'OTA Updates',
    href: '/ota',
    icon: Download,
  },
  {
    name: 'Ink Operations',
    href: '/ink-ops',
    icon: Pen,
  },
  {
    name: 'Experiments',
    href: '/experiments',
    icon: Beaker,
  },
  {
    name: 'Integrations Hub',
    href: '/integrations',
    icon: Plug,
  },
  {
    name: 'Incident Center',
    href: '/incidents',
    icon: AlertTriangle,
  },
  {
    name: 'Announcements',
    href: '/banners',
    icon: Megaphone,
  },
  {
    name: 'Notifications',
    href: '/notification-subscriptions',
    icon: Bell,
  },
  {
    name: 'Subscriptions',
    href: '/subscriptions',
    icon: CreditCard,
  },
  {
    name: 'Billing & Invoices',
    href: '/billing',
    icon: FileText,
  },
  {
    name: 'Device/Namespaces',
    href: '/namespaces',
    icon: Server,
  },
  {
    name: 'Support & Help',
    href: '/support',
    icon: HelpCircle,
  },
  {
    name: 'Data Governance',
    href: '/data-governance',
    icon: Shield,
  },
  {
    name: 'Content Moderation',
    href: '/moderation',
    icon: Eye,
  },
];

export function Sidebar({ onThemeToggle, isDark, onSearchOpen }: SidebarProps) {
  const location = useLocation();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  return (
    <>
      {/* Mobile menu button */}
      <div className='lg:hidden fixed top-4 left-4 z-50'>
        <Button
          variant='outline'
          size='icon'
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
        >
          {isMobileMenuOpen ? (
            <X className='h-4 w-4' />
          ) : (
            <Menu className='h-4 w-4' />
          )}
        </Button>
      </div>

      {/* Sidebar */}
      <div
        className={`
        fixed inset-y-0 left-0 z-40 w-64 bg-background border-r transform transition-transform duration-300 ease-in-out
        ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full'}
        lg:translate-x-0 lg:static lg:inset-0
      `}
      >
        <div className='flex flex-col h-full'>
          {/* Logo */}
          <div className='flex items-center justify-between p-6 border-b'>
            <div className='flex items-center gap-3'>
              <div className='w-8 h-8 bg-gradient-to-br from-primary to-purple-600 rounded-lg'></div>
              <h1 className='text-xl font-bold'>AIVO Admin</h1>
            </div>
            <Button
              variant='ghost'
              size='icon'
              onClick={onThemeToggle}
              className='h-8 w-8'
            >
              {isDark ? (
                <Sun className='h-4 w-4' />
              ) : (
                <Moon className='h-4 w-4' />
              )}
            </Button>
          </div>

          {/* Global Search Button */}
          {onSearchOpen && (
            <div className='px-4 pb-4'>
              <Button
                variant='outline'
                onClick={onSearchOpen}
                className='w-full justify-start text-sm text-muted-foreground'
              >
                <Search className='h-4 w-4 mr-2' />
                Search...
                <div className='ml-auto flex items-center gap-1'>
                  <Command className='h-3 w-3' />
                  <span className='text-xs'>K</span>
                </div>
              </Button>
            </div>
          )}

          {/* Navigation */}
          <nav className='flex-1 p-4 space-y-2'>
            {navigationItems.map(item => {
              const Icon = item.icon;
              const isActive = location.pathname === item.href;

              return (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={() => setIsMobileMenuOpen(false)}
                  className={`sidebar-item ${isActive ? 'active' : ''}`}
                >
                  <Icon className='h-5 w-5' />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </nav>

          {/* User info */}
          <div className='p-4 border-t'>
            <div className='flex items-center gap-3'>
              <div className='w-8 h-8 bg-primary rounded-full flex items-center justify-center text-primary-foreground text-sm font-medium'>
                A
              </div>
              <div className='flex-1 min-w-0'>
                <p className='text-sm font-medium truncate'>Admin User</p>
                <p className='text-xs text-muted-foreground truncate'>
                  System Administrator
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Mobile overlay */}
      {isMobileMenuOpen && (
        <div
          className='fixed inset-0 bg-black bg-opacity-50 z-30 lg:hidden'
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}
    </>
  );
}
