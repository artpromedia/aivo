/// <reference types="vitest/globals" />

import {
  setupMswServer,
  resetMswHandlers,
  closeMswServer,
} from './mocks/server';

// Test setup utilities for MSW (Mock Service Worker)
// This file sets up API mocking for Vitest tests

// Establish API mocking before all tests.
beforeAll(() => setupMswServer());

// Reset any request handlers that we may add during the tests,
// so they don't affect other tests.
afterEach(() => resetMswHandlers());

// Clean up after the tests are finished.
afterAll(() => closeMswServer());
