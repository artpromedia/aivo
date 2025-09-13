import { apiRequest } from './base';

// Integration Hub Service Types
export interface ConnectorType {
  GOOGLE_CLASSROOM: 'google_classroom';
  CANVAS_LTI: 'canvas_lti';
  ZOOM_LTI: 'zoom_lti';
  CLEVER: 'clever';
  ONEROSTER: 'oneroster';
}

export type ConnectorTypeValue =
  | 'google_classroom'
  | 'canvas_lti'
  | 'zoom_lti'
  | 'clever'
  | 'oneroster';

export type ConnectionStatus =
  | 'disconnected'
  | 'connecting'
  | 'connected'
  | 'error'
  | 'expired';

export type LogLevel = 'debug' | 'info' | 'warning' | 'error';

export interface ConnectorConfig {
  connector_type: ConnectorTypeValue;
  display_name: string;
  description: string;
  is_enabled: boolean;
  oauth_provider?: string;
  oauth_scopes?: string[];
  documentation_url?: string;
  config_schema: Record<string, unknown>;
}

export interface Integration {
  id: string;
  tenant_id: string;
  name: string;
  description?: string;
  connector_type: ConnectorTypeValue;
  status: ConnectionStatus;
  is_active: boolean;
  last_connected_at?: string;
  last_sync_at?: string;
  last_error_at?: string;
  last_error_message?: string;
  oauth_scopes?: string[];
  rate_limit_per_hour?: number;
  requests_today: number;
  created_at: string;
  updated_at: string;
  created_by?: string;
}

export interface ConnectionLog {
  id: string;
  integration_id: string;
  level: LogLevel;
  message: string;
  details?: Record<string, unknown>;
  operation?: string;
  duration_ms?: number;
  error_code?: string;
  error_type?: string;
  created_at: string;
}

export interface IntegrationTest {
  id: string;
  integration_id: string;
  test_type: string;
  test_name: string;
  success: boolean;
  duration_ms?: number;
  message?: string;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
}

export interface IntegrationCreateData {
  name: string;
  description?: string;
  connector_type: ConnectorTypeValue;
  config: Record<string, unknown>;
  oauth_scopes?: string[];
}

export interface IntegrationUpdateData {
  name?: string;
  description?: string;
  config?: Record<string, unknown>;
  is_active?: boolean;
  oauth_scopes?: string[];
}

export interface ConnectRequest {
  config: Record<string, unknown>;
  test_connection?: boolean;
}

export interface ConnectResponse {
  success: boolean;
  integration_id: string;
  status: ConnectionStatus;
  oauth_url?: string;
  message: string;
  test_results?: IntegrationTest[];
}

export interface TestConnectionRequest {
  test_types: string[];
}

export interface TestConnectionResponse {
  success: boolean;
  tests: IntegrationTest[];
  overall_message: string;
}

export interface IntegrationStatusResponse {
  integration: Integration;
  recent_logs: ConnectionLog[];
  recent_tests: IntegrationTest[];
  connection_health: {
    is_healthy: boolean;
    last_check?: string;
    next_sync?: string;
    error_count_24h: number;
  };
}

export interface PaginatedResponse {
  total: number;
  page: number;
  size: number;
}

export interface IntegrationList extends PaginatedResponse {
  integrations: Integration[];
}

export interface ConnectionLogList extends PaginatedResponse {
  logs: ConnectionLog[];
}

export interface IntegrationTestList extends PaginatedResponse {
  tests: IntegrationTest[];
}

// Integration Hub API
export class IntegrationHubAPI {
  private tenantId = 'default-tenant'; // TODO: Get from auth context

  // Connector Types
  async getConnectorTypes(): Promise<ConnectorConfig[]> {
    return apiRequest<ConnectorConfig[]>('/api/v1/connectors');
  }

