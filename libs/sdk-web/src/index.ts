// Auto-generated SDK exports
// Generated on: 2025-09-01T12:20:17.051Z

export * from './services/auth/src';
export * from './services/tenant/src';
export * from './services/enrollment/src';
export * from './services/payments/src';
export * from './services/learner/src';
export * from './services/orchestrator/src';
export * from './services/admin-portal/src';

// Re-export common types
export interface ApiConfig {
  basePath?: string;
  accessToken?: string;
  apiKey?: string;
  credentials?: 'include' | 'same-origin' | 'omit';
}

// SDK Version
export const SDK_VERSION = '1.0.0';
