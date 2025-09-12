import { http, HttpResponse } from 'msw';

// Mock invoice data
const mockInvoices: Array<{
  id: string;
  subscription_id: string;
  customer_id: string;
  status: 'paid' | 'pending' | 'failed' | 'draft' | 'overdue';
  amount_due: number;
  amount_paid: number;
  currency: string;
  invoice_number: string;
  billing_period_start: string;
  billing_period_end: string;
  issued_at: string;
  due_date: string;
  paid_at?: string;
  payment_method_id: string;
  line_items: Array<{
    id: string;
    description: string;
    quantity: number;
    unit_amount: number;
    amount: number;
    period_start: string;
    period_end: string;
  }>;
  tax_amount: number;
  discount_amount: number;
  subtotal: number;
  total: number;
  created_at: string;
  updated_at: string;
}> = [
  {
    id: 'inv_1',
    subscription_id: 'sub_1',
    customer_id: 'cus_123',
    status: 'paid' as const,
    amount_due: 2999,
    amount_paid: 2999,
    currency: 'usd',
    invoice_number: 'INV-2024-001',
    billing_period_start: '2024-01-01T00:00:00Z',
    billing_period_end: '2024-01-31T23:59:59Z',
    issued_at: '2024-01-01T00:00:00Z',
    due_date: '2024-01-15T00:00:00Z',
    paid_at: '2024-01-02T10:30:00Z',
    payment_method_id: 'pm_1',
    line_items: [
      {
        id: 'li_1',
        description: 'Professional Plan - January 2024',
        quantity: 50,
        unit_amount: 2999,
        amount: 149950,
        period_start: '2024-01-01T00:00:00Z',
        period_end: '2024-01-31T23:59:59Z',
      },
    ],
    tax_amount: 0,
    discount_amount: 0,
    subtotal: 149950,
    total: 149950,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-02T10:30:00Z',
  },
  {
    id: 'inv_2',
    subscription_id: 'sub_2',
    customer_id: 'cus_456',
    status: 'pending' as const,
    amount_due: 999,
    amount_paid: 0,
    currency: 'usd',
    invoice_number: 'INV-2024-002',
    billing_period_start: '2024-02-01T00:00:00Z',
    billing_period_end: '2024-02-29T23:59:59Z',
    issued_at: '2024-02-01T00:00:00Z',
    due_date: '2024-02-15T00:00:00Z',
    paid_at: undefined,
    payment_method_id: 'pm_2',
    line_items: [
      {
        id: 'li_2',
        description: 'Basic Plan - February 2024',
        quantity: 10,
        unit_amount: 999,
        amount: 9990,
        period_start: '2024-02-01T00:00:00Z',
        period_end: '2024-02-29T23:59:59Z',
      },
    ],
    tax_amount: 0,
    discount_amount: 0,
    subtotal: 9990,
    total: 9990,
    created_at: '2024-02-01T00:00:00Z',
    updated_at: '2024-02-01T00:00:00Z',
  },
];

// Mock payment methods
const mockPaymentMethods = [
  {
    id: 'pm_1',
    customer_id: 'cus_123',
    type: 'card' as const,
    card: {
      brand: 'visa',
      last4: '4242',
      exp_month: 12,
      exp_year: 2026,
      funding: 'credit',
    },
    billing_details: {
      name: 'John Doe',
      email: 'john@example.com',
      address: {
        line1: '123 Main St',
        city: 'San Francisco',
        state: 'CA',
        postal_code: '94102',
        country: 'US',
      },
    },
    is_default: true,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 'pm_2',
    customer_id: 'cus_456',
    type: 'card' as const,
    card: {
      brand: 'mastercard',
      last4: '8888',
      exp_month: 8,
      exp_year: 2025,
      funding: 'debit',
    },
    billing_details: {
      name: 'Jane Smith',
      email: 'jane@example.com',
      address: {
        line1: '456 Oak Ave',
        city: 'New York',
        state: 'NY',
        postal_code: '10001',
        country: 'US',
      },
    },
    is_default: true,
    created_at: '2024-01-15T00:00:00Z',
    updated_at: '2024-01-15T00:00:00Z',
  },
];

// Mock usage data
const mockUsageData = [
  {
    subscription_id: 'sub_1',
    metric: 'api_calls',
    period_start: '2024-01-01T00:00:00Z',
    period_end: '2024-01-31T23:59:59Z',
    quantity: 45230,
    unit_amount: 0.001,
    amount: 4523,
  },
  {
    subscription_id: 'sub_1',
    metric: 'storage_gb',
    period_start: '2024-01-01T00:00:00Z',
    period_end: '2024-01-31T23:59:59Z',
    quantity: 125.5,
    unit_amount: 0.1,
    amount: 1255,
  },
];

