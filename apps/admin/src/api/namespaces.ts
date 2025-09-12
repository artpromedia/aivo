import { apiRequest } from './base';

export interface DeviceNamespace {
  id: string;
  name: string;
  description: string;
  tenant_id: string;
  parent_id?: string;
  path: string;
  level: number;
  device_count: number;
  policy_count: number;
  created_at: string;
  updated_at: string;
  metadata: Record<string, string>;
  is_active: boolean;
}

export interface NamespaceDevice {
  id: string;
  serial_number: string;
  device_type: string;
  enrollment_status: string;
  location?: string;
  last_seen?: string;
  namespace_id: string;
  namespace_path: string;
}

export interface NamespacePolicy {
  id: string;
  name: string;
  policy_type: string;
  is_active: boolean;
  applied_at: string;
  namespace_id: string;
  device_count: number;
}

export interface CreateNamespaceRequest {
  name: string;
  description: string;
  parent_id?: string;
  metadata?: Record<string, string>;
}

export interface UpdateNamespaceRequest {
  name?: string;
  description?: string;
  metadata?: Record<string, string>;
  is_active?: boolean;
}

export interface MoveDevicesRequest {
  device_ids: string[];
  target_namespace_id: string;
}

export interface NamespaceTree {
  id: string;
  name: string;
  path: string;
  device_count: number;
  children: NamespaceTree[];
}

export interface NamespaceStats {
  namespace_id: string;
  total_devices: number;
  active_devices: number;
  inactive_devices: number;
  policies_applied: number;
  storage_used_gb: number;
  last_activity: string;
  device_types: {
    type: string;
    count: number;
  }[];
}

export class NamespacesAPI {
  static async getNamespaces(params?: {
    page?: number;
    limit?: number;
    parent_id?: string;
    tenant_id?: string;
    include_children?: boolean;
  }) {
    const queryParams = new URLSearchParams();
    if (params?.page) queryParams.set('page', params.page.toString());
    if (params?.limit) queryParams.set('limit', params.limit.toString());
    if (params?.parent_id) queryParams.set('parent_id', params.parent_id);
    if (params?.tenant_id) queryParams.set('tenant_id', params.tenant_id);
    if (params?.include_children) queryParams.set('include_children', 'true');

    return apiRequest<{
      namespaces: DeviceNamespace[];
      total: number;
      page: number;
      totalPages: number;
    }>(`/admin/namespaces?${queryParams.toString()}`);
  }

  static async getNamespace(namespaceId: string) {
    return apiRequest<DeviceNamespace>(`/admin/namespaces/${namespaceId}`);
  }

  static async createNamespace(data: CreateNamespaceRequest) {
    return apiRequest<DeviceNamespace>('/admin/namespaces', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  static async updateNamespace(
    namespaceId: string,
    data: UpdateNamespaceRequest
  ) {
    return apiRequest<DeviceNamespace>(`/admin/namespaces/${namespaceId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  static async deleteNamespace(namespaceId: string, force = false) {
    return apiRequest<void>(`/admin/namespaces/${namespaceId}`, {
      method: 'DELETE',
      body: JSON.stringify({ force }),
    });
  }

  static async getNamespaceDevices(
    namespaceId: string,
    params?: {
      page?: number;
      limit?: number;
      status?: string;
      device_type?: string;
    }
  ) {
    const queryParams = new URLSearchParams();
    if (params?.page) queryParams.set('page', params.page.toString());
    if (params?.limit) queryParams.set('limit', params.limit.toString());
    if (params?.status) queryParams.set('status', params.status);
    if (params?.device_type) queryParams.set('device_type', params.device_type);

    return apiRequest<{
      devices: NamespaceDevice[];
      total: number;
      page: number;
      totalPages: number;
    }>(`/admin/namespaces/${namespaceId}/devices?${queryParams.toString()}`);
  }

  static async getNamespacePolicies(namespaceId: string) {
    return apiRequest<{
      policies: NamespacePolicy[];
    }>(`/admin/namespaces/${namespaceId}/policies`);
  }

  static async moveDevices(data: MoveDevicesRequest) {
    return apiRequest<{
      moved_count: number;
      failed_devices: string[];
    }>('/admin/namespaces/move-devices', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  static async getNamespaceTree(tenantId?: string) {
    const queryParams = new URLSearchParams();
    if (tenantId) queryParams.set('tenant_id', tenantId);

    return apiRequest<{
      tree: NamespaceTree[];
    }>(`/admin/namespaces/tree?${queryParams.toString()}`);
  }

  static async getNamespaceStats(namespaceId: string) {
    return apiRequest<NamespaceStats>(`/admin/namespaces/${namespaceId}/stats`);
  }

  static async assignPolicy(namespaceId: string, policyId: string) {
    return apiRequest<NamespacePolicy>(
      `/admin/namespaces/${namespaceId}/policies`,
      {
        method: 'POST',
        body: JSON.stringify({ policy_id: policyId }),
      }
    );
  }

  static async unassignPolicy(namespaceId: string, policyId: string) {
    return apiRequest<void>(
      `/admin/namespaces/${namespaceId}/policies/${policyId}`,
      {
        method: 'DELETE',
      }
    );
  }

  static async searchNamespaces(query: string, tenant_id?: string) {
    const queryParams = new URLSearchParams({ q: query });
    if (tenant_id) queryParams.set('tenant_id', tenant_id);

    return apiRequest<{
      namespaces: DeviceNamespace[];
    }>(`/admin/namespaces/search?${queryParams.toString()}`);
  }

  static async getNamespaceHierarchy(namespaceId: string) {
    return apiRequest<{
      ancestors: DeviceNamespace[];
      current: DeviceNamespace;
      children: DeviceNamespace[];
      descendants_count: number;
    }>(`/admin/namespaces/${namespaceId}/hierarchy`);
  }
}
