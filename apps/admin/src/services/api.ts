// API Base URL - points to Kong Gateway
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Auth token management
let authToken: string | null = localStorage.getItem('admin_token');

export const setAuthToken = (token: string | null) => {
  authToken = token;
  if (token) {
    localStorage.setItem('admin_token', token);
  } else {
    localStorage.removeItem('admin_token');
  }
};

export const getAuthToken = () => authToken;

// Generic API request function
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    throw new Error(`API Error: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

// API Service classes
export class AdminPortalAPI {
  static async getDashboardSummary() {
    return apiRequest<{
      totalUsers: number;
      activeSubscriptions: number;
      monthlyRevenue: number;
      pendingApprovals: number;
      systemHealth: string;
    }>('/admin/dashboard/summary');
  }

  static async getUsageAnalytics() {
    return apiRequest<{
      labels: string[];
      datasets: Array<{
        label: string;
        data: number[];
        borderColor: string;
        backgroundColor: string;
      }>;
    }>('/admin/analytics/usage');
  }
}

export class UserAPI {
  static async getUsers(page = 1, limit = 10) {
    return apiRequest<{
      users: Array<{
        id: string;
        username: string;
        email: string;
        role: string;
        status: string;
        lastLogin: string;
        createdAt: string;
      }>;
      total: number;
      page: number;
      totalPages: number;
    }>(`/admin/users?page=${page}&limit=${limit}`);
  }

  static async updateUserRole(userId: string, role: string) {
    return apiRequest(`/admin/users/${userId}/role`, {
      method: 'PUT',
      body: JSON.stringify({ role }),
    });
  }

  static async deactivateUser(userId: string) {
    return apiRequest(`/admin/users/${userId}/deactivate`, {
      method: 'POST',
    });
  }
}

export class SubscriptionAPI {
  static async getSubscriptions() {
    return apiRequest<{
      current: {
        plan: string;
        seats: number;
        usedSeats: number;
        billing: string;
        nextBilling: string;
        amount: number;
      };
      availablePlans: Array<{
        id: string;
        name: string;
        price: number;
        features: string[];
        maxSeats: number;
      }>;
    }>('/admin/subscriptions');
  }

  static async changePlan(planId: string, seats: number) {
    return apiRequest('/admin/subscriptions/change', {
      method: 'POST',
      body: JSON.stringify({ planId, seats }),
    });
  }

  static async applyCoupon(couponCode: string) {
    return apiRequest('/admin/subscriptions/coupon', {
      method: 'POST',
      body: JSON.stringify({ couponCode }),
    });
  }
}

export class BillingAPI {
  static async getInvoices() {
    return apiRequest<{
      invoices: Array<{
        id: string;
        date: string;
        amount: number;
        status: string;
        description: string;
        downloadUrl: string;
      }>;
    }>('/admin/billing/invoices');
  }

  static async downloadInvoice(invoiceId: string) {
    const response = await fetch(
      `${API_BASE_URL}/admin/billing/invoices/${invoiceId}/download`,
      {
        headers: {
          Authorization: `Bearer ${authToken}`,
        },
      }
    );
    return response.blob();
  }
}

export class NamespaceAPI {
  static async getNamespaces() {
    return apiRequest<{
      namespaces: Array<{
        id: string;
        name: string;
        status: 'running' | 'stopped' | 'error';
        learners: number;
        lastActivity: string;
        resources: {
          cpu: number;
          memory: number;
          storage: number;
        };
      }>;
    }>('/admin/namespaces');
  }

  static async restartNamespace(namespaceId: string) {
    return apiRequest(`/admin/namespaces/${namespaceId}/restart`, {
      method: 'POST',
    });
  }
}

export class AuthAPI {
  static async login(username: string, password: string) {
    return apiRequest<{
      token: string;
      user: {
        id: string;
        username: string;
        role: string;
        permissions: string[];
      };
    }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
  }

  static async refreshToken() {
    return apiRequest<{ token: string }>('/auth/refresh', {
      method: 'POST',
    });
  }

  // Role management methods
  static async getRoles() {
    return apiRequest<{
      roles: Array<{
        id: string;
        name: string;
        description: string;
        permissions: string[];
      }>;
    }>('/admin/roles');
  }

  static async assignRole(userId: string, role: string) {
    return apiRequest('/admin/team/role-assign', {
      method: 'POST',
      body: JSON.stringify({ userId, role }),
    });
  }

  static async revokeRole(userId: string, role: string) {
    return apiRequest('/admin/team/role-revoke', {
      method: 'POST',
      body: JSON.stringify({ userId, role }),
    });
  }

  // Invite management methods
  static async getInvites() {
    return apiRequest<{
      invites: Array<{
        id: string;
        email: string;
        role: string;
        status: 'pending' | 'accepted' | 'expired';
        sentAt: string;
        expiresAt: string;
      }>;
    }>('/admin/invites');
  }

  static async resendInvite(inviteId: string) {
    return apiRequest('/admin/team/invite-resend', {
      method: 'POST',
      body: JSON.stringify({ inviteId }),
    });
  }
}

// RBAC API class
export class RBACAPI {
  // Permission Matrix endpoints
  static async getPermissionMatrix(tenantId?: string) {
    const params = tenantId ? `?tenant_id=${tenantId}` : '';
    return apiRequest<{
      tenant_id?: string;
      roles: Array<{
        id: string;
        name: string;
        display_name: string;
        description?: string;
        is_system: boolean;
        is_active: boolean;
        permission_count: number;
        permissions: string[];
      }>;
      permission_groups: Array<{
        resource: string;
        permissions: Array<{
          id: string;
          name: string;
          display_name: string;
          action: string;
          scope: string;
        }>;
      }>;
      matrix: Record<string, string[]>;
      summary: {
        total_roles: number;
        total_permissions: number;
        system_roles: number;
        custom_roles: number;
      };
    }>(`/admin/rbac/roles/matrix${params}`);
  }

  // Role management endpoints
  static async getRoles(tenantId?: string, includePermissions = false) {
    const params = new URLSearchParams();
    if (tenantId) params.append('tenant_id', tenantId);
    if (includePermissions) params.append('include_permissions', 'true');

    return apiRequest<{
      success: boolean;
      data: {
        roles: Array<{
          id: string;
          name: string;
          display_name: string;
          description?: string;
          tenant_id?: string;
          is_system: boolean;
          is_active: boolean;
          can_edit: boolean;
          can_delete: boolean;
          user_count: number;
          permissions?: Array<{
            id: string;
            name: string;
            display_name: string;
            resource: string;
            action: string;
            scope: string;
          }>;
        }>;
        summary: {
          total: number;
          system_roles: number;
          custom_roles: number;
          active_roles: number;
        };
      };
    }>(`/admin/rbac/roles?${params.toString()}`);
  }

  static async createCustomRole(
    name: string,
    displayName: string,
    description?: string,
    tenantId?: string
  ) {
    const params = tenantId ? `?tenant_id=${tenantId}` : '';
    return apiRequest(`/admin/rbac/roles/custom${params}`, {
      method: 'POST',
      body: JSON.stringify({
        name,
        display_name: displayName,
        description,
        tenant_id: tenantId,
      }),
    });
  }

  static async updateRole(
    roleId: string,
    updates: Record<string, unknown>,
    tenantId?: string
  ) {
    const params = tenantId ? `?tenant_id=${tenantId}` : '';
    return apiRequest(`/admin/rbac/roles/${roleId}${params}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  static async deleteRole(roleId: string, tenantId?: string) {
    const params = tenantId ? `?tenant_id=${tenantId}` : '';
    return apiRequest(`/admin/rbac/roles/${roleId}${params}`, {
      method: 'DELETE',
    });
  }

  // Permission management endpoints
  static async getPermissions(tenantId?: string) {
    const params = tenantId ? `?tenant_id=${tenantId}` : '';
    return apiRequest<{
      success: boolean;
      data: {
        grouped_permissions: Array<{
          resource: string;
          permissions: Array<{
            id: string;
            name: string;
            display_name: string;
            resource: string;
            action: string;
            scope: string;
          }>;
        }>;
        all_permissions: Array<{
          id: string;
          name: string;
          display_name: string;
          resource: string;
          action: string;
          scope: string;
        }>;
        summary: {
          total_permissions: number;
          resources: number;
        };
      };
    }>(`/admin/rbac/permissions${params}`);
  }

  static async updateRolePermissions(
    roleId: string,
    permissionIds: string[],
    tenantId?: string
  ) {
    const params = tenantId ? `?tenant_id=${tenantId}` : '';
    return apiRequest(`/admin/rbac/roles/${roleId}/permissions${params}`, {
      method: 'PUT',
      body: JSON.stringify({ permission_ids: permissionIds }),
    });
  }

  // User role assignment endpoints
  static async assignUserRole(
    userId: string,
    roleId: string,
    tenantId?: string,
    expiresAt?: string
  ) {
    const params = tenantId ? `?tenant_id=${tenantId}` : '';
    return apiRequest(`/admin/rbac/users/roles/assign${params}`, {
      method: 'POST',
      body: JSON.stringify({
        user_id: userId,
        role_id: roleId,
        tenant_id: tenantId,
        expires_at: expiresAt,
      }),
    });
  }

  static async revokeUserRole(userRoleId: string, tenantId?: string) {
    const params = tenantId ? `?tenant_id=${tenantId}` : '';
    return apiRequest(`/admin/rbac/users/roles/${userRoleId}${params}`, {
      method: 'DELETE',
    });
  }

  static async getUserRoles(userId: string, tenantId?: string) {
    const params = new URLSearchParams();
    if (tenantId) params.append('tenant_id', tenantId);

    return apiRequest<{
      success: boolean;
      data: {
        user_id: string;
        tenant_id?: string;
        roles: Array<{
          id: string;
          name: string;
          display_name: string;
          expires_at?: string;
        }>;
      };
    }>(`/admin/rbac/users/${userId}/roles?${params.toString()}`);
  }

  static async getUserPermissions(userId: string, tenantId?: string) {
    const params = new URLSearchParams();
    if (tenantId) params.append('tenant_id', tenantId);

    return apiRequest<{
      success: boolean;
      data: {
        user_id: string;
        tenant_id?: string;
        permissions: string[];
      };
    }>(`/admin/rbac/users/${userId}/permissions?${params.toString()}`);
  }

  // Access Review endpoints
  static async createAccessReview(
    title: string,
    description?: string,
    tenantId?: string,
    scope = 'admin',
    targetRoleId?: string,
    dueDays = 30
  ) {
    const params = tenantId ? `?tenant_id=${tenantId}` : '';
    return apiRequest(`/admin/rbac/access-reviews/start${params}`, {
      method: 'POST',
      body: JSON.stringify({
        title,
        description,
        tenant_id: tenantId,
        scope,
        target_role_id: targetRoleId,
        due_days: dueDays,
      }),
    });
  }

  static async getAccessReviews(tenantId?: string, status?: string) {
    const params = new URLSearchParams();
    if (tenantId) params.append('tenant_id', tenantId);
    if (status) params.append('status', status);

    return apiRequest<{
      success: boolean;
      data: {
        reviews: Array<{
          id: string;
          title: string;
          description?: string;
          tenant_id?: string;
          scope: string;
          status: string;
          total_items: number;
          reviewed_items: number;
          approved_items: number;
          revoked_items: number;
          due_date: string;
          created_at: string;
          started_at?: string;
          completed_at?: string;
          progress_percentage: number;
          is_overdue: boolean;
          days_remaining?: number;
          can_complete: boolean;
          urgency_level: string;
        }>;
        summary: {
          total: number;
          active: number;
          completed: number;
          overdue: number;
        };
      };
    }>(`/admin/rbac/access-reviews?${params.toString()}`);
  }

  static async getReviewItems(
    reviewId: string,
    tenantId?: string,
    status?: string
  ) {
    const params = new URLSearchParams();
    if (tenantId) params.append('tenant_id', tenantId);
    if (status) params.append('status', status);

    return apiRequest<{
      success: boolean;
      data: {
        review_id: string;
        items: Array<{
          id: string;
          user_id: string;
          user_name: string;
          role_id: string;
          role_name: string;
          status: string;
          last_access_date?: string;
          role_privileges: string[];
          needs_attention: boolean;
          risk_level: string;
          formatted_last_access: string;
        }>;
        summary: {
          total: number;
          pending: number;
          approved: number;
          revoked: number;
        };
      };
    }>(`/admin/rbac/access-reviews/${reviewId}/items?${params.toString()}`);
  }

  static async submitReviewDecision(
    reviewId: string,
    itemId: string,
    decision: string,
    notes?: string,
    justification?: string,
    tenantId?: string
  ) {
    const params = new URLSearchParams();
    params.append('item_id', itemId);
    if (tenantId) params.append('tenant_id', tenantId);

    return apiRequest(
      `/admin/rbac/access-reviews/${reviewId}/decision?${params.toString()}`,
      {
        method: 'POST',
        body: JSON.stringify({
          decision,
          notes,
          justification,
        }),
      }
    );
  }

  // Audit logs endpoint
  static async getAuditLogs(
    tenantId?: string,
    entityType?: string,
    entityId?: string,
    limit = 100
  ) {
    const params = new URLSearchParams();
    if (tenantId) params.append('tenant_id', tenantId);
    if (entityType) params.append('entity_type', entityType);
    if (entityId) params.append('entity_id', entityId);
    params.append('limit', limit.toString());

    return apiRequest<{
      success: boolean;
      data: Array<{
        id: string;
        event_type: string;
        entity_type: string;
        entity_id: string;
        actor_id: string;
        tenant_id?: string;
        event_data: Record<string, unknown>;
        changes: Record<string, unknown>;
        timestamp: string;
      }>;
    }>(`/admin/rbac/audit-logs?${params.toString()}`);
  }
}
