import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

import { Layout } from '@/components/layout/Layout';
import { BillingPage } from '@/pages/BillingPage';
import { Dashboard } from '@/pages/Dashboard';
import { DevicePolicy } from '@/pages/DevicePolicy';
import { Devices } from '@/pages/Devices';
import { InkOps } from '@/pages/InkOps';
import { NamespacesPage } from '@/pages/NamespacesPage';
import BannersPage from '@/pages/Operations/Banners';
import IncidentsPage from '@/pages/Operations/Incidents';
import NotificationSubscriptionsPage from '@/pages/Operations/NotificationSubscriptions';
import { OTA } from '@/pages/OTA';
import DataGovernance from '@/pages/Security/DataGovernance';
import { SubscriptionsPage } from '@/pages/SubscriptionsPage';
import Moderation from '@/pages/Trust/Moderation';
import { UsersPage } from '@/pages/UsersPage';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Routes>
          <Route path='/' element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path='users' element={<UsersPage />} />
            <Route path='devices' element={<Devices />} />
            <Route path='device-policies' element={<DevicePolicy />} />
            <Route path='ota' element={<OTA />} />
            <Route path='ink-ops' element={<InkOps />} />
            <Route path='subscriptions' element={<SubscriptionsPage />} />
            <Route path='billing' element={<BillingPage />} />
            <Route path='namespaces' element={<NamespacesPage />} />
            <Route path='incidents' element={<IncidentsPage />} />
            <Route path='banners' element={<BannersPage />} />
            <Route
              path='notification-subscriptions'
              element={<NotificationSubscriptionsPage />}
            />
            <Route path='data-governance' element={<DataGovernance />} />
            <Route path='moderation' element={<Moderation />} />
            <Route
              path='support'
              element={<div>Support Page (Coming Soon)</div>}
            />
          </Route>
        </Routes>
      </Router>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}

export default App;
