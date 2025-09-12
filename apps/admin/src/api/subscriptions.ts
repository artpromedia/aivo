import { apiRequest } from './base';

export interface Subscription {
  id: string;
  tenant_id: string;
  plan_id: string;
  plan_name: string;
  status: 'active' | 'canceled' | 'past_due' | 'trialing' | 'paused';
  current_period_start: string;
  current_period_end: string;
  cancel_at_period_end: boolean;
  canceled_at?: string;
  trial_start?: string;
  trial_end?: string;
  quantity: number;
  unit_amount: number;
  currency: string;
  billing_cycle: 'monthly' | 'yearly';
  created_at: string;
  updated_at: string;
  metadata?: Record<string, string>;
}

export interface SubscriptionPlan {
  id: string;
  name: string;
  description: string;
  amount: number;
  currency: string;
  interval: 'month' | 'year';
  interval_count: number;
  usage_type: 'licensed' | 'metered';
  features: string[];
  max_users?: number;
  max_devices?: number;
  storage_gb?: number;
  created_at: string;
  updated_at: string;
}

export interface SubscriptionUsage {
  subscription_id: string;
  period_start: string;
  period_end: string;
  usage_records: {
    metric: string;
    quantity: number;
    unit: string;
    description: string;
  }[];
  total_cost: number;
  currency: string;
}

export interface CreateSubscriptionRequest {
  tenant_id: string;
  plan_id: string;
  quantity?: number;
  trial_period_days?: number;
  payment_method_id?: string;
  metadata?: Record<string, string>;
}

export interface UpdateSubscriptionRequest {
  plan_id?: string;
  quantity?: number;
  cancel_at_period_end?: boolean;
  metadata?: Record<string, string>;
}

export class SubscriptionsAPI {
  static async getSubscriptions(params?: {
    page?: number;
    limit?: number;
    status?: string;
    tenant_id?: string;
  }) {
    const queryParams = new URLSearchParams();
    if (params?.page) queryParams.set('page', params.page.toString());
    if (params?.limit) queryParams.set('limit', params.limit.toString());
    if (params?.status) queryParams.set('status', params.status);
    if (params?.tenant_id) queryParams.set('tenant_id', params.tenant_id);

    return apiRequest<{
      subscriptions: Subscription[];
      total: number;
      page: number;
      totalPages: number;
    }>(`/admin/subscriptions?${queryParams.toString()}`);
  }

  static async getSubscription(subscriptionId: string) {
    return apiRequest<Subscription>(`/admin/subscriptions/${subscriptionId}`);
  }

  static async createSubscription(data: CreateSubscriptionRequest) {
    return apiRequest<Subscription>('/admin/subscriptions', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  static async updateSubscription(
    subscriptionId: string,
    data: UpdateSubscriptionRequest
  ) {
    return apiRequest<Subscription>(`/admin/subscriptions/${subscriptionId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  static async cancelSubscription(
    subscriptionId: string,
    cancelAtPeriodEnd = true
  ) {
    return apiRequest<Subscription>(
      `/admin/subscriptions/${subscriptionId}/cancel`,
      {
        method: 'POST',
        body: JSON.stringify({ cancel_at_period_end: cancelAtPeriodEnd }),
      }
    );
  }

  static async reactivateSubscription(subscriptionId: string) {
    return apiRequest<Subscription>(
      `/admin/subscriptions/${subscriptionId}/reactivate`,
      {
        method: 'POST',
      }
    );
  }

  static async getSubscriptionUsage(subscriptionId: string) {
    return apiRequest<SubscriptionUsage>(
      `/admin/subscriptions/${subscriptionId}/usage`
    );
  }

  static async getAvailablePlans() {
    return apiRequest<{
      plans: SubscriptionPlan[];
    }>('/admin/subscription-plans');
  }

  static async getSubscriptionsByTenant(tenantId: string) {
    return apiRequest<{
      subscriptions: Subscription[];
    }>(`/admin/tenants/${tenantId}/subscriptions`);
  }
}
