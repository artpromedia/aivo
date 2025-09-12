import { requireStaff } from '@/middleware/auth';
import { GraphQLContext, DashboardMetrics } from '@/types';

export const dashboardResolvers = {
  Query: {
    dashboard: requireStaff(
      async (_: any, { tenantId }: { tenantId?: string }, context: GraphQLContext) => {
        try {
          const effectiveTenantId = tenantId || context.user?.tenantId;
          if (!effectiveTenantId) {
            throw new Error('Tenant ID required');
          }

          const response =
            await context.dataSources.adminPortalService.getDashboardData(effectiveTenantId);

          if (response.error) {
            throw new Error(response.error);
          }

          return response.data;
        } catch (error) {
          const message = error instanceof Error ? error.message : 'Unknown error';
          throw new Error(`Failed to fetch dashboard data: ${message}`);
        }
      }
    ),
  },

  DashboardMetrics: {
    // Add any computed fields if needed
    totalActiveStudents: (parent: DashboardMetrics) => {
      return parent.totalLearners; // For backwards compatibility
    },
  },
};
