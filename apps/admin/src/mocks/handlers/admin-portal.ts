import { http, HttpResponse } from 'msw';

/**
 * Admin Portal Service MSW Handlers
 * Based on OpenAPI specification and Pact contracts
 */

// Mock data fixtures matching the Pact contract expectations
const mockAdminPortalData = {
  summary: {
    tenant_id: 'tenant_123',
    tenant_name: 'Acme Corporation',
    status: 'active',
    subscription_tier: 'professional',
    total_users: 45,
    active_users_30d: 38,
    total_documents: 1250,
    pending_approvals: 3,
    monthly_spend: '89.50',
    usage_alerts: 1,
    last_activity: '2024-09-02T10:30:00Z',
    health_score: 92.5,
  },
  team: {
    tenant_id: 'tenant_123',
    total_members: 12,
    active_members: 11,
    pending_invites: 2,
    members: [
      {
        user_id: 'user_001',
        email: 'admin@acme.com',
        name: 'John Smith',
        role: 'admin',
        status: 'active',
        last_login: '2024-09-02T09:15:00Z',
        permissions: ['admin', 'billing', 'team_management'],
        invite_status: null,
      },
      {
        user_id: 'user_002',
        email: 'sarah@acme.com',
        name: 'Sarah Johnson',
        role: 'teacher',
        status: 'active',
        last_login: '2024-09-01T14:30:00Z',
        permissions: ['documents', 'approvals'],
        invite_status: null,
      },
      {
        user_id: 'user_003',
        email: 'mike@acme.com',
        name: 'Mike Wilson',
        role: 'teacher',
        status: 'pending',
        last_login: null,
        permissions: ['documents'],
        invite_status: 'pending',
      },
    ],
    role_distribution: {
      admin: 2,
      teacher: 8,
      parent: 2,
    },
    recent_activity: [
      {
        user_id: 'user_001',
        action: 'document_approved',
        timestamp: '2024-09-02T08:45:00Z',
        details: 'Approved IEP for Student A',
      },
      {
        user_id: 'user_002',
        action: 'login',
        timestamp: '2024-09-01T14:30:00Z',
        details: 'User logged in',
      },
    ],
  },
  usage: {
    tenant_id: 'tenant_123',
    billing_period_start: '2024-09-01T00:00:00Z',
    billing_period_end: '2024-09-30T23:59:59Z',
    metrics: [
      {
        metric_name: 'API Calls',
        current_value: 75000,
        limit_value: 100000,
        percentage_used: 75.0,
        unit: 'requests',
      },
      {
        metric_name: 'Storage',
        current_value: 250,
        limit_value: 500,
        percentage_used: 50.0,
        unit: 'GB',
      },
      {
        metric_name: 'Users',
        current_value: 45,
        limit_value: 100,
        percentage_used: 45.0,
        unit: 'count',
      },
    ],
    total_api_calls: 75000,
    total_storage_gb: 15.2,
    bandwidth_gb: 8.5,
    cost_breakdown: {
      api_calls: '45.00',
      storage: '15.25',
      bandwidth: '8.75',
      support: '20.50',
    },
    projected_monthly_cost: '89.50',
    usage_trends: {
      api_calls_trend: 'increasing',
      storage_trend: 'stable',
      cost_trend: 'increasing',
    },
  },
  subscription: {
    tenant_id: 'tenant_123',
    current_tier: 'professional',
    billing_cycle: 'monthly',
    next_billing_date: '2024-10-01T00:00:00Z',
    auto_renewal: true,
    features: [
      'Advanced Analytics',
      'Priority Support',
      'Custom Integrations',
      'Advanced Security',
    ],
    usage_limits: {
      api_calls: 100000,
      storage_gb: 500,
      users: 100,
    },
    current_usage: {
      api_calls: 75000,
      storage_gb: 15.2,
      users: 45,
    },
  },
  billing: {
    tenant_id: 'tenant_123',
    current_balance: '0.00',
    next_payment_amount: '89.50',
    next_payment_date: '2024-10-01T00:00:00Z',
    payment_method: {
      type: 'credit_card',
      last_four: '4321',
      expiry_month: 12,
      expiry_year: 2025,
    },
    invoices: [
      {
        invoice_id: 'inv_001',
        date: '2024-09-01T00:00:00Z',
        amount: '89.50',
        status: 'paid',
        description: 'Monthly subscription - Professional Plan',
      },
      {
        invoice_id: 'inv_002',
        date: '2024-08-01T00:00:00Z',
        amount: '89.50',
        status: 'paid',
        description: 'Monthly subscription - Professional Plan',
      },
    ],
  },
};

