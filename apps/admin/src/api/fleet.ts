import { apiRequest } from './base';

export interface DeviceFilter {
  device_ids?: string[];
  tenant_id?: string;
  device_type?: string;
  firmware_version?: string;
  status?: string;
  tags?: string[];
}

export interface ActionConfig {
  slack_channel?: string;
  email_recipients?: string[];
  webhook_url?: string;
  notification_template?: string;
  escalation_delay_minutes?: number;
}

export interface ActionParameters {
  wipe_type?: 'factory' | 'enterprise';
  reboot_force?: boolean;
  lock_message?: string;
  custom_params?: Record<string, string | number | boolean>;
}

export interface DeviceResponse {
  status_code?: number;
  message?: string;
  error_details?: string;
  timestamp?: string;
  device_info?: Record<string, string | number>;
}

export interface ActionResult {
  success: boolean;
  message?: string;
  error_code?: string;
  details?: Record<string, string | number>;
}

export interface Alert {
  id: string;
  message: string;
  severity: 'critical' | 'warning' | 'info';
  timestamp: string;
  device_id?: string;
  rule_id?: string;
}

export interface FleetHealth {
  summary: {
    total_devices: number;
    online_percentage: number;
    mean_heartbeat_minutes: number;
    firmware_versions: number;
    last_updated: string;
    range_days: number;
  };
  status_distribution: Record<string, number>;
  firmware_drift: Array<{
    version: string;
    device_count: number;
    percentage: number;
    is_latest: boolean;
  }>;
  health_trends: Array<{
    date: string;
    online_percentage: number;
    total_devices: number;
    new_enrollments: number;
  }>;
  alerts: {
    critical: Alert[];
    warnings: Alert[];
  };
}

export interface AlertRule {
  rule_id: string;
  name: string;
  description?: string;
  metric: string;
  condition: string;
  threshold: string;
  window_minutes: number;
  tenant_id?: string;
  device_filter?: DeviceFilter;
  actions: string[];
  action_config?: ActionConfig;
  is_enabled: boolean;
  trigger_count: number;
  last_triggered_at?: string;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface AlertRuleRequest {
  name: string;
  description?: string;
  metric: string;
  condition: string;
  threshold: string;
  window_minutes?: number;
  tenant_id?: string;
  device_filter?: DeviceFilter;
  actions: string[];
  action_config?: ActionConfig;
  is_enabled?: boolean;
}

export interface AlertMetrics {
  metrics: Array<{
    key: string;
    name: string;
    description: string;
    unit: string;
  }>;
  conditions: Array<{
    key: string;
    name: string;
    description: string;
  }>;
  actions: Array<{
    key: string;
    name: string;
    description: string;
  }>;
}

export interface RemoteActionRequest {
  reason?: string;
  parameters?: ActionParameters;
  priority?: number;
  initiated_by: string;
  correlation_id?: string;
  client_ip?: string;
}

export interface RemoteAction {
  action_id: string;
  device_id: string;
  action_type: string;
  status: string;
  reason?: string;
  parameters?: ActionParameters;
  priority: number;
  initiated_by: string;
  created_at: string;
  sent_at?: string;
  acknowledged_at?: string;
  completed_at?: string;
  expires_at: string;
  error_message?: string;
  attempts: number;
  max_attempts: number;
}

export class FleetAPI {
  static async getFleetHealth(params?: {
    tenantId?: string;
    rangeDays?: number;
  }): Promise<FleetHealth> {
    const queryParams = new URLSearchParams();
    if (params?.tenantId) queryParams.set('tenant_id', params.tenantId);
    if (params?.rangeDays)
      queryParams.set('range_days', params.rangeDays.toString());

    return apiRequest<FleetHealth>(`/fleet/health?${queryParams.toString()}`);
  }

  static async getAlertRules(params?: {
    tenantId?: string;
    isEnabled?: boolean;
  }): Promise<{ rules: AlertRule[]; total: number }> {
    const queryParams = new URLSearchParams();
    if (params?.tenantId) queryParams.set('tenant_id', params.tenantId);
    if (params?.isEnabled !== undefined)
      queryParams.set('is_enabled', params.isEnabled.toString());

    return apiRequest<{ rules: AlertRule[]; total: number }>(
      `/alerts/rules?${queryParams.toString()}`
    );
  }

