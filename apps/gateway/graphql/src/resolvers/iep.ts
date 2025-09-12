import { requireStaff } from '@/middleware/auth';
import { clearCacheForIep } from '@/services/dataloaders';
import {
  GraphQLContext,
  IepDoc,
  IepDocInput,
  GoalInput,
  AccommodationInput,
  CrdtOperationInput,
  IepStatus,
} from '@/types';

export const iepResolvers = {
  Query: {
    iep: requireStaff(async (_: any, { id }: { id: string }, context: GraphQLContext) => {
      try {
        const iep = await context.loaders.iepLoader.load(id);
        if (!iep) return null;

        // Check tenant access
        const authService = new (await import('@/middleware/auth')).JWTAuthService({
          secret: process.env.JWT_SECRET || '',
          issuer: process.env.JWT_ISSUER || '',
          audience: process.env.JWT_AUDIENCE || '',
        });

        if (!authService.canAccessTenant(context.user!, iep.tenantId)) {
          throw new Error('Insufficient permissions to access IEP');
        }

        return iep;
      } catch {
        return null;
      }
    }),

    ieps: requireStaff(
      async (
        _: any,
        { tenantId, studentId, status, limit = 50, offset = 0 }: any,
        context: GraphQLContext
      ) => {
        try {
          const effectiveTenantId = tenantId || context.user?.tenantId;
          if (!effectiveTenantId) {
            throw new Error('Tenant ID required');
          }

          const response = await context.dataSources.iepService.getIeps({
            tenantId: effectiveTenantId,
            studentId,
            status,
            limit,
            offset,
          });

          if (response.error) {
            throw new Error(response.error);
          }

          return response.data || [];
        } catch (error) {
          const message = error instanceof Error ? error.message : 'Unknown error';
          throw new Error(`Failed to fetch IEPs: ${message}`);
        }
      }
    ),

    activeIeps: requireStaff(
      async (_: any, { tenantId }: { tenantId?: string }, context: GraphQLContext) => {
        try {
          const effectiveTenantId = tenantId || context.user?.tenantId;
          if (!effectiveTenantId) {
            throw new Error('Tenant ID required');
          }

          const response = await context.dataSources.iepService.getIeps({
            tenantId: effectiveTenantId,
            status: IepStatus.ACTIVE,
          });

          if (response.error) {
            throw new Error(response.error);
          }

          return response.data || [];
        } catch (error) {
          const message = error instanceof Error ? error.message : 'Unknown error';
          throw new Error(`Failed to fetch active IEPs: ${message}`);
        }
      }
    ),

    pendingApprovals: requireStaff(
      async (_: any, { tenantId }: { tenantId?: string }, context: GraphQLContext) => {
        try {
          const effectiveTenantId = tenantId || context.user?.tenantId;
          if (!effectiveTenantId) {
            throw new Error('Tenant ID required');
          }

          const response = await context.dataSources.iepService.getIeps({
            tenantId: effectiveTenantId,
            status: IepStatus.SUBMITTED_FOR_APPROVAL,
          });

          if (response.error) {
            throw new Error(response.error);
          }

          return response.data || [];
        } catch (error) {
          const message = error instanceof Error ? error.message : 'Unknown error';
          throw new Error(`Failed to fetch pending approvals: ${message}`);
        }
      }
    ),
  },

  Mutation: {
    createIep: requireStaff(
      async (_: any, { input }: { input: IepDocInput }, context: GraphQLContext) => {
        try {
          const tenantId = context.user?.tenantId;
          if (!tenantId) {
            throw new Error('Tenant ID required');
          }

          const iepWithTenant = {
            ...input,
            tenantId,
            createdBy: context.user!.id,
          };

          const response = await context.dataSources.iepService.createIep({
            ...iepWithTenant,
            documentVersion: '1.0',
            status: IepStatus.DRAFT,
            currentApprovalStep: 0,
            vectorClock: {},
            operations: [],
          } as any);

          if (response.error) {
            throw new Error(response.error);
          }

          return response.data;
        } catch (error) {
          const message = error instanceof Error ? error.message : 'Unknown error';
          throw new Error(`Failed to create IEP: ${message}`);
        }
      }
    ),

    saveDraft: requireStaff(
      async (
        _: any,
        { iepId, operations }: { iepId: string; operations: CrdtOperationInput[] },
        context: GraphQLContext
      ) => {
        try {
          // Verify access to IEP
          const existingIep = await context.loaders.iepLoader.load(iepId);
          if (!existingIep) {
            throw new Error('IEP not found');
          }

          // Check tenant access
          if (existingIep.tenantId !== context.user?.tenantId) {
            throw new Error('Insufficient permissions to modify IEP');
          }

          const response = await context.dataSources.iepService.saveDraft(iepId, operations);

          if (response.error) {
            throw new Error(response.error);
          }

          // Clear cache for updated IEP
          await clearCacheForIep(context.cache, iepId, existingIep.studentId);
          context.loaders.iepLoader.clear(iepId);

          return response.data;
        } catch (error) {
          const message = error instanceof Error ? error.message : 'Unknown error';
          throw new Error(`Failed to save IEP draft: ${message}`);
        }
      }
    ),

    submitForApproval: requireStaff(
      async (_: any, { iepId }: { iepId: string }, context: GraphQLContext) => {
        try {
          // Verify access to IEP
          const existingIep = await context.loaders.iepLoader.load(iepId);
          if (!existingIep) {
            throw new Error('IEP not found');
          }

          // Check tenant access
          if (existingIep.tenantId !== context.user?.tenantId) {
            throw new Error('Insufficient permissions to submit IEP');
          }

          const response = await context.dataSources.iepService.submitForApproval(iepId);

          if (response.error) {
            throw new Error(response.error);
          }

          // Clear cache for updated IEP
          await clearCacheForIep(context.cache, iepId, existingIep.studentId);
          context.loaders.iepLoader.clear(iepId);

          return response.data;
        } catch (error) {
          const message = error instanceof Error ? error.message : 'Unknown error';
          throw new Error(`Failed to submit IEP for approval: ${message}`);
        }
      }
    ),

    addGoal: requireStaff(
      async (
        _: any,
        { iepId, goal }: { iepId: string; goal: GoalInput },
        context: GraphQLContext
      ) => {
        try {
          // Verify access to IEP
          const existingIep = await context.loaders.iepLoader.load(iepId);
          if (!existingIep) {
            throw new Error('IEP not found');
          }

          // Check tenant access
          if (existingIep.tenantId !== context.user?.tenantId) {
            throw new Error('Insufficient permissions to modify IEP');
          }

          const response = await context.dataSources.iepService.addGoal(iepId, goal);

          if (response.error) {
            throw new Error(response.error);
          }

          // Clear cache for updated IEP
          await clearCacheForIep(context.cache, iepId, existingIep.studentId);
          context.loaders.iepLoader.clear(iepId);

          return response.data;
        } catch (error) {
          const message = error instanceof Error ? error.message : 'Unknown error';
          throw new Error(`Failed to add goal: ${message}`);
        }
      }
    ),

    addAccommodation: requireStaff(
      async (
        _: any,
        { iepId, accommodation }: { iepId: string; accommodation: AccommodationInput },
        context: GraphQLContext
      ) => {
        try {
          // Verify access to IEP
          const existingIep = await context.loaders.iepLoader.load(iepId);
          if (!existingIep) {
            throw new Error('IEP not found');
          }

          // Check tenant access
          if (existingIep.tenantId !== context.user?.tenantId) {
            throw new Error('Insufficient permissions to modify IEP');
          }

          const response = await context.dataSources.iepService.addAccommodation(
            iepId,
            accommodation
          );

          if (response.error) {
            throw new Error(response.error);
          }

          // Clear cache for updated IEP
          await clearCacheForIep(context.cache, iepId, existingIep.studentId);
          context.loaders.iepLoader.clear(iepId);

          return response.data;
        } catch (error) {
          const message = error instanceof Error ? error.message : 'Unknown error';
          throw new Error(`Failed to add accommodation: ${message}`);
        }
      }
    ),
  },

  IepDoc: {
    student: async (parent: IepDoc, _: any, context: GraphQLContext) => {
      if (parent.student) return parent.student;
      return context.loaders.learnerLoader.load(parent.studentId);
    },
  },
};
