// Auto-generated SDK exports
// Generated on: 2025-09-01T12:20:17.051Z

// Export shared runtime and common types from auth service
export * from './services/auth/src/runtime';

// Export models from each service with namespacing to avoid conflicts
export * as AuthModels from './services/auth/src/models/index';
export * as TenantModels from './services/tenant/src/models/index';
export * as EnrollmentModels from './services/enrollment/src/models/index';
export * as PaymentModels from './services/payments/src/models/index';
export * as LearnerModels from './services/learner/src/models/index';
export * as OrchestratorModels from './services/orchestrator/src/models/index';
export * as AdminPortalModels from './services/admin-portal/src/models/index';

// Export specific API classes
export { AuthenticationApi, ProfileApi } from './services/auth/src/apis/index';
export { TenantSettingsApi, TenantsApi } from './services/tenant/src/apis/index';
export { BulkOperationsApi, EnrollmentsApi, ProgressApi } from './services/enrollment/src/apis/index';
export { CouponsApi, InvoicesApi, PaymentMethodsApi, SubscriptionsApi } from './services/payments/src/apis/index';
export { 
  AchievementsApi, 
  AnalyticsApi as LearnerAnalyticsApi, 
  BulkOperationsApi as LearnerBulkOperationsApi, 
  LearnerProfileApi, 
  LearnersApi 
} from './services/learner/src/apis/index';
export { AssessmentsApi, CoursesApi, LearningPathsApi, ModulesApi } from './services/orchestrator/src/apis/index';
export { 
  AnalyticsApi as AdminAnalyticsApi, 
  BillingApi, 
  DashboardApi, 
  NamespacesApi, 
  SubscriptionApi, 
  TeamApi 
} from './services/admin-portal/src/apis/index';

// Re-export common types
export interface ApiConfig {
  basePath?: string;
  accessToken?: string;
  apiKey?: string;
  credentials?: 'include' | 'same-origin' | 'omit';
}

// Export MSW handlers for testing/mocking
export { handlers as mswHandlers } from './msw/handlers';
export { server as mswServer } from './msw/setup';

// SDK Version
export const SDK_VERSION = '1.0.0';
