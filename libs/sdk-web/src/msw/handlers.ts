// Auto-generated MSW handlers for API mocking
// Generated on: 2025-09-01T12:21:11.862Z

import { http, HttpResponse } from 'msw';

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
  'admin-portal': {
    // Add mock data for admin-portal service
  },
};

// Generated handlers
export const handlers = [
  // AUTH Service Handlers
  http.get('*/auth/v1/*', () => {
    return HttpResponse.json(mockFixtures.auth);
  }),
  // TENANT Service Handlers
  http.get('*/tenant/v1/*', () => {
    return HttpResponse.json(mockFixtures.tenant);
  }),
  // ENROLLMENT Service Handlers
  http.get('*/enrollment/v1/*', () => {
    return HttpResponse.json(mockFixtures.enrollment);
  }),
  // PAYMENTS Service Handlers
  http.get('*/payments/v1/*', () => {
    return HttpResponse.json(mockFixtures.payments);
  }),
  // LEARNER Service Handlers
  http.get('*/learner/v1/*', () => {
    return HttpResponse.json(mockFixtures.learner);
  }),
  // ORCHESTRATOR Service Handlers
  http.get('*/orchestrator/v1/*', () => {
    return HttpResponse.json(mockFixtures.orchestrator);
  }),
  // ADMIN-PORTAL Service Handlers
  http.get('*/admin-portal/v1/*', () => {
    return HttpResponse.json(mockFixtures['admin-portal']);
  }),
];

export default handlers;
