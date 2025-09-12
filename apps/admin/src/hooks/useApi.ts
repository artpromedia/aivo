import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

import {
  AdminPortalAPI,
  UserAPI,
  SubscriptionAPI,
  BillingAPI,
  NamespaceAPI,
} from '@/services/api';

// Dashboard hooks
export const useDashboardSummary = () => {
  return useQuery({
    queryKey: ['dashboard', 'summary'],
    queryFn: AdminPortalAPI.getDashboardSummary,
  });
};

export const useUsageAnalytics = () => {
  return useQuery({
    queryKey: ['analytics', 'usage'],
    queryFn: AdminPortalAPI.getUsageAnalytics,
  });
};

// User management hooks
export const useUsers = (page = 1, limit = 10) => {
  return useQuery({
    queryKey: ['users', page, limit],
    queryFn: () => UserAPI.getUsers(page, limit),
  });
};

export const useUpdateUserRole = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: string }) =>
      UserAPI.updateUserRole(userId, role),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
};

export const useDeactivateUser = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (userId: string) => UserAPI.deactivateUser(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
};

// Subscription hooks
export const useSubscriptions = () => {
  return useQuery({
    queryKey: ['subscriptions'],
    queryFn: SubscriptionAPI.getSubscriptions,
  });
};

export const useChangePlan = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ planId, seats }: { planId: string; seats: number }) =>
      SubscriptionAPI.changePlan(planId, seats),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscriptions'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
};

export const useApplyCoupon = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (couponCode: string) => SubscriptionAPI.applyCoupon(couponCode),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscriptions'] });
    },
  });
};

// Billing hooks
export const useInvoices = () => {
  return useQuery({
    queryKey: ['billing', 'invoices'],
    queryFn: BillingAPI.getInvoices,
  });
};

export const useDownloadInvoice = () => {
  return useMutation({
    mutationFn: (invoiceId: string) => BillingAPI.downloadInvoice(invoiceId),
    onSuccess: (blob: Blob, invoiceId: string) => {
      // Create download link
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

// Namespace hooks
export const useNamespaces = () => {
  return useQuery({
    queryKey: ['namespaces'],
    queryFn: NamespaceAPI.getNamespaces,
  });
};

export const useRestartNamespace = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (namespaceId: string) =>
      NamespaceAPI.restartNamespace(namespaceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['namespaces'] });
    },
  });
};

// Role management hooks
export const useRoles = () => {
  return useQuery({
    queryKey: ['roles'],
    queryFn: UserAPI.getRoles,
  });
};

export const useAssignRole = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: string }) =>
      UserAPI.assignRole(userId, role),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
};

export const useRevokeRole = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: string }) =>
      UserAPI.revokeRole(userId, role),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
};

// Invite management hooks
export const useInvites = () => {
  return useQuery({
    queryKey: ['invites'],
    queryFn: UserAPI.getInvites,
  });
};

export const useResendInvite = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (inviteId: string) => UserAPI.resendInvite(inviteId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invites'] });
    },
  });
};