// Mock billing stats
const mockBillingStats = {
  total_revenue: 1599450, // $15,994.50 in cents
  monthly_recurring_revenue: 179945, // $1,799.45 in cents
  outstanding_amount: 9990, // $99.90 in cents
  total_customers: 15,
  active_subscriptions: 12,
  failed_payments: 2,
  upcoming_renewals: 8,
  average_invoice_value: 89957, // $899.57 in cents
};

export const billingHandlers = [
  // Get billing stats
  http.get('/api/billing/stats', () => {
    return HttpResponse.json(mockBillingStats);
  }),

  // Get invoices
  http.get('/api/billing/invoices', ({ request }) => {
    const url = new URL(request.url);
    const page = parseInt(url.searchParams.get('page') || '1');
    const limit = parseInt(url.searchParams.get('limit') || '10');
    const status = url.searchParams.get('status');
    const customer_id = url.searchParams.get('customer_id');

    let filteredInvoices = [...mockInvoices];

    if (status) {
      filteredInvoices = filteredInvoices.filter(inv => inv.status === status);
    }

    if (customer_id) {
      filteredInvoices = filteredInvoices.filter(
        inv => inv.customer_id === customer_id
      );
    }

    const startIndex = (page - 1) * limit;
    const endIndex = startIndex + limit;
    const paginatedInvoices = filteredInvoices.slice(startIndex, endIndex);

    return HttpResponse.json({
      invoices: paginatedInvoices,
      pagination: {
        page,
        limit,
        total: filteredInvoices.length,
        pages: Math.ceil(filteredInvoices.length / limit),
      },
    });
  }),

  // Get single invoice
  http.get('/api/billing/invoices/:id', ({ params }) => {
    const { id } = params;
    const invoice = mockInvoices.find(inv => inv.id === id);

    if (!invoice) {
      return new HttpResponse(null, { status: 404 });
    }

    return HttpResponse.json(invoice);
  }),

  // Download invoice PDF
  http.get('/api/billing/invoices/:id/pdf', ({ params }) => {
    const { id } = params;
    const invoice = mockInvoices.find(inv => inv.id === id);

    if (!invoice) {
      return new HttpResponse(null, { status: 404 });
    }

    // Mock PDF blob
    const pdfContent = `%PDF-1.4 Mock PDF for invoice ${invoice.invoice_number}`;
    const blob = new Blob([pdfContent], { type: 'application/pdf' });

    return new HttpResponse(blob, {
      headers: {
        'Content-Type': 'application/pdf',
        'Content-Disposition': `attachment; filename="${invoice.invoice_number}.pdf"`,
      },
    });
  }),

  // Get payment methods
  http.get('/api/billing/payment-methods', ({ request }) => {
    const url = new URL(request.url);
    const customer_id = url.searchParams.get('customer_id');

    let filteredMethods = [...mockPaymentMethods];

    if (customer_id) {
      filteredMethods = filteredMethods.filter(
        pm => pm.customer_id === customer_id
      );
    }

    return HttpResponse.json({
      payment_methods: filteredMethods,
    });
  }),

  // Add payment method
  http.post('/api/billing/payment-methods', async ({ request }) => {
    const body = (await request.json()) as {
      customer_id: string;
      type: 'card';
      card: {
        number: string;
        exp_month: number;
        exp_year: number;
        cvc: string;
      };
      billing_details: {
        name: string;
        email: string;
        address: {
          line1: string;
          city: string;
          state: string;
          postal_code: string;
          country: string;
        };
      };
      is_default?: boolean;
    };

    const newPaymentMethod = {
      id: `pm_${Date.now()}`,
      customer_id: body.customer_id,
      type: body.type,
      card: {
        brand: body.card.number.startsWith('4') ? 'visa' : 'mastercard',
        last4: body.card.number.slice(-4),
        exp_month: body.card.exp_month,
        exp_year: body.card.exp_year,
        funding: 'credit' as const,
      },
      billing_details: body.billing_details,
      is_default: body.is_default || false,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    mockPaymentMethods.push(newPaymentMethod);
    return HttpResponse.json(newPaymentMethod);
  }),

  // Update payment method
  http.put('/api/billing/payment-methods/:id', async ({ params, request }) => {
    const { id } = params;
    const body = (await request.json()) as {
      is_default?: boolean;
      billing_details?: {
        name?: string;
        email?: string;
        address?: {
          line1?: string;
          city?: string;
          state?: string;
          postal_code?: string;
          country?: string;
        };
      };
    };

    const index = mockPaymentMethods.findIndex(pm => pm.id === id);

    if (index === -1) {
      return new HttpResponse(null, { status: 404 });
    }

    const paymentMethod = { ...mockPaymentMethods[index] };

    if (body.is_default !== undefined) {
      paymentMethod.is_default = body.is_default;
      // If setting as default, make all others non-default for this customer
      if (body.is_default) {
        mockPaymentMethods.forEach(pm => {
          if (pm.customer_id === paymentMethod.customer_id && pm.id !== id) {
            pm.is_default = false;
          }
        });
      }
    }

    if (body.billing_details) {
      paymentMethod.billing_details = {
        name: body.billing_details.name || paymentMethod.billing_details.name,
        email:
          body.billing_details.email || paymentMethod.billing_details.email,
        address: {
          line1:
            body.billing_details.address?.line1 ||
            paymentMethod.billing_details.address.line1,
          city:
            body.billing_details.address?.city ||
            paymentMethod.billing_details.address.city,
          state:
            body.billing_details.address?.state ||
            paymentMethod.billing_details.address.state,
          postal_code:
            body.billing_details.address?.postal_code ||
            paymentMethod.billing_details.address.postal_code,
          country:
            body.billing_details.address?.country ||
            paymentMethod.billing_details.address.country,
        },
      };
    }

    paymentMethod.updated_at = new Date().toISOString();
    mockPaymentMethods[index] = paymentMethod;

    return HttpResponse.json(paymentMethod);
  }),

  // Delete payment method
  http.delete('/api/billing/payment-methods/:id', ({ params }) => {
    const { id } = params;
    const index = mockPaymentMethods.findIndex(pm => pm.id === id);

    if (index === -1) {
      return new HttpResponse(null, { status: 404 });
    }

    mockPaymentMethods.splice(index, 1);
    return new HttpResponse(null, { status: 204 });
  }),

  // Get usage data
  http.get('/api/billing/usage', ({ request }) => {
    const url = new URL(request.url);
    const subscription_id = url.searchParams.get('subscription_id');
    const metric = url.searchParams.get('metric');

    let filteredUsage = [...mockUsageData];

    if (subscription_id) {
      filteredUsage = filteredUsage.filter(
        usage => usage.subscription_id === subscription_id
      );
    }

    if (metric) {
      filteredUsage = filteredUsage.filter(usage => usage.metric === metric);
    }

    return HttpResponse.json({
      usage: filteredUsage,
    });
  }),

  // Process payment manually
  http.post('/api/billing/invoices/:id/pay', async ({ params }) => {
    const { id } = params;
    const invoiceIndex = mockInvoices.findIndex(inv => inv.id === id);

    if (invoiceIndex === -1) {
      return new HttpResponse(null, { status: 404 });
    }

    const invoice = mockInvoices[invoiceIndex];
    if (invoice.status === 'paid') {
      return HttpResponse.json(
        { error: 'Invoice already paid' },
        { status: 400 }
      );
    }

    const updatedInvoice = {
      ...invoice,
      status: 'paid' as const,
      amount_paid: invoice.amount_due,
      paid_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    mockInvoices[invoiceIndex] = updatedInvoice;
    return HttpResponse.json(updatedInvoice);
  }),

  // Retry failed payment
  http.post('/api/billing/invoices/:id/retry', async ({ params }) => {
    const { id } = params;
    const invoiceIndex = mockInvoices.findIndex(inv => inv.id === id);

    if (invoiceIndex === -1) {
      return new HttpResponse(null, { status: 404 });
    }

    const invoice = mockInvoices[invoiceIndex];
    if (invoice.status === 'paid') {
      return HttpResponse.json(
        { error: 'Invoice already paid' },
        { status: 400 }
      );
    }

    // Simulate retry - 80% success rate
    const success = Math.random() > 0.2;

    const updatedInvoice = {
      ...invoice,
      status: success ? ('paid' as const) : ('failed' as const),
      amount_paid: success ? invoice.amount_due : invoice.amount_paid,
      paid_at: success ? new Date().toISOString() : invoice.paid_at,
      updated_at: new Date().toISOString(),
    };

    mockInvoices[invoiceIndex] = updatedInvoice;
    return HttpResponse.json(updatedInvoice);
  }),
];
