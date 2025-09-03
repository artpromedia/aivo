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
}
