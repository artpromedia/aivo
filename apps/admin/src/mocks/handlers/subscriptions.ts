import { http, HttpResponse } from 'msw';

// Subscription type definition
interface MockSubscription {
  id: string;
  tenant_id: string;
  plan_id: string;
  plan_name: string;
  status: string;
  current_period_start: string;
  current_period_end: string;
  cancel_at_period_end: boolean;
  canceled_at?: string;
  quantity: number;
  unit_amount: number;
  currency: string;
  billing_cycle: 'monthly' | 'yearly';
  created_at: string;
  updated_at: string;
  metadata: Record<string, string>;
}

// Mock subscription data
const mockSubscriptions: MockSubscription[] = [
  {
    id: 'sub_1',
    tenant_id: 'tenant_123',
    plan_id: 'plan_pro',
    plan_name: 'Professional Plan',
    status: 'active',
    current_period_start: '2024-01-01T00:00:00Z',
    current_period_end: '2024-02-01T00:00:00Z',
    cancel_at_period_end: false,
    quantity: 50,
    unit_amount: 2999, // $29.99 in cents
    currency: 'usd',
    billing_cycle: 'monthly' as const,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    metadata: { department: 'education' },
  },
  {
    id: 'sub_2',
    tenant_id: 'tenant_456',
    plan_id: 'plan_enterprise',
    plan_name: 'Enterprise Plan',
    status: 'active',
    current_period_start: '2024-01-15T00:00:00Z',
    current_period_end: '2025-01-15T00:00:00Z',
    cancel_at_period_end: false,
    quantity: 200,
    unit_amount: 9999, // $99.99 in cents
    currency: 'usd',
    billing_cycle: 'yearly',
    created_at: '2024-01-15T00:00:00Z',
    updated_at: '2024-01-15T00:00:00Z',
    metadata: { contract: 'enterprise-2024' },
  },
  {
    id: 'sub_3',
    tenant_id: 'tenant_789',
    plan_id: 'plan_basic',
    plan_name: 'Basic Plan',
    status: 'past_due',
    current_period_start: '2024-01-10T00:00:00Z',
    current_period_end: '2024-02-10T00:00:00Z',
    cancel_at_period_end: false,
    quantity: 10,
    unit_amount: 999, // $9.99 in cents
    currency: 'usd',
    billing_cycle: 'monthly',
    created_at: '2024-01-10T00:00:00Z',
    updated_at: '2024-01-10T00:00:00Z',
    metadata: { trial: 'converted' },
  },
];