export const adminPortalHandlers = [
  // Dashboard Summary
  http.get('http://localhost:8000/admin/dashboard/summary', ({ request }) => {
    const url = new URL(request.url);
    const tenantId = url.searchParams.get('tenant_id');
    const authHeader = request.headers.get('authorization');

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return HttpResponse.json(
        {
          error: 'Unauthorized',
          message: 'Valid authentication required',
        },
        { status: 401 }
      );
    }

    if (!tenantId) {
      return HttpResponse.json(
        {
          error: 'Bad Request',
          message: 'tenant_id parameter is required',
        },
        { status: 400 }
      );
    }

    return HttpResponse.json(mockAdminPortalData.summary, {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }),

  // Team Information
  http.get('*/admin-portal/v1/team', ({ request }) => {
    const url = new URL(request.url);
    const tenantId = url.searchParams.get('tenant_id');
    const authHeader = request.headers.get('authorization');

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return HttpResponse.json(
        {
          error: 'Unauthorized',
          message: 'Valid authentication required',
        },
        { status: 401 }
      );
    }

    if (!tenantId) {
      return HttpResponse.json(
        {
          error: 'Bad Request',
          message: 'tenant_id parameter is required',
        },
        { status: 400 }
      );
    }

    return HttpResponse.json(mockAdminPortalData.team, {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }),

  // Usage Metrics
  http.get('*/admin-portal/v1/usage', ({ request }) => {
    const url = new URL(request.url);
    const tenantId = url.searchParams.get('tenant_id');
    const authHeader = request.headers.get('authorization');

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return HttpResponse.json(
        {
          error: 'Unauthorized',
          message: 'Valid authentication required',
        },
        { status: 401 }
      );
    }

    if (!tenantId) {
      return HttpResponse.json(
        {
          error: 'Bad Request',
          message: 'tenant_id parameter is required',
        },
        { status: 400 }
      );
    }

    return HttpResponse.json(mockAdminPortalData.usage, {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }),

  // Subscription Details
  http.get('*/admin-portal/v1/subscription', ({ request }) => {
    const url = new URL(request.url);
    const tenantId = url.searchParams.get('tenant_id');
    const authHeader = request.headers.get('authorization');

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return HttpResponse.json(
        {
          error: 'Unauthorized',
          message: 'Valid authentication required',
        },
        { status: 401 }
      );
    }

    if (!tenantId) {
      return HttpResponse.json(
        {
          error: 'Bad Request',
          message: 'tenant_id parameter is required',
        },
        { status: 400 }
      );
    }

    return HttpResponse.json(mockAdminPortalData.subscription, {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }),

  // Billing History
  http.get('*/admin-portal/v1/billing/history', ({ request }) => {
    const url = new URL(request.url);
    const tenantId = url.searchParams.get('tenant_id');
    const authHeader = request.headers.get('authorization');

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return HttpResponse.json(
        {
          error: 'Unauthorized',
          message: 'Valid authentication required',
        },
        { status: 401 }
      );
    }

    if (!tenantId) {
      return HttpResponse.json(
        {
          error: 'Bad Request',
          message: 'tenant_id parameter is required',
        },
        { status: 400 }
      );
    }

    return HttpResponse.json(mockAdminPortalData.billing, {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }),

  // Health Check
  http.get('*/admin-portal/v1/health', () => {
    return HttpResponse.json(
      {
        status: 'healthy',
        service: 'admin-portal-svc',
        version: '1.0.0',
        timestamp: new Date().toISOString(),
      },
      {
        status: 200,
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );
  }),
];
