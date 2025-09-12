import { http, HttpResponse } from 'msw';

// Mock namespace data
const mockNamespaces: Array<{
  id: string;
  name: string;
  description: string;
  parent_id?: string;
  path: string;
  level: number;
  tenant_id: string;
  device_count: number;
  total_device_count: number;
  policies: Array<{
    id: string;
    name: string;
    type: 'security' | 'access' | 'configuration';
    enabled: boolean;
  }>;
  metadata: Record<string, string>;
  created_at: string;
  updated_at: string;
}> = [
  {
    id: 'ns_root',
    name: 'Root',
    description: 'Root namespace for all devices',
    parent_id: undefined,
    path: '/',
    level: 0,
    tenant_id: 'tenant_123',
    device_count: 5,
    total_device_count: 87,
    policies: [
      {
        id: 'pol_1',
        name: 'Default Security Policy',
        type: 'security',
        enabled: true,
      },
      {
        id: 'pol_2',
        name: 'Global Access Policy',
        type: 'access',
        enabled: true,
      },
    ],
    metadata: { environment: 'production' },
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'ns_education',
    name: 'Education',
    description: 'Educational institution devices',
    parent_id: 'ns_root',
    path: '/education',
    level: 1,
    tenant_id: 'tenant_123',
    device_count: 25,
    total_device_count: 45,
    policies: [
      {
        id: 'pol_3',
        name: 'Student Device Policy',
        type: 'security',
        enabled: true,
      },
      {
        id: 'pol_4',
        name: 'Educational Content Filter',
        type: 'configuration',
        enabled: true,
      },
    ],
    metadata: { institution_type: 'university', region: 'north' },
    created_at: '2024-01-02T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z',
  },
  {
    id: 'ns_edu_classroom',
    name: 'Classrooms',
    description: 'Classroom devices and equipment',
    parent_id: 'ns_education',
    path: '/education/classrooms',
    level: 2,
    tenant_id: 'tenant_123',
    device_count: 15,
    total_device_count: 15,
    policies: [
      {
        id: 'pol_5',
        name: 'Classroom Display Policy',
        type: 'configuration',
        enabled: true,
      },
    ],
    metadata: { building: 'main', floor: '2' },
    created_at: '2024-01-03T00:00:00Z',
    updated_at: '2024-01-03T00:00:00Z',
  },
  {
    id: 'ns_edu_labs',
    name: 'Labs',
    description: 'Computer labs and research facilities',
    parent_id: 'ns_education',
    path: '/education/labs',
    level: 2,
    tenant_id: 'tenant_123',
    device_count: 20,
    total_device_count: 20,
    policies: [
      {
        id: 'pol_6',
        name: 'Lab Equipment Policy',
        type: 'security',
        enabled: true,
      },
      {
        id: 'pol_7',
        name: 'Research Access Control',
        type: 'access',
        enabled: false,
      },
    ],
    metadata: { lab_type: 'computer_science', capacity: '40' },
    created_at: '2024-01-04T00:00:00Z',
    updated_at: '2024-01-04T00:00:00Z',
  },
  {
    id: 'ns_healthcare',
    name: 'Healthcare',
    description: 'Medical devices and equipment',
    parent_id: 'ns_root',
    path: '/healthcare',
    level: 1,
    tenant_id: 'tenant_123',
    device_count: 12,
    total_device_count: 32,
    policies: [
      {
        id: 'pol_8',
        name: 'HIPAA Compliance Policy',
        type: 'security',
        enabled: true,
      },
      {
        id: 'pol_9',
        name: 'Medical Device Access',
        type: 'access',
        enabled: true,
      },
    ],
    metadata: { facility_type: 'hospital', compliance: 'hipaa' },
    created_at: '2024-01-05T00:00:00Z',
    updated_at: '2024-01-05T00:00:00Z',
  },
  {
    id: 'ns_health_icu',
    name: 'ICU',
    description: 'Intensive Care Unit devices',
    parent_id: 'ns_healthcare',
    path: '/healthcare/icu',
    level: 2,
    tenant_id: 'tenant_123',
    device_count: 8,
    total_device_count: 8,
    policies: [
      {
        id: 'pol_10',
        name: 'Critical Care Policy',
        type: 'security',
        enabled: true,
      },
    ],
    metadata: { ward: 'icu', beds: '12' },
    created_at: '2024-01-06T00:00:00Z',
    updated_at: '2024-01-06T00:00:00Z',
  },
  {
    id: 'ns_health_general',
    name: 'General Wards',
    description: 'General patient care devices',
    parent_id: 'ns_healthcare',
    path: '/healthcare/general',
    level: 2,
    tenant_id: 'tenant_123',
    device_count: 12,
    total_device_count: 12,
    policies: [
      {
        id: 'pol_11',
        name: 'General Care Policy',
        type: 'configuration',
        enabled: true,
      },
    ],
    metadata: { ward_type: 'general', capacity: '50' },
    created_at: '2024-01-07T00:00:00Z',
    updated_at: '2024-01-07T00:00:00Z',
  },
  {
    id: 'ns_retail',
    name: 'Retail',
    description: 'Point of sale and retail devices',
    parent_id: 'ns_root',
    path: '/retail',
    level: 1,
    tenant_id: 'tenant_123',
    device_count: 8,
    total_device_count: 10,
    policies: [
      {
        id: 'pol_12',
        name: 'PCI Compliance Policy',
        type: 'security',
        enabled: true,
      },
    ],
    metadata: { store_type: 'electronics', location: 'downtown' },
    created_at: '2024-01-08T00:00:00Z',
    updated_at: '2024-01-08T00:00:00Z',
  },
  {
    id: 'ns_retail_pos',
    name: 'Point of Sale',
    description: 'Cash registers and payment terminals',
    parent_id: 'ns_retail',
    path: '/retail/pos',
    level: 2,
    tenant_id: 'tenant_123',
    device_count: 6,
    total_device_count: 6,
    policies: [
      {
        id: 'pol_13',
        name: 'Payment Security Policy',
        type: 'security',
        enabled: true,
      },
    ],
    metadata: { terminal_type: 'contactless', count: '6' },
    created_at: '2024-01-09T00:00:00Z',
    updated_at: '2024-01-09T00:00:00Z',
  },
  {
    id: 'ns_manufacturing',
    name: 'Manufacturing',
    description: 'Industrial and manufacturing equipment',
    parent_id: 'ns_root',
    path: '/manufacturing',
    level: 1,
    tenant_id: 'tenant_123',
    device_count: 0,
    total_device_count: 0,
    policies: [
      {
        id: 'pol_14',
        name: 'Industrial Safety Policy',
        type: 'security',
        enabled: true,
      },
    ],
    metadata: { facility_type: 'assembly', shift_pattern: '24x7' },
    created_at: '2024-01-10T00:00:00Z',
    updated_at: '2024-01-10T00:00:00Z',
  },
];

