import { adminPortalHandlers } from './handlers/admin-portal';
import { authHandlers } from './handlers/auth';
import { deviceHandlers } from './handlers/device';
import { inkHandlers } from './handlers/ink';
import { otaHandlers } from './handlers/ota';
import { policyHandlers } from './handlers/policy';
import { tenantHandlers } from './handlers/tenant';
import { userHandlers } from './handlers/users';

/**
 * Combine all MSW handlers for offline E2E testing
 * This ensures the admin app can run without backend dependencies
 */
export const handlers = [
  ...adminPortalHandlers,
  ...authHandlers,
  ...tenantHandlers,
  ...deviceHandlers,
  ...inkHandlers,
  ...policyHandlers,
  ...otaHandlers,
  ...userHandlers,
];

export default handlers;
