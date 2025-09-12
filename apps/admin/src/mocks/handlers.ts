import { adminPortalHandlers } from './handlers/admin-portal';
import { authHandlers } from './handlers/auth';
import { billingHandlers } from './handlers/billing';
import { deviceHandlers } from './handlers/device';
import { inkHandlers } from './handlers/ink';
import { namespacesHandlers } from './handlers/namespaces';
import { otaHandlers } from './handlers/ota';
import { policyHandlers } from './handlers/policy';
import { subscriptionHandlers } from './handlers/subscriptions';
import { tenantHandlers } from './handlers/tenant';
import { userHandlers } from './handlers/users';

/**
 * Combine all MSW handlers for offline E2E testing
 * This ensures the admin app can run without backend dependencies
 */
export const handlers = [
  ...adminPortalHandlers,
  ...authHandlers,
  ...billingHandlers,
  ...deviceHandlers,
  ...inkHandlers,
  ...namespacesHandlers,
  ...otaHandlers,
  ...policyHandlers,
  ...subscriptionHandlers,
  ...tenantHandlers,
  ...userHandlers,
];

export default handlers;
