import { http, HttpResponse } from 'msw';

/**
 * Device Policy MSW Handlers
 */

const mockPolicies = [
  {
    id: 'policy_001',
    name: 'Student Kiosk Mode',
    description: 'Restrict devices to educational apps only',
    policy_type: 'kiosk',
    config: {
      allowed_apps: ['com.educational.math', 'com.educational.reading'],
      exit_code: '1234',
      lockdown_level: 'strict',
    },
    active: true,
    created_at: '2024-09-01T10:00:00Z',
    updated_at: '2024-09-01T10:00:00Z',
  },
  {
    id: 'policy_002',
    name: 'School Network Policy',
    description: 'Configure network access for school devices',
    policy_type: 'network',
    config: {
      wifi_enabled: true,
      mobile_data_enabled: false,
      allowed_networks: ['SchoolWiFi', 'SchoolWiFi_Guest'],
    },
    active: true,
    created_at: '2024-09-02T11:00:00Z',
    updated_at: '2024-09-02T11:00:00Z',
  },
  {
    id: 'policy_003',
    name: 'Safe DNS Policy',
    description: 'Block inappropriate content via DNS filtering',
    policy_type: 'dns',
    config: {
      primary_dns: '1.1.1.3',
      secondary_dns: '1.0.0.3',
      blocked_domains: ['facebook.com', 'youtube.com', 'tiktok.com'],
      allowed_domains: ['educational-site.com', 'khan-academy.org'],
    },
    active: true,
    created_at: '2024-09-03T12:00:00Z',
    updated_at: '2024-09-03T12:00:00Z',
  },
] as Array<{
  id: string;
  name: string;
  description: string;
  policy_type: string;
  config: Record<string, unknown>;
  active: boolean;
  created_at: string;
  updated_at: string;
}>;

export const policyHandlers = [
  // Get policies
  http.get(
    'http://localhost:8000/device-policy-svc/policies',
    ({ request }) => {
      const url = new URL(request.url);
      const page = parseInt(url.searchParams.get('page') || '1');
      const limit = parseInt(url.searchParams.get('limit') || '20');
      const policyType = url.searchParams.get('policy_type');

      let filteredPolicies = [...mockPolicies];

      if (policyType) {
        filteredPolicies = filteredPolicies.filter(
          p => p.policy_type === policyType
        );
      }

      const startIndex = (page - 1) * limit;
      const endIndex = startIndex + limit;
      const paginatedPolicies = filteredPolicies.slice(startIndex, endIndex);

      return HttpResponse.json({
        policies: paginatedPolicies,
        total: filteredPolicies.length,
        page,
        limit,
        pages: Math.ceil(filteredPolicies.length / limit),
      });
    }
  ),

  // Create policy
  http.post(
    'http://localhost:8000/device-policy-svc/policies',
    async ({ request }) => {
      const body = (await request.json()) as {
        name: string;
        description: string;
        policy_type: string;
        config: Record<string, unknown>;
      };

      const newPolicy = {
        id: `policy_${Date.now()}`,
        name: body.name,
        description: body.description,
        policy_type: body.policy_type,
        config: body.config,
        active: true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      mockPolicies.push(newPolicy);

      return HttpResponse.json(newPolicy, { status: 201 });
    }
  ),

  // Update policy
  http.put(
    'http://localhost:8000/device-policy-svc/policies/:policyId',
    async ({ params, request }) => {
      const body = (await request.json()) as {
        name?: string;
        description?: string;
        config?: Record<string, unknown>;
        active?: boolean;
      };

      const policy = mockPolicies.find(p => p.id === params.policyId);
      if (policy) {
        Object.assign(policy, {
          ...body,
          updated_at: new Date().toISOString(),
        });
        return HttpResponse.json(policy);
      }

      return new HttpResponse(null, { status: 404 });
    }
  ),

  // Delete policy
  http.delete(
    'http://localhost:8000/device-policy-svc/policies/:policyId',
    ({ params }) => {
      const index = mockPolicies.findIndex(p => p.id === params.policyId);
      if (index !== -1) {
        mockPolicies.splice(index, 1);
        return HttpResponse.json({ success: true });
      }

      return new HttpResponse(null, { status: 404 });
    }
  ),

  // Deploy policy to devices
  http.post(
    'http://localhost:8000/device-policy-svc/policies/:policyId/deploy',
    async ({ params, request }) => {
      const body = (await request.json()) as { device_ids: string[] };

      return HttpResponse.json({
        policy_id: params.policyId,
        deployment_id: `deployment_${Date.now()}`,
        device_count: body.device_ids.length,
        status: 'initiated',
      });
    }
  ),
];
