import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

import { Layout } from '@/components/layout/Layout';

// Lazy load components for code splitting
const Dashboard = lazy(() =>
  import('@/pages/Dashboard').then(module => ({ default: module.Dashboard }))
);
const UsersPage = lazy(() =>
  import('@/pages/UsersPage').then(module => ({ default: module.UsersPage }))
);
const BillingPage = lazy(() =>
  import('@/pages/BillingPage').then(module => ({
    default: module.BillingPage,
  }))
);
const DevicePolicy = lazy(() =>
  import('@/pages/DevicePolicy').then(module => ({
    default: module.DevicePolicy,
  }))
);
const Devices = lazy(() =>
  import('@/pages/Devices').then(module => ({ default: module.Devices }))
);
const FleetHealth = lazy(() =>
  import('@/pages/Devices/FleetHealth').then(module => ({
    default: module.FleetHealth,
  }))
);
const ExperimentsPage = lazy(() =>
  import('@/pages/Experiments').then(module => ({
    default: module.ExperimentsPage,
  }))
);
const Hub = lazy(() =>
  import('@/pages/Integrations').then(module => ({ default: module.Hub }))
);
const Secrets = lazy(() => import('@/pages/Integrations/Secrets'));
const InkOps = lazy(() =>
  import('@/pages/InkOps').then(module => ({ default: module.InkOps }))
);
const NamespacesPage = lazy(() =>
  import('@/pages/NamespacesPage').then(module => ({
    default: module.NamespacesPage,
  }))
);
const BannersPage = lazy(() => import('@/pages/Operations/Banners'));
const IncidentsPage = lazy(() => import('@/pages/Operations/Incidents'));
const NotificationSubscriptionsPage = lazy(
  () => import('@/pages/Operations/NotificationSubscriptions')
);
const OTA = lazy(() =>
  import('@/pages/OTA').then(module => ({ default: module.OTA }))
);
const DataGovernance = lazy(() => import('@/pages/Security/DataGovernance'));
const SubscriptionsPage = lazy(() =>
  import('@/pages/SubscriptionsPage').then(module => ({
    default: module.SubscriptionsPage,
  }))
);
const Moderation = lazy(() => import('@/pages/Trust/Moderation'));

// Loading component
const PageLoader = () => (
  <div className='flex items-center justify-center min-h-[200px]'>
    <div className='animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600'></div>
  </div>
);

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
            <Route
              index
              element={
                <Suspense fallback={<PageLoader />}>
                  <Dashboard />
                </Suspense>
              }
            />
            <Route
              path='users'
              element={
                <Suspense fallback={<PageLoader />}>
                  <UsersPage />
                </Suspense>
              }
            />
            <Route
              path='devices'
              element={
                <Suspense fallback={<PageLoader />}>
                  <Devices />
                </Suspense>
              }
            />
            <Route
              path='fleet-health'
              element={
                <Suspense fallback={<PageLoader />}>
                  <FleetHealth />
                </Suspense>
              }
            />
            <Route
              path='device-policies'
              element={
                <Suspense fallback={<PageLoader />}>
                  <DevicePolicy />
                </Suspense>
              }
            />
            <Route
              path='ota'
              element={
                <Suspense fallback={<PageLoader />}>
                  <OTA />
                </Suspense>
              }
            />
            <Route
              path='ink-ops'
              element={
                <Suspense fallback={<PageLoader />}>
                  <InkOps />
                </Suspense>
              }
            />
            <Route
              path='experiments'
              element={
                <Suspense fallback={<PageLoader />}>
                  <ExperimentsPage />
                </Suspense>
              }
            />
            <Route
              path='secrets'
              element={
                <Suspense fallback={<PageLoader />}>
                  <Secrets />
                </Suspense>
              }
            />
            <Route
              path='integrations'
              element={
                <Suspense fallback={<PageLoader />}>
                  <Hub />
                </Suspense>
              }
            />
            <Route
              path='subscriptions'
              element={
                <Suspense fallback={<PageLoader />}>
                  <SubscriptionsPage />
                </Suspense>
              }
            />
            <Route
              path='billing'
              element={
                <Suspense fallback={<PageLoader />}>
                  <BillingPage />
                </Suspense>
              }
            />
            <Route
              path='namespaces'
              element={
                <Suspense fallback={<PageLoader />}>
                  <NamespacesPage />
                </Suspense>
              }
            />
            <Route
              path='incidents'
              element={
                <Suspense fallback={<PageLoader />}>
                  <IncidentsPage />
                </Suspense>
              }
            />
            <Route
              path='banners'
              element={
                <Suspense fallback={<PageLoader />}>
                  <BannersPage />
                </Suspense>
              }
            />
            <Route
              path='notification-subscriptions'
              element={
                <Suspense fallback={<PageLoader />}>
                  <NotificationSubscriptionsPage />
                </Suspense>
              }
            />
            <Route
              path='data-governance'
              element={
                <Suspense fallback={<PageLoader />}>
                  <DataGovernance />
                </Suspense>
              }
            />
            <Route
              path='moderation'
              element={
                <Suspense fallback={<PageLoader />}>
                  <Moderation />
                </Suspense>
              }
            />
            <Route
              path='support'
              element={<div>Support Page (Coming Soon)</div>}
            />
          </Route>
        </Routes>
      </Router>
      {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
    </QueryClientProvider>
  );
}

export default App;
