import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

import { Layout } from '@/components/layout/Layout';
import { Dashboard } from '@/pages/Dashboard';
import { DevicePolicy } from '@/pages/DevicePolicy';
import { Devices } from '@/pages/Devices';
import { InkOps } from '@/pages/InkOps';
import { OTA } from '@/pages/OTA';
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
            <Route
              path='subscriptions'
              element={<div>Subscriptions Page (Coming Soon)</div>}
            />
            <Route
              path='billing'
              element={<div>Billing Page (Coming Soon)</div>}
            />
            <Route
              path='namespaces'
              element={<div>Namespaces Page (Coming Soon)</div>}
            />
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