const mockPlans = [
  {
    id: 'plan_basic',
    name: 'Basic Plan',
    description: 'Perfect for small teams getting started',
    amount: 999, // $9.99 in cents
    currency: 'usd',
    interval: 'month',
    interval_count: 1,
    usage_type: 'licensed',
    features: ['Up to 10 users', '1GB storage', 'Email support'],
    max_users: 10,
    max_devices: 25,
    storage_gb: 1,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'plan_pro',
    name: 'Professional Plan',
    description: 'For growing teams that need more features',
    amount: 2999, // $29.99 in cents
    currency: 'usd',
    interval: 'month',
    interval_count: 1,
    usage_type: 'licensed',
    features: [
      'Up to 50 users',
      '10GB storage',
      'Priority support',
      'Advanced analytics',
    ],
    max_users: 50,
    max_devices: 100,
    storage_gb: 10,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'plan_enterprise',
    name: 'Enterprise Plan',
    description: 'For large organizations with advanced needs',
    amount: 9999, // $99.99 in cents
    currency: 'usd',
    interval: 'month',
    interval_count: 1,
    usage_type: 'licensed',
    features: [
      'Unlimited users',
      'Unlimited storage',
      '24/7 support',
      'Custom integrations',
      'SSO',
    ],
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
];

export const subscriptionHandlers = [
  // Get subscriptions
  http.get('http://localhost:8000/admin/subscriptions', ({ request }) => {
    const url = new URL(request.url);
    const status = url.searchParams.get('status');
    const page = parseInt(url.searchParams.get('page') || '1');
    const limit = parseInt(url.searchParams.get('limit') || '10');

    let filteredSubscriptions = mockSubscriptions;
    if (status && status !== 'all') {
      filteredSubscriptions = mockSubscriptions.filter(
        sub => sub.status === status
      );
    }

    const start = (page - 1) * limit;
    const end = start + limit;
    const paginatedSubscriptions = filteredSubscriptions.slice(start, end);

    return HttpResponse.json({
      subscriptions: paginatedSubscriptions,
      total: filteredSubscriptions.length,
      page,
      totalPages: Math.ceil(filteredSubscriptions.length / limit),
    });
  }),

  // Get single subscription
  http.get(
    'http://localhost:8000/admin/subscriptions/:subscriptionId',
    ({ params }) => {
      const subscription = mockSubscriptions.find(
        s => s.id === params.subscriptionId
      );
      if (subscription) {
        return HttpResponse.json(subscription);
      }
      return HttpResponse.json(
        { error: 'Subscription not found' },
        { status: 404 }
      );
    }
  ),

  // Get subscription plans
  http.get('http://localhost:8000/admin/subscription-plans', () => {
    return HttpResponse.json({ plans: mockPlans });
  }),

  // Get subscription usage
  http.get(
    'http://localhost:8000/admin/subscriptions/:subscriptionId/usage',
    ({ params }) => {
      const subscription = mockSubscriptions.find(
        s => s.id === params.subscriptionId
      );
      if (subscription) {
        return HttpResponse.json({
          subscription_id: subscription.id,
          period_start: subscription.current_period_start,
          period_end: subscription.current_period_end,
          usage_records: [
            {
              metric: 'users',
              quantity: 35,
              unit: 'count',
              description: 'Active users',
            },
            {
              metric: 'devices',
              quantity: 78,
              unit: 'count',
              description: 'Enrolled devices',
            },
            {
              metric: 'storage',
              quantity: 5.2,
              unit: 'GB',
              description: 'Storage used',
            },
            {
              metric: 'api_calls',
              quantity: 12540,
              unit: 'count',
              description: 'API calls made',
            },
          ],
          total_cost: subscription.unit_amount * subscription.quantity,
          currency: subscription.currency,
        });
      }
      return HttpResponse.json(
        { error: 'Subscription not found' },
        { status: 404 }
      );
    }
  ),

  // Create subscription
  http.post('/api/subscriptions', async ({ request }) => {
    const body = (await request.json()) as {
      plan_id: string;
      quantity: number;
      metadata?: Record<string, string>;
    };
    const newSubscription = {
      id: `sub_${Date.now()}`,
      tenant_id: 'tenant_123',
      plan_id: body.plan_id,
      plan_name:
        mockPlans.find(p => p.id === body.plan_id)?.name || 'Unknown Plan',
      status: 'active' as const,
      current_period_start: new Date().toISOString(),
      current_period_end: new Date(
        Date.now() + 30 * 24 * 60 * 60 * 1000
      ).toISOString(),
      cancel_at_period_end: false,
      quantity: body.quantity,
      unit_amount: mockPlans.find(p => p.id === body.plan_id)?.amount || 0,
      currency: 'usd',
      billing_cycle: 'monthly' as const,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      metadata: { trial: 'new', ...body.metadata },
    };

    mockSubscriptions.push(newSubscription);
    return HttpResponse.json(newSubscription);
  }),

  // Update subscription
  http.put('/api/subscriptions/:id', async ({ params, request }) => {
    const { id } = params;
    const body = (await request.json()) as {
      quantity?: number;
      cancel_at_period_end?: boolean;
      metadata?: Record<string, string>;
    };
    const index = mockSubscriptions.findIndex(sub => sub.id === id);

    if (index === -1) {
      return new HttpResponse(null, { status: 404 });
    }

    const subscription = { ...mockSubscriptions[index] };
    if (body.quantity !== undefined) {
      subscription.quantity = body.quantity;
    }
    if (body.cancel_at_period_end !== undefined) {
      subscription.cancel_at_period_end = body.cancel_at_period_end;
    }
    if (body.metadata !== undefined) {
      subscription.metadata = { ...subscription.metadata, ...body.metadata };
    }
    subscription.updated_at = new Date().toISOString();

    mockSubscriptions[index] = subscription;
    return HttpResponse.json(subscription);
  }),

  // Cancel subscription
  http.post(
    '/api/subscriptions/:subscriptionId/cancel',
    async ({ params, request }) => {
      const body = (await request.json()) as { cancel_at_period_end?: boolean };
      const subscription = mockSubscriptions.find(
        s => s.id === params.subscriptionId
      );

      if (subscription) {
        subscription.cancel_at_period_end = body.cancel_at_period_end !== false;
        if (!subscription.cancel_at_period_end) {
          subscription.status = 'canceled';
          subscription.canceled_at = new Date().toISOString();
        }
        subscription.updated_at = new Date().toISOString();
        return HttpResponse.json(subscription);
      }
      return HttpResponse.json(
        { error: 'Subscription not found' },
        { status: 404 }
      );
    }
  ),

  // Reactivate subscription
  http.post(
    'http://localhost:8000/admin/subscriptions/:subscriptionId/reactivate',
    ({ params }) => {
      const subscription = mockSubscriptions.find(
        s => s.id === params.subscriptionId
      );

      if (subscription) {
        subscription.status = 'active';
        subscription.cancel_at_period_end = false;
        subscription.canceled_at = undefined;
        subscription.updated_at = new Date().toISOString();
        return HttpResponse.json(subscription);
      }
      return HttpResponse.json(
        { error: 'Subscription not found' },
        { status: 404 }
      );
    }
  ),
];
