import { requireStaff } from '@/middleware/auth';
import { GraphQLContext } from '@/types';

export const analyticsResolvers = {
  Query: {
    dashboardMetrics: requireStaff(
      async (_: any, { tenantId }: { tenantId?: string }, context: GraphQLContext) => {
        try {
          const effectiveTenantId = tenantId || context.user?.tenantId;
          if (!effectiveTenantId) {
            throw new Error('Tenant ID required');
          }

          const response =
            await context.dataSources.analyticsService.getDashboardMetrics(effectiveTenantId);

          if (response.error) {
            throw new Error(response.error);
          }

          return response.data;
        } catch (error) {
          const message = error instanceof Error ? error.message : 'Unknown error';
          throw new Error(`Failed to fetch dashboard metrics: ${message}`);
        }
      }
    ),

    learnerAnalytics: requireStaff(
      async (_: any, { learnerId }: { learnerId: string }, context: GraphQLContext) => {
        try {
          // First verify the learner exists and user has access
          const learner = await context.loaders.learnerLoader.load(learnerId);
          if (!learner) {
            throw new Error('Learner not found');
          }

          // Check tenant access
          if (learner.tenantId !== context.user?.tenantId) {
            throw new Error('Insufficient permissions to access learner analytics');
          }

          return await context.loaders.analyticsLoader.load(learnerId);
        } catch (error) {
          const message = error instanceof Error ? error.message : 'Unknown error';
          throw new Error(`Failed to fetch learner analytics: ${message}`);
        }
      }
    ),

    academicTrends: requireStaff(
      async (
        _: any,
        {
          tenantId,
          timeframe = '6months',
        }: {
          tenantId?: string;
          timeframe?: string;
        },
        context: GraphQLContext
      ) => {
        try {
          const effectiveTenantId = tenantId || context.user?.tenantId;
          if (!effectiveTenantId) {
            throw new Error('Tenant ID required');
          }

          const response = await context.dataSources.analyticsService.getAcademicTrends(
            effectiveTenantId,
            timeframe
          );

          if (response.error) {
            throw new Error(response.error);
          }

          return response.data || [];
        } catch (error) {
          const message = error instanceof Error ? error.message : 'Unknown error';
          throw new Error(`Failed to fetch academic trends: ${message}`);
        }
      }
    ),
  },

  LearnerAnalytics: {
    learner: async (parent: any, _: any, context: GraphQLContext) => {
      return context.loaders.learnerLoader.load(parent.learnerId);
    },
  },
};
