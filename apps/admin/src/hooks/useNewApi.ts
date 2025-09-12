import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import {
  SubscriptionsAPI,
  BillingAPI,
  NamespacesAPI,
  type CreateSubscriptionRequest,
  type UpdateSubscriptionRequest,
  type BillingSettings,
  type CreateNamespaceRequest,
  type UpdateNamespaceRequest,
  type MoveDevicesRequest,
} from '@/api';

// Subscription hooks
export const useSubscriptions = (params?: {
  page?: number;
  limit?: number;
  status?: string;
  tenant_id?: string;
}) => {
  return useQuery({
    queryKey: ['subscriptions', params],
    queryFn: () => SubscriptionsAPI.getSubscriptions(params),
  });
};

export const useSubscription = (subscriptionId: string) => {
  return useQuery({
    queryKey: ['subscriptions', subscriptionId],
    queryFn: () => SubscriptionsAPI.getSubscription(subscriptionId),
    enabled: !!subscriptionId,
  });
};

export const useSubscriptionPlans = () => {
  return useQuery({
    queryKey: ['subscription-plans'],
    queryFn: SubscriptionsAPI.getAvailablePlans,
  });
};

export const useSubscriptionUsage = (subscriptionId: string) => {
  return useQuery({
    queryKey: ['subscriptions', subscriptionId, 'usage'],
    queryFn: () => SubscriptionsAPI.getSubscriptionUsage(subscriptionId),
    enabled: !!subscriptionId,
  });
};

export const useCreateSubscription = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateSubscriptionRequest) =>
      SubscriptionsAPI.createSubscription(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscriptions'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
};

export const useUpdateSubscription = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      subscriptionId,
      data,
    }: {
      subscriptionId: string;
      data: UpdateSubscriptionRequest;
    }) => SubscriptionsAPI.updateSubscription(subscriptionId, data),
    onSuccess: (_, { subscriptionId }) => {
      queryClient.invalidateQueries({ queryKey: ['subscriptions'] });
      queryClient.invalidateQueries({
        queryKey: ['subscriptions', subscriptionId],
      });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
};

export const useCancelSubscription = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      subscriptionId,
      cancelAtPeriodEnd,
    }: {
      subscriptionId: string;
      cancelAtPeriodEnd?: boolean;
    }) =>
      SubscriptionsAPI.cancelSubscription(subscriptionId, cancelAtPeriodEnd),
    onSuccess: (_, { subscriptionId }) => {
      queryClient.invalidateQueries({ queryKey: ['subscriptions'] });
      queryClient.invalidateQueries({
        queryKey: ['subscriptions', subscriptionId],
      });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
};

export const useReactivateSubscription = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (subscriptionId: string) =>
      SubscriptionsAPI.reactivateSubscription(subscriptionId),
    onSuccess: (_, subscriptionId) => {
      queryClient.invalidateQueries({ queryKey: ['subscriptions'] });
      queryClient.invalidateQueries({
        queryKey: ['subscriptions', subscriptionId],
      });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
};

// Billing hooks
export const useBillingHistory = (tenantId: string) => {
  return useQuery({
    queryKey: ['billing', tenantId, 'history'],
    queryFn: () => BillingAPI.getBillingHistory(tenantId),
    enabled: !!tenantId,
  });
};

export const useInvoices = (params?: {
  page?: number;
  limit?: number;
  status?: string;
  tenant_id?: string;
  date_from?: string;
  date_to?: string;
}) => {
  return useQuery({
    queryKey: ['billing', 'invoices', params],
    queryFn: () => BillingAPI.getInvoices(params),
  });
};

export const useInvoice = (invoiceId: string) => {
  return useQuery({
    queryKey: ['billing', 'invoices', invoiceId],
    queryFn: () => BillingAPI.getInvoice(invoiceId),
    enabled: !!invoiceId,
  });
};

