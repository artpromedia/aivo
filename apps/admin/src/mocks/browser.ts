import { setupWorker } from 'msw/browser';

import { handlers } from './handlers';

/**
 * Browser MSW setup for development and E2E testing
 * This enables offline development with mocked API responses
 */
export const worker = setupWorker(...handlers);

// Start the worker in development mode
if (import.meta.env.DEV || import.meta.env.MODE === 'test') {
  worker.start({
    onUnhandledRequest: 'bypass',
    serviceWorker: {
      url: '/mockServiceWorker.js',
    },
  });
}
