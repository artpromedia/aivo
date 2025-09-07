import { resolve } from 'path';

import {
  PactV3,
  MatchersV3,
  SpecificationVersion,
} from '@pact-foundation/pact';

const { like, eachLike, regex } = MatchersV3;

const provider = new PactV3({
  consumer: 'admin-app',
  provider: 'admin-portal-svc',
  spec: SpecificationVersion.SPECIFICATION_VERSION_V3,
  dir: resolve(process.cwd(), 'contracts'),
});

describe('Admin App Consumer Tests', () => {
  describe('Dashboard Summary', () => {
    it('should get dashboard summary data', async () => {
      await provider
        .given('tenant exists with id tenant_123')
        .uponReceiving('a request for dashboard summary')
        .withRequest({
          method: 'GET',
          path: '/admin-portal/v1/dashboard/summary',
          headers: {
            Authorization: regex('^Bearer .+', 'Bearer valid-jwt-token'),
            'Content-Type': 'application/json',
          },
          query: {
            tenant_id: 'tenant_123',
          },
        })
        .willRespondWith({
          status: 200,
          headers: {
            'Content-Type': 'application/json',
          },
          body: like({
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
          }),
        });

      await provider.executeTest(async mockService => {
        const response = await fetch(
          `${mockService.url}/admin-portal/v1/dashboard/summary?tenant_id=tenant_123`,
          {
            headers: {
              Authorization: 'Bearer valid-jwt-token',
              'Content-Type': 'application/json',
            },
          }
        );

        expect(response.status).toBe(200);
        const data = await response.json();
        expect(data.tenant_id).toBe('tenant_123');
        expect(data.tenant_name).toBe('Acme Corporation');
        expect(data.status).toBe('active');
        expect(typeof data.total_users).toBe('number');
        expect(typeof data.health_score).toBe('number');
      });
    });

    it('should get team information', async () => {
      await provider
        .given('tenant exists with team members')
        .uponReceiving('a request for team information')
        .withRequest({
          method: 'GET',
          path: '/admin-portal/v1/team',
          headers: {
            Authorization: regex('^Bearer .+', 'Bearer valid-jwt-token'),
            'Content-Type': 'application/json',
          },
          query: {
            tenant_id: 'tenant_123',
          },
        })
        .willRespondWith({
          status: 200,
          headers: {
            'Content-Type': 'application/json',
          },
          body: like({
            tenant_id: 'tenant_123',
            total_members: 12,
            active_members: 11,
            pending_invites: 2,
            members: eachLike({
              user_id: 'user_001',
              email: 'admin@acme.com',
              name: 'John Smith',
              role: 'admin',
              status: 'active',
              last_login: '2024-09-02T09:15:00Z',
              permissions: ['admin', 'billing', 'team_management'],
              invite_status: null,
            }),
            role_distribution: like({
              admin: 2,
              teacher: 8,
              parent: 2,
            }),
            recent_activity: eachLike({
              user_id: 'user_001',
              action: 'document_approved',
              timestamp: '2024-09-02T08:45:00Z',
              details: 'Approved IEP for Student A',
            }),
          }),
        });

      await provider.executeTest(async mockService => {
        const response = await fetch(
          `${mockService.url}/admin-portal/v1/team?tenant_id=tenant_123`,
          {
            headers: {
              Authorization: 'Bearer valid-jwt-token',
              'Content-Type': 'application/json',
            },
          }
        );

        expect(response.status).toBe(200);
        const data = await response.json();
        expect(data.tenant_id).toBe('tenant_123');
        expect(Array.isArray(data.members)).toBe(true);
        expect(typeof data.total_members).toBe('number');
        expect(typeof data.role_distribution).toBe('object');
      });
    });

    it('should get usage metrics', async () => {
      await provider
        .given('tenant has usage data')
        .uponReceiving('a request for usage metrics')
        .withRequest({
          method: 'GET',
          path: '/admin-portal/v1/usage',
          headers: {
            Authorization: regex('^Bearer .+', 'Bearer valid-jwt-token'),
            'Content-Type': 'application/json',
          },
          query: {
            tenant_id: 'tenant_123',
          },
        })
        .willRespondWith({
          status: 200,
          headers: {
            'Content-Type': 'application/json',
          },
          body: like({
            tenant_id: 'tenant_123',
            billing_period_start: '2024-09-01T00:00:00Z',
            billing_period_end: '2024-09-30T23:59:59Z',
            metrics: eachLike({
              metric_name: 'API Calls',
              current_value: 75000,
              limit_value: 100000,
              percentage_used: 75.0,
              unit: 'requests',
            }),
            total_api_calls: 75000,
            total_storage_gb: 15.2,
            bandwidth_gb: 8.5,
            cost_breakdown: like({
              api_calls: '45.00',
              storage: '15.25',
              bandwidth: '8.75',
              support: '20.50',
            }),
            projected_monthly_cost: '89.50',
            usage_trends: like({
              api_calls_trend: 'increasing',
              storage_trend: 'stable',
              cost_trend: 'increasing',
            }),
          }),
        });

      await provider.executeTest(async mockService => {
        const response = await fetch(
          `${mockService.url}/admin-portal/v1/usage?tenant_id=tenant_123`,
          {
            headers: {
              Authorization: 'Bearer valid-jwt-token',
              'Content-Type': 'application/json',
            },
          }
        );

        expect(response.status).toBe(200);
        const data = await response.json();
        expect(data.tenant_id).toBe('tenant_123');
        expect(Array.isArray(data.metrics)).toBe(true);
        expect(typeof data.total_api_calls).toBe('number');
        expect(typeof data.cost_breakdown).toBe('object');
      });
    });
  });

  describe('Authentication', () => {
    it('should handle unauthorized requests', async () => {
      await provider
        .given('user is not authenticated')
        .uponReceiving('a request without valid authorization')
        .withRequest({
          method: 'GET',
          path: '/admin-portal/v1/dashboard/summary',
          headers: {
            'Content-Type': 'application/json',
          },
          query: {
            tenant_id: 'tenant_123',
          },
        })
        .willRespondWith({
          status: 401,
          headers: {
            'Content-Type': 'application/json',
          },
          body: like({
            error: 'Unauthorized',
            message: 'Valid authentication required',
          }),
        });

      await provider.executeTest(async mockService => {
        const response = await fetch(
          `${mockService.url}/admin-portal/v1/dashboard/summary?tenant_id=tenant_123`,
          {
            headers: {
              'Content-Type': 'application/json',
            },
          }
        );

        expect(response.status).toBe(401);
        const data = await response.json();
        expect(data.error).toBe('Unauthorized');
      });
    });
  });
});
