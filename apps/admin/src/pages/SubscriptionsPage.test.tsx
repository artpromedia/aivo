import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect } from 'vitest';

import { SubscriptionsPage } from '@/pages/SubscriptionsPage';

// Test utilities
function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
      mutations: {
        retry: false,
      },
    },
  });
}

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = createTestQueryClient();

  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{ui}</BrowserRouter>
    </QueryClientProvider>
  );
}

describe('SubscriptionsPage', () => {
  it('renders the subscriptions page title', async () => {
    renderWithProviders(<SubscriptionsPage />);

    expect(screen.getByText('Subscription Management')).toBeInTheDocument();
    expect(
      screen.getByText(
        'Manage customer subscriptions, plans, and billing cycles'
      )
    ).toBeInTheDocument();
  });

  it('shows loading state initially', async () => {
    renderWithProviders(<SubscriptionsPage />);

    expect(screen.getByText('Loading subscriptions...')).toBeInTheDocument();
  });

  it('renders create subscription button', async () => {
    renderWithProviders(<SubscriptionsPage />);

    expect(
      screen.getByRole('button', { name: /create subscription/i })
    ).toBeInTheDocument();
  });
});
