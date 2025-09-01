// Auto-generated MSW handlers for API mocking
// Generated on: 2025-09-01T12:21:11.862Z

import { rest } from 'msw';

// Mock data fixtures
const mockFixtures = {
  auth: {
    // Add mock data for auth service
  },
  tenant: {
    // Add mock data for tenant service
  },
  enrollment: {
    // Add mock data for enrollment service
  },
  payments: {
    // Add mock data for payments service
  },
  learner: {
    // Add mock data for learner service
  },
  orchestrator: {
    // Add mock data for orchestrator service
  },
  admin-portal: {
    // Add mock data for admin-portal service
  },
};

// Generated handlers
export const handlers = [
  // AUTH Service Handlers
  rest.get('*/auth/v1/*', (req, res, ctx) => {
    return res(ctx.status(200), ctx.json(mockFixtures.auth));
  }),
  // TENANT Service Handlers
  rest.get('*/auth/v1/*', (req, res, ctx) => {
    return res(ctx.status(200), ctx.json(mockFixtures.tenant));
  }),
  // ENROLLMENT Service Handlers
  rest.get('*/auth/v1/*', (req, res, ctx) => {
    return res(ctx.status(200), ctx.json(mockFixtures.enrollment));
  }),
  // PAYMENTS Service Handlers
  rest.get('*/auth/v1/*', (req, res, ctx) => {
    return res(ctx.status(200), ctx.json(mockFixtures.payments));
  }),
  // LEARNER Service Handlers
  rest.get('*/auth/v1/*', (req, res, ctx) => {
    return res(ctx.status(200), ctx.json(mockFixtures.learner));
  }),
  // ORCHESTRATOR Service Handlers
  rest.get('*/auth/v1/*', (req, res, ctx) => {
    return res(ctx.status(200), ctx.json(mockFixtures.orchestrator));
  }),
  // ADMIN-PORTAL Service Handlers
  rest.get('*/auth/v1/*', (req, res, ctx) => {
    return res(ctx.status(200), ctx.json(mockFixtures.admin-portal));
  }),
];

export default handlers;
