import { setupServer } from 'msw/node';

import { handlers } from './handlers';

/**
 * Node.js MSW setup for Jest tests and CI/CD
 * This enables testing without running actual backend services
 */
export const server = setupServer(...handlers);

export function setupMswServer() {
  // Establish API mocking before all tests
  server.listen({ onUnhandledRequest: 'error' });
}

export function resetMswHandlers() {
  // Reset any request handlers that are declared as a part of our tests
  // (i.e. for testing one-time error scenarios)
  server.resetHandlers();
}

export function closeMswServer() {
  // Clean up after the tests are finished
  server.close();
}
