// Auto-generated SDK exports
// Generated on: 2025-09-01T12:20:17.051Z

export * from './services/auth';
export * from './services/tenant';
export * from './services/enrollment';
export * from './services/payments';
export * from './services/learner';
export * from './services/orchestrator';
export * from './services/admin-portal';

// Re-export common types
export interface ApiConfig {
  basePath?: string;
  accessToken?: string;
  apiKey?: string;
  credentials?: 'include' | 'same-origin' | 'omit';
}

// SDK Version
export const SDK_VERSION = '1.0.0';
