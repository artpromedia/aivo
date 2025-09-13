import { useQuery } from '@tanstack/react-query';
import React from 'react';

import { FlagsAPI, type EvaluationContext } from '../api/flags';

// Hook for evaluating a single flag
export function useFeatureFlag(
  flagKey: string,
  context: EvaluationContext,
  defaultValue = false
) {
  return useQuery({
    queryKey: ['feature-flag', flagKey, context],
    queryFn: () =>
      FlagsAPI.evaluateFlag({
        flag_key: flagKey,
        context,
        default_value: defaultValue,
      }),
    staleTime: 30000, // 30 seconds
    refetchInterval: 60000, // Refetch every minute
  });
}

// Hook for evaluating multiple flags at once
export function useFeatureFlags(context: EvaluationContext) {
  return useQuery({
    queryKey: ['feature-flags', context],
    queryFn: () => FlagsAPI.getUserFlags(context.user_id, context),
    staleTime: 30000,
    refetchInterval: 60000,
    enabled: !!context.user_id,
  });
}

// Hook to check if a flag is enabled (returns boolean directly)
export function useFlag(
  flagKey: string,
  context: EvaluationContext,
  defaultValue = false
): boolean {
  const { data } = useFeatureFlag(flagKey, context, defaultValue);
  return data?.value ?? defaultValue;
}

// React component for flag-gated features
export function FeatureGate({
  flagKey,
  context,
  defaultValue = false,
  children,
  fallback = null,
}: {
  flagKey: string;
  context: EvaluationContext;
  defaultValue?: boolean;
  children: React.ReactNode;
  fallback?: React.ReactNode;
}) {
  const isEnabled = useFlag(flagKey, context, defaultValue);

  if (!isEnabled) {
    return fallback as React.ReactElement;
  }

  return children as React.ReactElement;
}

// Higher-order component for flag-gated features
export function withFeatureFlag<P extends object>(
  flagKey: string,
  context: EvaluationContext,
  defaultValue = false
) {
  return function (WrappedComponent: React.ComponentType<P>) {
    return function FeatureFlaggedComponent(props: P) {
      const isEnabled = useFlag(flagKey, context, defaultValue);

      if (!isEnabled) {
        return null;
      }

      return React.createElement(WrappedComponent, props);
    };
  };
}

// Hook for experiment variants
export function useExperimentVariant(
  flagKey: string,
  context: EvaluationContext
): { variant: string | null; isInExperiment: boolean } {
  const { data } = useFeatureFlag(flagKey, context);

  return {
    variant: data?.variant || null,
    isInExperiment: !!data?.experiment_id,
  };
}

// User context helper
export function createUserContext(
  userId: string,
  tenantId?: string,
  userRole?: string,
  userRegion?: string,
  userGradeBand?: string,
  customAttributes?: Record<string, string | number | boolean>
): EvaluationContext {
  return {
    user_id: userId,
    tenant_id: tenantId,
    session_id: `session-${Date.now()}`, // Simple session ID
    user_role: userRole,
    user_region: userRegion,
    user_grade_band: userGradeBand,
    custom_attributes: customAttributes,
  };
}
