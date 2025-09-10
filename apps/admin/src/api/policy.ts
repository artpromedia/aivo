import { apiRequest } from './base';

export interface PolicyConfig {
  [key: string]: unknown;
}

export interface Policy {
  id: string;
  name: string;
  description: string;
  policy_type: 'kiosk' | 'network' | 'dns' | 'study_window';
  config: PolicyConfig;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

export interface PolicyAssignment {
  id: string;
  device_id: string;
  policy_id: string;
  assigned_at: string;
  status: 'active' | 'pending' | 'failed';
  device?: {
    id: string;
    serial_number: string;
    device_type: string;
  };
  policy?: Policy;
}

export interface CreatePolicyRequest {
  name: string;
  description: string;
  policy_type: 'kiosk' | 'network' | 'dns' | 'study_window';
  config: PolicyConfig;
}

export class PolicyAPI {
  static async getPolicies(params?: {
    page?: number;
    limit?: number;
    policy_type?: string;
    is_active?: boolean;
  }) {
    const queryParams = new URLSearchParams();
    if (params?.page) queryParams.set('page', params.page.toString());
    if (params?.limit) queryParams.set('limit', params.limit.toString());
    if (params?.policy_type) queryParams.set('policy_type', params.policy_type);
    if (params?.is_active !== undefined)
      queryParams.set('is_active', params.is_active.toString());

    return apiRequest<{
      policies: Policy[];
      total: number;
      page: number;
      totalPages: number;
    }>(`/admin/policies?${queryParams.toString()}`);
  }

  static async getPolicy(policyId: string) {
    return apiRequest<Policy>(`/admin/policies/${policyId}`);
  }

  static async createPolicy(policy: CreatePolicyRequest) {
    return apiRequest<Policy>('/admin/policies', {
      method: 'POST',
      body: JSON.stringify(policy),
    });
  }

  static async updatePolicy(
    policyId: string,
    updates: Partial<CreatePolicyRequest>
  ) {
    return apiRequest<Policy>(`/admin/policies/${policyId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  static async deletePolicy(policyId: string) {
    return apiRequest<void>(`/admin/policies/${policyId}`, {
      method: 'DELETE',
    });
  }

  static async getDevicePolicies(deviceId: string) {
    return apiRequest<{
      assignments: PolicyAssignment[];
    }>(`/admin/devices/${deviceId}/policies`);
  }

  static async assignPolicy(deviceId: string, policyId: string) {
    return apiRequest<PolicyAssignment>('/admin/device-policies', {
      method: 'POST',
      body: JSON.stringify({
        device_id: deviceId,
        policy_id: policyId,
      }),
    });
  }

  static async unassignPolicy(assignmentId: string) {
    return apiRequest<void>(`/admin/device-policies/${assignmentId}`, {
      method: 'DELETE',
    });
  }

  static async bulkAssignPolicy(policyId: string, deviceIds: string[]) {
    return apiRequest<{
      successful: string[];
      failed: Array<{ device_id: string; error: string }>;
    }>('/admin/device-policies/bulk', {
      method: 'POST',
      body: JSON.stringify({
        policy_id: policyId,
        device_ids: deviceIds,
      }),
    });
  }
}
