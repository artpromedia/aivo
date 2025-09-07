import { http, HttpResponse } from 'msw';

/**
 * Tenant Service MSW Handlers
 * Based on OpenAPI specification for multi-tenant management
 */

const mockTenantData = {
  tenants: [
    {
      id: 'tenant_123',
      name: 'Acme Corporation',
      status: 'active',
      type: 'district',
      created_at: '2024-01-01T00:00:00Z',
      settings: {
        timezone: 'America/New_York',
        locale: 'en-US',
        features: ['analytics', 'integrations', 'advanced_reporting'],
      },
      subscription: {
        tier: 'professional',
        seats_total: 100,
        seats_used: 45,
        billing_cycle: 'monthly',
      },
    },
  ],
  schools: [
    {
      id: 'school_001',
      tenant_id: 'tenant_123',
      name: 'Acme Elementary School',
      type: 'elementary',
      status: 'active',
      address: {
        street: '123 Education Lane',
        city: 'Learning City',
        state: 'CA',
        zip: '90210',
      },
      contact: {
        phone: '555-0123',
        email: 'contact@acme-elementary.edu',
      },
      enrollment: {
        total_students: 450,
        grade_levels: ['K', '1', '2', '3', '4', '5'],
      },
    },
  ],
  users: [
    {
      id: 'user_001',
      tenant_id: 'tenant_123',
      email: 'admin@acme.com',
      name: 'John Smith',
      role: 'admin',
      status: 'active',
      schools: ['school_001'],
      permissions: ['admin', 'billing', 'team_management'],
      created_at: '2024-01-15T00:00:00Z',
      last_login: '2024-09-02T09:15:00Z',
    },
  ],
};

export const tenantHandlers = [
  // Get Tenant Details
  http.get('*/tenant/v1/tenants/:tenantId', ({ params, request }) => {
    const { tenantId } = params;
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

    const tenant = mockTenantData.tenants.find(t => t.id === tenantId);

    if (!tenant) {
      return HttpResponse.json(
        {
          error: 'Not Found',
          message: 'Tenant not found',
        },
        { status: 404 }
      );
    }

    return HttpResponse.json(tenant, {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }),

  // List Schools in Tenant
  http.get('*/tenant/v1/tenants/:tenantId/schools', ({ params, request }) => {
    const { tenantId } = params;
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

    const schools = mockTenantData.schools.filter(
      s => s.tenant_id === tenantId
    );

    return HttpResponse.json(
      {
        schools,
        total: schools.length,
        tenant_id: tenantId,
      },
      {
        status: 200,
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );
  }),

  // List Users in Tenant
  http.get('*/tenant/v1/tenants/:tenantId/users', ({ params, request }) => {
    const { tenantId } = params;
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

    const users = mockTenantData.users.filter(u => u.tenant_id === tenantId);

    return HttpResponse.json(
      {
        users,
        total: users.length,
        tenant_id: tenantId,
        statistics: {
          total_users: users.length,
          active_users: users.filter(u => u.status === 'active').length,
          roles: {
            admin: users.filter(u => u.role === 'admin').length,
            teacher: users.filter(u => u.role === 'teacher').length,
            parent: users.filter(u => u.role === 'parent').length,
          },
        },
      },
      {
        status: 200,
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );
  }),

  // Update Tenant Settings
  http.patch('*/tenant/v1/tenants/:tenantId', async ({ params, request }) => {
    const { tenantId } = params;
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

    const tenant = mockTenantData.tenants.find(t => t.id === tenantId);

    if (!tenant) {
      return HttpResponse.json(
        {
          error: 'Not Found',
          message: 'Tenant not found',
        },
        { status: 404 }
      );
    }

    // Mock update - in real implementation would update the tenant
    return HttpResponse.json(tenant, {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }),

  // Health Check
  http.get('*/tenant/v1/health', () => {
    return HttpResponse.json(
      {
        status: 'healthy',
        service: 'tenant-svc',
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