  static async createAlertRule(rule: AlertRuleRequest): Promise<AlertRule> {
    return apiRequest<AlertRule>('/alerts/rules', {
      method: 'POST',
      body: JSON.stringify({
        ...rule,
        created_by: 'current-user-id', // This would come from auth context
      }),
    });
  }

  static async getAlertRule(ruleId: string): Promise<AlertRule> {
    return apiRequest<AlertRule>(`/alerts/rules/${ruleId}`);
  }

  static async updateAlertRule(
    ruleId: string,
    rule: AlertRuleRequest
  ): Promise<AlertRule> {
    return apiRequest<AlertRule>(`/alerts/rules/${ruleId}`, {
      method: 'PUT',
      body: JSON.stringify(rule),
    });
  }

  static async deleteAlertRule(ruleId: string): Promise<void> {
    return apiRequest<void>(`/alerts/rules/${ruleId}`, {
      method: 'DELETE',
    });
  }

  static async toggleAlertRule(
    ruleId: string,
    enabled: boolean
  ): Promise<AlertRule> {
    return apiRequest<AlertRule>(`/alerts/rules/${ruleId}/toggle`, {
      method: 'POST',
      body: JSON.stringify({ enabled }),
    });
  }

  static async getAlertMetrics(): Promise<AlertMetrics> {
    return apiRequest<AlertMetrics>('/alerts/metrics');
  }

  // Remote Device Actions

  static async executeDeviceAction(
    deviceId: string,
    actionType: string,
    request: RemoteActionRequest
  ): Promise<RemoteAction> {
    return apiRequest<RemoteAction>(
      `/devices/${deviceId}/actions/${actionType}`,
      {
        method: 'POST',
        body: JSON.stringify({
          ...request,
          initiated_by: request.initiated_by || 'current-user-id', // This would come from auth context
        }),
      }
    );
  }

  static async getDeviceActions(
    deviceId: string,
    params?: {
      statusFilter?: string;
      limit?: number;
    }
  ): Promise<{ actions: RemoteAction[]; total: number; device_id: string }> {
    const queryParams = new URLSearchParams();
    if (params?.statusFilter)
      queryParams.set('status_filter', params.statusFilter);
    if (params?.limit) queryParams.set('limit', params.limit.toString());

    return apiRequest<{
      actions: RemoteAction[];
      total: number;
      device_id: string;
    }>(`/devices/${deviceId}/actions?${queryParams.toString()}`);
  }

  static async getActionDetails(actionId: string): Promise<RemoteAction> {
    return apiRequest<RemoteAction>(`/actions/${actionId}`);
  }

  static async acknowledgeAction(
    actionId: string
  ): Promise<{ message: string; action_id: string }> {
    return apiRequest<{ message: string; action_id: string }>(
      `/actions/${actionId}/acknowledge`,
      {
        method: 'POST',
      }
    );
  }

  static async completeAction(
    actionId: string,
    resultData?: ActionResult,
    deviceResponse?: DeviceResponse
  ): Promise<{ message: string; action_id: string }> {
    return apiRequest<{ message: string; action_id: string }>(
      `/actions/${actionId}/complete`,
      {
        method: 'POST',
        body: JSON.stringify({
          result_data: resultData,
          device_response: deviceResponse,
        }),
      }
    );
  }

  static async failAction(
    actionId: string,
    errorMessage: string,
    deviceResponse?: DeviceResponse
  ): Promise<{ message: string; action_id: string }> {
    return apiRequest<{ message: string; action_id: string }>(
      `/actions/${actionId}/fail`,
      {
        method: 'POST',
        body: JSON.stringify({
          error_message: errorMessage,
          device_response: deviceResponse,
        }),
      }
    );
  }

  static async getActionStatistics(days = 7): Promise<{
    period_days: number;
    status_distribution: Record<string, number>;
    action_type_distribution: Record<string, number>;
    total_actions: number;
  }> {
    return apiRequest<{
      period_days: number;
      status_distribution: Record<string, number>;
      action_type_distribution: Record<string, number>;
      total_actions: number;
    }>(`/actions/stats?days=${days}`);
  }

  static async cleanupExpiredActions(): Promise<{
    message: string;
    expired_count: number;
  }> {
    return apiRequest<{ message: string; expired_count: number }>(
      '/actions/cleanup',
      {
        method: 'POST',
      }
    );
  }
}
