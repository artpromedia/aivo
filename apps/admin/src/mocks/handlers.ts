import { adminPortalHandlers } from './handlers/admin-portal';
import { authHandlers } from './handlers/auth';
import { tenantHandlers } from './handlers/tenant';

/**
 * Combine all MSW handlers for offline E2E testing
 * This ensures the admin app can run without backend dependencies
 */
export const handlers = [
  ...adminPortalHandlers,
  ...authHandlers,
  ...tenantHandlers,
];

export default handlers;
