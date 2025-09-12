import { apiRequest } from './base';

export interface Invoice {
  id: string;
  invoice_number: string;
  tenant_id: string;
  subscription_id?: string;
  amount: number;
  currency: string;
  status: 'draft' | 'open' | 'paid' | 'void' | 'uncollectible';
  due_date: string;
  paid_at?: string;
  created_at: string;
  updated_at: string;
  download_url?: string;
  description?: string;
  line_items: InvoiceLineItem[];
  tax_amount: number;
  discount_amount: number;
  total_amount: number;
}

export interface InvoiceLineItem {
  id: string;
  description: string;
  quantity: number;
  unit_amount: number;
  total_amount: number;
  period_start?: string;
  period_end?: string;
}

export interface PaymentMethod {
  id: string;
  tenant_id: string;
  type: 'card' | 'bank_account' | 'paypal';
  card?: {
    brand: string;
    last4: string;
    exp_month: number;
    exp_year: number;
  };
  bank_account?: {
    bank_name: string;
    last4: string;
    account_type: string;
  };
  is_default: boolean;
  created_at: string;
}

export interface BillingHistory {
  tenant_id: string;
  current_balance: string;
  next_payment_due?: string;
  payment_method?: PaymentMethod;
  invoices: Invoice[];
  total_spent_ytd: string;
  payment_history: PaymentRecord[];
}

export interface PaymentRecord {
  id: string;
  amount: number;
  currency: string;
  status: 'succeeded' | 'failed' | 'pending' | 'refunded';
  created_at: string;
  payment_method_type: string;
  description?: string;
  invoice_id?: string;
}

export interface BillingSettings {
  tenant_id: string;
  billing_email: string;
  billing_address: {
    line1: string;
    line2?: string;
    city: string;
    state: string;
    postal_code: string;
    country: string;
  };
  tax_id?: string;
  auto_pay_enabled: boolean;
  invoice_prefix: string;
  billing_cycle_day: number;
}

export interface UsageMetrics {
  tenant_id: string;
  period_start: string;
  period_end: string;
  metrics: {
    users_active: number;
    devices_enrolled: number;
    storage_used_gb: number;
    api_calls: number;
    ink_operations: number;
    ml_inferences: number;
  };
  costs: {
    base_subscription: number;
    overage_charges: number;
    total: number;
  };
  currency: string;
}

export class BillingAPI {
  static async getBillingHistory(tenantId: string) {
    return apiRequest<BillingHistory>(`/admin/billing/${tenantId}/history`);
  }

  static async getInvoices(params?: {
    page?: number;
    limit?: number;
    status?: string;
    tenant_id?: string;
    date_from?: string;
    date_to?: string;
  }) {
    const queryParams = new URLSearchParams();
    if (params?.page) queryParams.set('page', params.page.toString());
    if (params?.limit) queryParams.set('limit', params.limit.toString());
    if (params?.status) queryParams.set('status', params.status);
    if (params?.tenant_id) queryParams.set('tenant_id', params.tenant_id);
    if (params?.date_from) queryParams.set('date_from', params.date_from);
    if (params?.date_to) queryParams.set('date_to', params.date_to);

    return apiRequest<{
      invoices: Invoice[];
      total: number;
      page: number;
      totalPages: number;
    }>(`/admin/billing/invoices?${queryParams.toString()}`);
  }

  static async getInvoice(invoiceId: string) {
    return apiRequest<Invoice>(`/admin/billing/invoices/${invoiceId}`);
  }

  static async downloadInvoice(invoiceId: string) {
    const response = await fetch(
      `/admin/billing/invoices/${invoiceId}/download`,
      {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      }
    );

    if (!response.ok) {
      throw new Error('Failed to download invoice');
    }

    return response.blob();
  }

  static async getPaymentMethods(tenantId: string) {
    return apiRequest<{
      payment_methods: PaymentMethod[];
    }>(`/admin/billing/${tenantId}/payment-methods`);
  }

  static async addPaymentMethod(
    tenantId: string,
    paymentMethodData: {
      type: string;
      token: string;
      is_default?: boolean;
    }
  ) {
    return apiRequest<PaymentMethod>(
      `/admin/billing/${tenantId}/payment-methods`,
      {
        method: 'POST',
        body: JSON.stringify(paymentMethodData),
      }
    );
  }

  static async removePaymentMethod(tenantId: string, paymentMethodId: string) {
    return apiRequest<void>(
      `/admin/billing/${tenantId}/payment-methods/${paymentMethodId}`,
      {
        method: 'DELETE',
      }
    );
  }

  static async setDefaultPaymentMethod(
    tenantId: string,
    paymentMethodId: string
  ) {
    return apiRequest<PaymentMethod>(
      `/admin/billing/${tenantId}/payment-methods/${paymentMethodId}/default`,
      {
        method: 'POST',
      }
    );
  }

  static async getBillingSettings(tenantId: string) {
    return apiRequest<BillingSettings>(`/admin/billing/${tenantId}/settings`);
  }

  static async updateBillingSettings(
    tenantId: string,
    settings: Partial<BillingSettings>
  ) {
    return apiRequest<BillingSettings>(`/admin/billing/${tenantId}/settings`, {
      method: 'PUT',
      body: JSON.stringify(settings),
    });
  }

  static async getUsageMetrics(tenantId: string, period?: string) {
    const queryParams = new URLSearchParams();
    if (period) queryParams.set('period', period);

    return apiRequest<UsageMetrics>(
      `/admin/billing/${tenantId}/usage?${queryParams.toString()}`
    );
  }

  static async createInvoice(
    tenantId: string,
    invoiceData: {
      description: string;
      line_items: Omit<InvoiceLineItem, 'id'>[];
      due_date: string;
    }
  ) {
    return apiRequest<Invoice>(`/admin/billing/${tenantId}/invoices`, {
      method: 'POST',
      body: JSON.stringify(invoiceData),
    });
  }

  static async voidInvoice(invoiceId: string) {
    return apiRequest<Invoice>(`/admin/billing/invoices/${invoiceId}/void`, {
      method: 'POST',
    });
  }

  static async retryPayment(invoiceId: string) {
    return apiRequest<Invoice>(`/admin/billing/invoices/${invoiceId}/retry`, {
      method: 'POST',
    });
  }
}