export const useDownloadInvoice = () => {
  return useMutation({
    mutationFn: BillingAPI.downloadInvoice,
    onSuccess: (blob: Blob, invoiceId: string) => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `invoice-${invoiceId}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    },
  });
};

export const usePaymentMethods = (tenantId: string) => {
  return useQuery({
    queryKey: ['billing', tenantId, 'payment-methods'],
    queryFn: () => BillingAPI.getPaymentMethods(tenantId),
    enabled: !!tenantId,
  });
};

export const useAddPaymentMethod = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      tenantId,
      paymentMethodData,
    }: {
      tenantId: string;
      paymentMethodData: { type: string; token: string; is_default?: boolean };
    }) => BillingAPI.addPaymentMethod(tenantId, paymentMethodData),
    onSuccess: (_, { tenantId }) => {
      queryClient.invalidateQueries({
        queryKey: ['billing', tenantId, 'payment-methods'],
      });
    },
  });
};

export const useRemovePaymentMethod = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      tenantId,
      paymentMethodId,
    }: {
      tenantId: string;
      paymentMethodId: string;
    }) => BillingAPI.removePaymentMethod(tenantId, paymentMethodId),
    onSuccess: (_, { tenantId }) => {
      queryClient.invalidateQueries({
        queryKey: ['billing', tenantId, 'payment-methods'],
      });
    },
  });
};

export const useSetDefaultPaymentMethod = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      tenantId,
      paymentMethodId,
    }: {
      tenantId: string;
      paymentMethodId: string;
    }) => BillingAPI.setDefaultPaymentMethod(tenantId, paymentMethodId),
    onSuccess: (_, { tenantId }) => {
      queryClient.invalidateQueries({
        queryKey: ['billing', tenantId, 'payment-methods'],
      });
    },
  });
};

export const useBillingSettings = (tenantId: string) => {
  return useQuery({
    queryKey: ['billing', tenantId, 'settings'],
    queryFn: () => BillingAPI.getBillingSettings(tenantId),
    enabled: !!tenantId,
  });
};

export const useUpdateBillingSettings = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      tenantId,
      settings,
    }: {
      tenantId: string;
      settings: Partial<BillingSettings>;
    }) => BillingAPI.updateBillingSettings(tenantId, settings),
    onSuccess: (_, { tenantId }) => {
      queryClient.invalidateQueries({
        queryKey: ['billing', tenantId, 'settings'],
      });
    },
  });
};

export const useUsageMetrics = (tenantId: string, period?: string) => {
  return useQuery({
    queryKey: ['billing', tenantId, 'usage', period],
    queryFn: () => BillingAPI.getUsageMetrics(tenantId, period),
    enabled: !!tenantId,
  });
};

// Namespace hooks
export const useNamespaces = (params?: {
  page?: number;
  limit?: number;
  parent_id?: string;
  tenant_id?: string;
  include_children?: boolean;
}) => {
  return useQuery({
    queryKey: ['namespaces', params],
    queryFn: () => NamespacesAPI.getNamespaces(params),
  });
};

export const useNamespace = (namespaceId: string) => {
  return useQuery({
    queryKey: ['namespaces', namespaceId],
    queryFn: () => NamespacesAPI.getNamespace(namespaceId),
    enabled: !!namespaceId,
  });
};

export const useNamespaceTree = (tenantId?: string) => {
  return useQuery({
    queryKey: ['namespaces', 'tree', tenantId],
    queryFn: () => NamespacesAPI.getNamespaceTree(tenantId),
  });
};

export const useNamespaceDevices = (
  namespaceId: string,
  params?: {
    page?: number;
    limit?: number;
    status?: string;
    device_type?: string;
  }
) => {
  return useQuery({
    queryKey: ['namespaces', namespaceId, 'devices', params],
    queryFn: () => NamespacesAPI.getNamespaceDevices(namespaceId, params),
    enabled: !!namespaceId,
  });
};

export const useNamespacePolicies = (namespaceId: string) => {
  return useQuery({
    queryKey: ['namespaces', namespaceId, 'policies'],
    queryFn: () => NamespacesAPI.getNamespacePolicies(namespaceId),
    enabled: !!namespaceId,
  });
};

export const useNamespaceStats = (namespaceId: string) => {
  return useQuery({
    queryKey: ['namespaces', namespaceId, 'stats'],
    queryFn: () => NamespacesAPI.getNamespaceStats(namespaceId),
    enabled: !!namespaceId,
  });
};

export const useCreateNamespace = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateNamespaceRequest) =>
      NamespacesAPI.createNamespace(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['namespaces'] });
      queryClient.invalidateQueries({ queryKey: ['namespaces', 'tree'] });
    },
  });
};

export const useUpdateNamespace = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      namespaceId,
      data,
    }: {
      namespaceId: string;
      data: UpdateNamespaceRequest;
    }) => NamespacesAPI.updateNamespace(namespaceId, data),
    onSuccess: (_, { namespaceId }) => {
      queryClient.invalidateQueries({ queryKey: ['namespaces'] });
      queryClient.invalidateQueries({ queryKey: ['namespaces', namespaceId] });
      queryClient.invalidateQueries({ queryKey: ['namespaces', 'tree'] });
    },
  });
};

export const useDeleteNamespace = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      namespaceId,
      force,
    }: {
      namespaceId: string;
      force?: boolean;
    }) => NamespacesAPI.deleteNamespace(namespaceId, force),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['namespaces'] });
      queryClient.invalidateQueries({ queryKey: ['namespaces', 'tree'] });
    },
  });
};

export const useMoveDevices = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: MoveDevicesRequest) => NamespacesAPI.moveDevices(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['namespaces'] });
      queryClient.invalidateQueries({ queryKey: ['devices'] });
    },
  });
};

export const useAssignPolicy = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      namespaceId,
      policyId,
    }: {
      namespaceId: string;
      policyId: string;
    }) => NamespacesAPI.assignPolicy(namespaceId, policyId),
    onSuccess: (_, { namespaceId }) => {
      queryClient.invalidateQueries({
        queryKey: ['namespaces', namespaceId, 'policies'],
      });
    },
  });
};

export const useUnassignPolicy = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      namespaceId,
      policyId,
    }: {
      namespaceId: string;
      policyId: string;
    }) => NamespacesAPI.unassignPolicy(namespaceId, policyId),
    onSuccess: (_, { namespaceId }) => {
      queryClient.invalidateQueries({
        queryKey: ['namespaces', namespaceId, 'policies'],
      });
    },
  });
};