// Mock policies
const mockPolicies = [
  {
    id: 'pol_template_1',
    name: 'Basic Security Template',
    type: 'security' as const,
    description: 'Standard security policy for general devices',
    configuration: {
      encryption_required: true,
      password_complexity: 'high',
      auto_lock_timeout: 300,
    },
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'pol_template_2',
    name: 'Guest Access Template',
    type: 'access' as const,
    description: 'Limited access policy for guest devices',
    configuration: {
      network_access: 'guest',
      time_restrictions: true,
      content_filtering: 'moderate',
    },
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'pol_template_3',
    name: 'Kiosk Configuration',
    type: 'configuration' as const,
    description: 'Standard configuration for kiosk devices',
    configuration: {
      single_app_mode: true,
      user_interaction_timeout: 30,
      auto_restart_schedule: 'daily',
    },
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
];

export const namespacesHandlers = [
  // Get namespace tree
  http.get('/api/namespaces/tree', ({ request }) => {
    const url = new URL(request.url);
    const tenant_id = url.searchParams.get('tenant_id') || 'tenant_123';

    const filteredNamespaces = mockNamespaces.filter(
      ns => ns.tenant_id === tenant_id
    );

    // Build tree structure
    type NamespaceTreeNode = (typeof mockNamespaces)[0] & {
      children: NamespaceTreeNode[];
    };

    const buildTree = (parentId?: string): NamespaceTreeNode[] => {
      return filteredNamespaces
        .filter(ns => ns.parent_id === parentId)
        .map(ns => ({
          ...ns,
          children: buildTree(ns.id),
        }));
    };

    const tree = buildTree();
    return HttpResponse.json({ tree });
  }),

  // Get namespaces (flat list)
  http.get('/api/namespaces', ({ request }) => {
    const url = new URL(request.url);
    const page = parseInt(url.searchParams.get('page') || '1');
    const limit = parseInt(url.searchParams.get('limit') || '10');
    const parent_id = url.searchParams.get('parent_id');
    const search = url.searchParams.get('search');

    let filteredNamespaces = [...mockNamespaces];

    if (parent_id) {
      filteredNamespaces = filteredNamespaces.filter(
        ns => ns.parent_id === parent_id
      );
    }

    if (search) {
      const searchLower = search.toLowerCase();
      filteredNamespaces = filteredNamespaces.filter(
        ns =>
          ns.name.toLowerCase().includes(searchLower) ||
          ns.description.toLowerCase().includes(searchLower)
      );
    }

    const startIndex = (page - 1) * limit;
    const endIndex = startIndex + limit;
    const paginatedNamespaces = filteredNamespaces.slice(startIndex, endIndex);

    return HttpResponse.json({
      namespaces: paginatedNamespaces,
      pagination: {
        page,
        limit,
        total: filteredNamespaces.length,
        pages: Math.ceil(filteredNamespaces.length / limit),
      },
    });
  }),

  // Get single namespace
  http.get('/api/namespaces/:id', ({ params }) => {
    const { id } = params;
    const namespace = mockNamespaces.find(ns => ns.id === id);

    if (!namespace) {
      return new HttpResponse(null, { status: 404 });
    }

    return HttpResponse.json(namespace);
  }),

  // Create namespace
  http.post('/api/namespaces', async ({ request }) => {
    const body = (await request.json()) as {
      name: string;
      description: string;
      parent_id?: string;
      tenant_id: string;
      metadata?: Record<string, string>;
    };

    const parentNamespace = body.parent_id
      ? mockNamespaces.find(ns => ns.id === body.parent_id)
      : null;

    const parentPath = parentNamespace ? parentNamespace.path : '';
    const level = parentNamespace ? parentNamespace.level + 1 : 0;
    const path =
      parentPath === '/'
        ? `/${body.name.toLowerCase()}`
        : `${parentPath}/${body.name.toLowerCase()}`;

    const newNamespace = {
      id: `ns_${Date.now()}`,
      name: body.name,
      description: body.description,
      parent_id: body.parent_id,
      path,
      level,
      tenant_id: body.tenant_id,
      device_count: 0,
      total_device_count: 0,
      policies: [],
      metadata: body.metadata || {},
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    mockNamespaces.push(newNamespace);
    return HttpResponse.json(newNamespace);
  }),

  // Update namespace
  http.put('/api/namespaces/:id', async ({ params, request }) => {
    const { id } = params;
    const body = (await request.json()) as {
      name?: string;
      description?: string;
      metadata?: Record<string, string>;
    };

    const index = mockNamespaces.findIndex(ns => ns.id === id);

    if (index === -1) {
      return new HttpResponse(null, { status: 404 });
    }

    const namespace = { ...mockNamespaces[index] };

    if (body.name !== undefined) {
      namespace.name = body.name;
      // Update path if name changed
      const pathParts = namespace.path.split('/');
      pathParts[pathParts.length - 1] = body.name.toLowerCase();
      namespace.path = pathParts.join('/');
    }

    if (body.description !== undefined) {
      namespace.description = body.description;
    }

    if (body.metadata !== undefined) {
      namespace.metadata = { ...namespace.metadata, ...body.metadata };
    }

    namespace.updated_at = new Date().toISOString();
    mockNamespaces[index] = namespace;

    return HttpResponse.json(namespace);
  }),

  // Delete namespace
  http.delete('/api/namespaces/:id', ({ params }) => {
    const { id } = params;
    const namespace = mockNamespaces.find(ns => ns.id === id);

    if (!namespace) {
      return new HttpResponse(null, { status: 404 });
    }

    // Check if namespace has children
    const hasChildren = mockNamespaces.some(ns => ns.parent_id === id);
    if (hasChildren) {
      return HttpResponse.json(
        { error: 'Cannot delete namespace with child namespaces' },
        { status: 400 }
      );
    }

    // Check if namespace has devices
    if (namespace.device_count > 0) {
      return HttpResponse.json(
        { error: 'Cannot delete namespace with devices' },
        { status: 400 }
      );
    }

    const index = mockNamespaces.findIndex(ns => ns.id === id);
    mockNamespaces.splice(index, 1);

    return new HttpResponse(null, { status: 204 });
  }),

  // Move namespace
  http.post('/api/namespaces/:id/move', async ({ params, request }) => {
    const { id } = params;
    const body = (await request.json()) as { new_parent_id?: string };

    const namespace = mockNamespaces.find(ns => ns.id === id);
    if (!namespace) {
      return new HttpResponse(null, { status: 404 });
    }

    // Validate new parent exists
    if (body.new_parent_id) {
      const newParent = mockNamespaces.find(ns => ns.id === body.new_parent_id);
      if (!newParent) {
        return HttpResponse.json(
          { error: 'New parent namespace not found' },
          { status: 400 }
        );
      }

      // Prevent moving to own child
      const isChildOfTarget = (targetId: string, checkId: string): boolean => {
        const children = mockNamespaces.filter(ns => ns.parent_id === checkId);
        return children.some(
          child => child.id === targetId || isChildOfTarget(targetId, child.id)
        );
      };

      if (
        body.new_parent_id &&
        typeof body.new_parent_id === 'string' &&
        isChildOfTarget(body.new_parent_id, id as string)
      ) {
        return HttpResponse.json(
          { error: 'Cannot move namespace to its own child' },
          { status: 400 }
        );
      }
    }

    // Update namespace
    const index = mockNamespaces.findIndex(ns => ns.id === id);
    const updatedNamespace = { ...mockNamespaces[index] };

    updatedNamespace.parent_id = body.new_parent_id;

    // Update level and path
    const newParent = body.new_parent_id
      ? mockNamespaces.find(ns => ns.id === body.new_parent_id)
      : null;

    updatedNamespace.level = newParent ? newParent.level + 1 : 0;
    const parentPath = newParent ? newParent.path : '';
    updatedNamespace.path =
      parentPath === '/'
        ? `/${updatedNamespace.name.toLowerCase()}`
        : `${parentPath}/${updatedNamespace.name.toLowerCase()}`;

    updatedNamespace.updated_at = new Date().toISOString();
    mockNamespaces[index] = updatedNamespace;

    return HttpResponse.json(updatedNamespace);
  }),

  // Get namespace policies
  http.get('/api/namespaces/:id/policies', ({ params }) => {
    const { id } = params;
    const namespace = mockNamespaces.find(ns => ns.id === id);

    if (!namespace) {
      return new HttpResponse(null, { status: 404 });
    }

    return HttpResponse.json({ policies: namespace.policies });
  }),

  // Add policy to namespace
  http.post('/api/namespaces/:id/policies', async ({ params, request }) => {
    const { id } = params;
    const body = (await request.json()) as {
      policy_template_id: string;
      name: string;
      enabled?: boolean;
    };

    const namespaceIndex = mockNamespaces.findIndex(ns => ns.id === id);
    if (namespaceIndex === -1) {
      return new HttpResponse(null, { status: 404 });
    }

    const policyTemplate = mockPolicies.find(
      p => p.id === body.policy_template_id
    );
    if (!policyTemplate) {
      return HttpResponse.json(
        { error: 'Policy template not found' },
        { status: 400 }
      );
    }

    const newPolicy = {
      id: `pol_${Date.now()}`,
      name: body.name,
      type: policyTemplate.type,
      enabled: body.enabled !== false,
    };

    const namespace = { ...mockNamespaces[namespaceIndex] };
    namespace.policies = [...namespace.policies, newPolicy];
    namespace.updated_at = new Date().toISOString();

    mockNamespaces[namespaceIndex] = namespace;
    return HttpResponse.json(newPolicy);
  }),

  // Update namespace policy
  http.put(
    '/api/namespaces/:id/policies/:policyId',
    async ({ params, request }) => {
      const { id, policyId } = params;
      const body = (await request.json()) as {
        name?: string;
        enabled?: boolean;
      };

      const namespaceIndex = mockNamespaces.findIndex(ns => ns.id === id);
      if (namespaceIndex === -1) {
        return new HttpResponse(null, { status: 404 });
      }

      const namespace = { ...mockNamespaces[namespaceIndex] };
      const policyIndex = namespace.policies.findIndex(p => p.id === policyId);

      if (policyIndex === -1) {
        return HttpResponse.json(
          { error: 'Policy not found' },
          { status: 404 }
        );
      }

      const policy = { ...namespace.policies[policyIndex] };

      if (body.name !== undefined) {
        policy.name = body.name;
      }

      if (body.enabled !== undefined) {
        policy.enabled = body.enabled;
      }

      namespace.policies[policyIndex] = policy;
      namespace.updated_at = new Date().toISOString();
      mockNamespaces[namespaceIndex] = namespace;

      return HttpResponse.json(policy);
    }
  ),

  // Remove policy from namespace
  http.delete('/api/namespaces/:id/policies/:policyId', ({ params }) => {
    const { id, policyId } = params;

    const namespaceIndex = mockNamespaces.findIndex(ns => ns.id === id);
    if (namespaceIndex === -1) {
      return new HttpResponse(null, { status: 404 });
    }

    const namespace = { ...mockNamespaces[namespaceIndex] };
    const policyIndex = namespace.policies.findIndex(p => p.id === policyId);

    if (policyIndex === -1) {
      return HttpResponse.json({ error: 'Policy not found' }, { status: 404 });
    }

    namespace.policies.splice(policyIndex, 1);
    namespace.updated_at = new Date().toISOString();
    mockNamespaces[namespaceIndex] = namespace;

    return new HttpResponse(null, { status: 204 });
  }),

  // Get policy templates
  http.get('/api/policies/templates', () => {
    return HttpResponse.json({ templates: mockPolicies });
  }),

  // Get namespace stats
  http.get('/api/namespaces/stats', () => {
    const stats = {
      total_namespaces: mockNamespaces.length,
      total_devices: mockNamespaces.reduce(
        (sum, ns) => sum + ns.total_device_count,
        0
      ),
      namespaces_by_level: mockNamespaces.reduce(
        (acc, ns) => {
          acc[ns.level] = (acc[ns.level] || 0) + 1;
          return acc;
        },
        {} as Record<number, number>
      ),
      policies_count: mockNamespaces.reduce(
        (sum, ns) => sum + ns.policies.length,
        0
      ),
      active_policies: mockNamespaces.reduce(
        (sum, ns) => sum + ns.policies.filter(p => p.enabled).length,
        0
      ),
    };

    return HttpResponse.json(stats);
  }),
];
