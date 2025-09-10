import { requireStaff } from '@/middleware/auth';
import { clearCacheForLearner } from '@/services/dataloaders';
import { GraphQLContext, Learner, LearnerInput, GuardianInput } from '@/types';

export const learnerResolvers = {
  Query: {
    learner: async (_: any, { id }: { id: string }, context: GraphQLContext) => {
      const learner = await context.loaders.learnerLoader.load(id);
      if (!learner) return null;

      // Check tenant access
      const authService = context.user ? new (await import('@/middleware/auth')).JWTAuthService({
        secret: process.env.JWT_SECRET || '',
        issuer: process.env.JWT_ISSUER || '',
        audience: process.env.JWT_AUDIENCE || '',
      }) : null;

      if (authService && !authService.canAccessLearnerData(context.user!, id, learner.tenantId)) {
        throw new Error('Insufficient permissions to access learner data');
      }

      return learner;
    },

    learners: requireStaff(async (
      _: any,
      { tenantId, enrollmentStatus, grade, limit = 50, offset = 0 }: any,
      context: GraphQLContext
    ) => {
      const params = {
        tenantId: tenantId || context.user?.tenantId,
        enrollmentStatus,
        grade,
        limit,
        offset,
      };

      const response = await context.dataSources.learnerService.getLearners(params);
      if (response.error) {
        throw new Error(response.error);
      }

      return response.data || [];
    }),
  },

  Mutation: {
    createLearner: requireStaff(async (
      _: any,
      { input }: { input: LearnerInput },
      context: GraphQLContext
    ) => {
      const tenantId = context.user?.tenantId;
      if (!tenantId) {
        throw new Error('Tenant ID required');
      }

      const learnerWithTenant = { ...input, tenantId };
      const response = await context.dataSources.learnerService.createLearner(learnerWithTenant as any);
      
      if (response.error) {
        throw new Error(response.error);
      }

      return response.data;
    }),

    updateLearner: requireStaff(async (
      _: any,
      { id, input }: { id: string; input: LearnerInput },
      context: GraphQLContext
    ) => {
      // First check if learner exists and user has access
      const existingLearner = await context.loaders.learnerLoader.load(id);
      if (!existingLearner) {
        throw new Error('Learner not found');
      }

      const authService = new (await import('@/middleware/auth')).JWTAuthService({
        secret: process.env.JWT_SECRET || '',
        issuer: process.env.JWT_ISSUER || '',
        audience: process.env.JWT_AUDIENCE || '',
      });

      if (!authService.canAccessLearnerData(context.user!, id, existingLearner.tenantId)) {
        throw new Error('Insufficient permissions to update learner');
      }

      const response = await context.dataSources.learnerService.updateLearner(id, input);
      
      if (response.error) {
        throw new Error(response.error);
      }

      // Clear cache for updated learner
      await clearCacheForLearner(context.cache, id);
      context.loaders.learnerLoader.clear(id);

      return response.data;
    }),

    addGuardian: requireStaff(async (
      _: any,
      { learnerId, guardian }: { learnerId: string; guardian: GuardianInput },
      context: GraphQLContext
    ) => {
      // Check learner access
      const existingLearner = await context.loaders.learnerLoader.load(learnerId);
      if (!existingLearner) {
        throw new Error('Learner not found');
      }

      const authService = new (await import('@/middleware/auth')).JWTAuthService({
        secret: process.env.JWT_SECRET || '',
        issuer: process.env.JWT_ISSUER || '',
        audience: process.env.JWT_AUDIENCE || '',
      });

      if (!authService.canAccessLearnerData(context.user!, learnerId, existingLearner.tenantId)) {
        throw new Error('Insufficient permissions to add guardian');
      }

      const response = await context.dataSources.learnerService.addGuardian(learnerId, guardian);
      
      if (response.error) {
        throw new Error(response.error);
      }

      // Clear cache for learner guardians
      await context.cache.del(`guardians:${learnerId}`);
      context.loaders.guardianLoader.clear(learnerId);

      return response.data;
    }),
  },

  Learner: {
    guardians: async (parent: Learner, _: any, context: GraphQLContext) => {
      return context.loaders.guardianLoader.load(parent.id);
    },

    ieps: async (parent: Learner, _: any, context: GraphQLContext) => {
      return context.loaders.studentIepsLoader.load(parent.id);
    },

    analytics: async (parent: Learner, _: any, context: GraphQLContext) => {
      try {
        return await context.loaders.analyticsLoader.load(parent.id);
      } catch {
        // Analytics might not exist for all learners
        return null;
      }
    },
  },
};
