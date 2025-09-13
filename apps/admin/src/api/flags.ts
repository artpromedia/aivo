// API client for feature flags service
const FLAGS_API_BASE = 'http://localhost:8007/api/v1';

export interface TargetingRules {
  roles?: string[];
  regions?: string[];
  grade_bands?: string[];
  include_users?: string[];
  exclude_users?: string[];
}

export interface FeatureFlag {
  id: number;
  key: string;
  name: string;
  description?: string;
  enabled: boolean;
  rollout_percentage: number;
  targeting_rules: TargetingRules;
  tenant_id?: string;
  is_experiment: boolean;
  experiment_id?: string;
  created_at: string;
  updated_at: string;
  created_by?: string;
}

export interface FeatureFlagCreate {
  key: string;
  name: string;
  description?: string;
  enabled: boolean;
  rollout_percentage: number;
  targeting_rules?: TargetingRules;
  tenant_id?: string | null;
  is_experiment: boolean;
  experiment_id?: string | null;
}

export interface FeatureFlagUpdate {
  name?: string;
  description?: string;
  enabled?: boolean;
  rollout_percentage?: number;
  targeting_rules?: TargetingRules;
  is_experiment?: boolean;
  experiment_id?: string;
}

export interface ExperimentVariant {
  name: string;
  weight: number;
  description?: string;
}

export interface Experiment {
  id: number;
  experiment_id: string;
  flag_id: number;
  name: string;
  description?: string;
  hypothesis?: string;
  variants: ExperimentVariant[];
  success_metrics: string[];
  status: string;
  start_date?: string;
  end_date?: string;
  results: Record<string, string | number | boolean>;
  statistical_significance?: number;
  created_at: string;
  updated_at: string;
  created_by?: string;
}

export interface ExperimentCreate {
  experiment_id: string;
  flag_id: number;
  name: string;
  description?: string;
  hypothesis?: string;
  variants: ExperimentVariant[];
  success_metrics: string[];
  start_date?: string;
  end_date?: string;
}

export interface EvaluationContext {
  user_id: string;
  tenant_id?: string;
  session_id?: string;
  user_role?: string;
  user_region?: string;
  user_grade_band?: string;
  custom_attributes?: Record<string, string | number | boolean>;
}

export interface EvaluationResponse {
  flag_key: string;
  value: boolean;
  variant?: string;
  experiment_id?: string;
  reason: string;
}

export interface FlagAnalytics {
  flag_id: number;
  flag_key: string;
  total_exposures: number;
  unique_users: number;
  exposure_rate: number;
  conversion_rate?: number;
  period_start: string;
  period_end: string;
}

export interface ExperimentAnalytics {
  experiment_id: string;
  variants: Record<string, Record<string, string | number | boolean>>;
  statistical_significance?: number;
  confidence_interval?: Record<string, number>;
  sample_size: number;
  period_start: string;
  period_end: string;
}

export class FlagsAPI {
  static async listFlags(params?: {
    tenant_id?: string;
    enabled?: boolean;
    is_experiment?: boolean;
    limit?: number;
    offset?: number;
  }): Promise<FeatureFlag[]> {
    const searchParams = new URLSearchParams();
    if (params?.tenant_id) searchParams.append('tenant_id', params.tenant_id);
    if (params?.enabled !== undefined)
      searchParams.append('enabled', params.enabled.toString());
    if (params?.is_experiment !== undefined)
      searchParams.append('is_experiment', params.is_experiment.toString());
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    if (params?.offset) searchParams.append('offset', params.offset.toString());

    const response = await fetch(`${FLAGS_API_BASE}/flags?${searchParams}`);
    if (!response.ok) throw new Error('Failed to fetch flags');
    return response.json();
  }

  static async getFlag(key: string): Promise<FeatureFlag> {
    const response = await fetch(`${FLAGS_API_BASE}/flags/${key}`);
    if (!response.ok) throw new Error('Failed to fetch flag');
    return response.json();
  }

  static async createFlag(data: FeatureFlagCreate): Promise<FeatureFlag> {
    const response = await fetch(`${FLAGS_API_BASE}/flags`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to create flag');
    return response.json();
  }

  static async updateFlag(
    key: string,
    data: FeatureFlagUpdate
  ): Promise<FeatureFlag> {
    const response = await fetch(`${FLAGS_API_BASE}/flags/${key}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to update flag');
    return response.json();
  }

  static async deleteFlag(key: string): Promise<{ message: string }> {
    const response = await fetch(`${FLAGS_API_BASE}/flags/${key}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete flag');
    return response.json();
  }

  static async toggleFlag(
    key: string
  ): Promise<{ flag_key: string; enabled: boolean }> {
    const response = await fetch(`${FLAGS_API_BASE}/flags/${key}/toggle`, {
      method: 'POST',
    });
    if (!response.ok) throw new Error('Failed to toggle flag');
    return response.json();
  }

  static async evaluateFlag(data: {
    flag_key: string;
    context: EvaluationContext;
    default_value?: boolean;
  }): Promise<EvaluationResponse> {
    const response = await fetch(`${FLAGS_API_BASE}/evaluate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to evaluate flag');
    return response.json();
  }

  static async getUserFlags(
    userId: string,
    context?: Partial<EvaluationContext>
  ): Promise<{
    flags: Record<
      string,
      { value: boolean; variant?: string; experiment_id?: string }
    >;
    user_id: string;
    tenant_id?: string;
  }> {
    const searchParams = new URLSearchParams({ user_id: userId });
    if (context?.tenant_id) searchParams.append('tenant_id', context.tenant_id);
    if (context?.user_role) searchParams.append('user_role', context.user_role);
    if (context?.user_region)
      searchParams.append('user_region', context.user_region);
    if (context?.user_grade_band)
      searchParams.append('user_grade_band', context.user_grade_band);

    const response = await fetch(
      `${FLAGS_API_BASE}/flags/${userId}?${searchParams}`
    );
    if (!response.ok) throw new Error('Failed to fetch user flags');
    return response.json();
  }

  // Experiment methods
  static async listExperiments(flagKey: string): Promise<Experiment[]> {
    const response = await fetch(
      `${FLAGS_API_BASE}/flags/${flagKey}/experiments`
    );
    if (!response.ok) throw new Error('Failed to fetch experiments');
    return response.json();
  }

  static async createExperiment(
    flagKey: string,
    data: ExperimentCreate
  ): Promise<Experiment> {
    const response = await fetch(
      `${FLAGS_API_BASE}/flags/${flagKey}/experiments`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      }
    );
    if (!response.ok) throw new Error('Failed to create experiment');
    return response.json();
  }

  // Analytics methods
  static async getFlagAnalytics(
    flagKey: string,
    periodDays = 7
  ): Promise<FlagAnalytics> {
    const response = await fetch(
      `${FLAGS_API_BASE}/exposures/analytics/${flagKey}?period_days=${periodDays}`
    );
    if (!response.ok) throw new Error('Failed to fetch flag analytics');
    return response.json();
  }

  static async getExperimentAnalytics(
    experimentId: string,
    periodDays = 30
  ): Promise<ExperimentAnalytics> {
    const response = await fetch(
      `${FLAGS_API_BASE}/exposures/experiments/${experimentId}/analytics?period_days=${periodDays}`
    );
    if (!response.ok) throw new Error('Failed to fetch experiment analytics');
    return response.json();
  }
}