  // Integrations CRUD
  async getIntegrations(params?: {
    page?: number;
    size?: number;
    connector_type?: ConnectorTypeValue;
    status?: ConnectionStatus;
  }): Promise<IntegrationList> {
    const queryParams = new URLSearchParams();
    if (params?.page) queryParams.set('page', params.page.toString());
    if (params?.size) queryParams.set('size', params.size.toString());
    if (params?.connector_type)
      queryParams.set('connector_type', params.connector_type);
    if (params?.status) queryParams.set('status', params.status);

    const url = `/api/v1/tenants/${this.tenantId}/integrations${queryParams.toString() ? `?${queryParams}` : ''}`;
    return apiRequest<IntegrationList>(url);
  }

  async getIntegration(integrationId: string): Promise<Integration> {
    return apiRequest<Integration>(
      `/api/v1/tenants/${this.tenantId}/integrations/${integrationId}`
    );
  }

  async createIntegration(data: IntegrationCreateData): Promise<Integration> {
    return apiRequest<Integration>(
      `/api/v1/tenants/${this.tenantId}/integrations`,
      {
        method: 'POST',
        body: JSON.stringify(data),
      }
    );
  }

  async updateIntegration(
    integrationId: string,
    data: IntegrationUpdateData
  ): Promise<Integration> {
    return apiRequest<Integration>(
      `/api/v1/tenants/${this.tenantId}/integrations/${integrationId}`,
      {
        method: 'PUT',
        body: JSON.stringify(data),
      }
    );
  }

  async deleteIntegration(integrationId: string): Promise<{ message: string }> {
    return apiRequest(
      `/api/v1/tenants/${this.tenantId}/integrations/${integrationId}`,
      {
        method: 'DELETE',
      }
    );
  }

  // Connection Management
  async connectIntegration(
    integrationId: string,
    data: ConnectRequest
  ): Promise<ConnectResponse> {
    return apiRequest<ConnectResponse>(
      `/api/v1/tenants/${this.tenantId}/integrations/${integrationId}/connect`,
      {
        method: 'POST',
        body: JSON.stringify(data),
      }
    );
  }

  async testConnection(
    integrationId: string,
    data: TestConnectionRequest
  ): Promise<TestConnectionResponse> {
    return apiRequest<TestConnectionResponse>(
      `/api/v1/tenants/${this.tenantId}/integrations/${integrationId}/test`,
      {
        method: 'POST',
        body: JSON.stringify(data),
      }
    );
  }

  async getIntegrationStatus(
    integrationId: string
  ): Promise<IntegrationStatusResponse> {
    return apiRequest<IntegrationStatusResponse>(
      `/api/v1/tenants/${this.tenantId}/integrations/${integrationId}/status`
    );
  }

  // Logs and Tests
  async getIntegrationLogs(
    integrationId: string,
    params?: {
      page?: number;
      size?: number;
      level?: LogLevel;
      operation?: string;
    }
  ): Promise<ConnectionLogList> {
    const queryParams = new URLSearchParams();
    if (params?.page) queryParams.set('page', params.page.toString());
    if (params?.size) queryParams.set('size', params.size.toString());
    if (params?.level) queryParams.set('level', params.level);
    if (params?.operation) queryParams.set('operation', params.operation);

    const url = `/api/v1/tenants/${this.tenantId}/integrations/${integrationId}/logs${queryParams.toString() ? `?${queryParams}` : ''}`;
    return apiRequest<ConnectionLogList>(url);
  }

  async getIntegrationTests(
    integrationId: string,
    params?: {
      page?: number;
      size?: number;
      test_type?: string;
    }
  ): Promise<IntegrationTestList> {
    const queryParams = new URLSearchParams();
    if (params?.page) queryParams.set('page', params.page.toString());
    if (params?.size) queryParams.set('size', params.size.toString());
    if (params?.test_type) queryParams.set('test_type', params.test_type);

    const url = `/api/v1/tenants/${this.tenantId}/integrations/${integrationId}/tests${queryParams.toString() ? `?${queryParams}` : ''}`;
    return apiRequest<IntegrationTestList>(url);
  }
}

// Export singleton instance
export const integrationHubAPI = new IntegrationHubAPI();
