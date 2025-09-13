import { apiRequest } from './base';

// Additional type definitions for better type safety
export interface VisualizationConfig {
  chart_type?: 'table' | 'bar' | 'line' | 'pie';
  show_totals?: boolean;
  color_scheme?: string;
  [key: string]: unknown;
}

export interface FilterConfig {
  [key: string]: unknown;
}

export interface S3Config {
  bucket?: string;
  key_prefix?: string;
  region?: string;
  [key: string]: unknown;
}

export interface EmailConfig {
  subject?: string;
  body?: string;
  template?: string;
  [key: string]: unknown;
}

export interface JoinConfig {
  table: string;
  type: 'inner' | 'left' | 'right' | 'full';
  on: string;
  [key: string]: unknown;
}

export interface Report {
  id: string;
  name: string;
  description?: string;
  tenant_id: string;
  created_by: string;
  query_config: QueryConfig;
  visualization_config?: VisualizationConfig;
  filters?: FilterConfig;
  row_limit: number;
  is_public: boolean;
  tags?: string[];
  created_at: string;
  updated_at: string;
}

export interface QueryConfig {
  table: string;
  fields: string[];
  joins?: JoinConfig[];
  filters?: QueryFilter[];
  group_by?: string[];
  sort?: QuerySort[];
  limit?: number;
}

export interface QueryFilter {
  field: string;
  operator:
    | 'eq'
    | 'ne'
    | 'gt'
    | 'gte'
    | 'lt'
    | 'lte'
    | 'in'
    | 'not_in'
    | 'like'
    | 'between';
  value: string | number | boolean | string[] | number[] | null;
}

export interface QuerySort {
  field: string;
  direction: 'asc' | 'desc';
}

export interface Schedule {
  id: string;
  report_id: string;
  name: string;
  description?: string;
  cron_expression: string;
  timezone: string;
  format: 'csv' | 'pdf' | 'xlsx';
  delivery_method: 'email' | 's3' | 'both';
  recipients?: string[];
  s3_config?: S3Config;
  email_config?: EmailConfig;
  is_active: boolean;
  last_run_at?: string;
  next_run_at?: string;
  run_count: number;
  created_at: string;
}

export interface Export {
  id: string;
  report_id: string;
  schedule_id?: string;
  tenant_id: string;
  initiated_by: string;
  format: 'csv' | 'pdf' | 'xlsx';
  status: 'pending' | 'processing' | 'completed' | 'failed';
  file_path?: string;
  file_size?: number;
  row_count?: number;
  error_message?: string;
  download_url?: string;
  expires_at?: string;
  execution_time_ms?: number;
  created_at: string;
  completed_at?: string;
}

export interface CreateReportRequest {
  name: string;
  description?: string;
  query_config: QueryConfig;
  row_limit?: number;
  is_public?: boolean;
  tags?: string[];
}

export interface CreateScheduleRequest {
  report_id: string;
  name: string;
  description?: string;
  cron_expression: string;
  timezone?: string;
  format: 'csv' | 'pdf' | 'xlsx';
  delivery_method: 'email' | 's3' | 'both';
  recipients?: string[];
  s3_config?: S3Config;
  email_config?: EmailConfig;
  is_active?: boolean;
}

export interface CreateExportRequest {
  report_id: string;
  format: 'csv' | 'pdf' | 'xlsx';
}

export class ReportsAPI {
  private static baseURL = '/api/reports';

  // Reports
  static async listReports(params?: {
    page?: number;
    limit?: number;
    search?: string;
    tags?: string[];
  }): Promise<{ reports: Report[]; total: number }> {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set('page', params.page.toString());
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    if (params?.search) searchParams.set('search', params.search);
    if (params?.tags?.length) searchParams.set('tags', params.tags.join(','));

    const url = `${this.baseURL}${searchParams.toString() ? '?' + searchParams : ''}`;
    return apiRequest<{ reports: Report[]; total: number }>(url);
  }

  static async getReport(id: string): Promise<Report> {
    return apiRequest<Report>(`${this.baseURL}/${id}`);
  }

  static async createReport(data: CreateReportRequest): Promise<Report> {
    return apiRequest<Report>(this.baseURL, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  static async updateReport(
    id: string,
    data: Partial<CreateReportRequest>
  ): Promise<Report> {
    return apiRequest<Report>(`${this.baseURL}/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  static async deleteReport(id: string): Promise<void> {
    await apiRequest<void>(`${this.baseURL}/${id}`, {
      method: 'DELETE',
    });
  }

  static async previewReport(
    id: string,
    params?: {
      limit?: number;
      offset?: number;
    }
  ): Promise<{
    data: Record<string, unknown>[];
    columns: string[];
    total: number;
  }> {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    if (params?.offset) searchParams.set('offset', params.offset.toString());

    const url = `${this.baseURL}/${id}/preview${searchParams.toString() ? '?' + searchParams : ''}`;
    return apiRequest<{
      data: Record<string, unknown>[];
      columns: string[];
      total: number;
    }>(url);
  }

  // Schedules
  static async listSchedules(params?: {
    report_id?: string;
    page?: number;
    limit?: number;
  }): Promise<{ schedules: Schedule[]; total: number }> {
    const searchParams = new URLSearchParams();
    if (params?.report_id) searchParams.set('report_id', params.report_id);
    if (params?.page) searchParams.set('page', params.page.toString());
    if (params?.limit) searchParams.set('limit', params.limit.toString());

    const url = `${this.baseURL}/schedules${searchParams.toString() ? '?' + searchParams : ''}`;
    return apiRequest<{ schedules: Schedule[]; total: number }>(url);
  }

  static async getSchedule(id: string): Promise<Schedule> {
    return apiRequest<Schedule>(`${this.baseURL}/schedules/${id}`);
  }

  static async createSchedule(data: CreateScheduleRequest): Promise<Schedule> {
    return apiRequest<Schedule>(`${this.baseURL}/schedules`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  static async updateSchedule(
    id: string,
    data: Partial<CreateScheduleRequest>
  ): Promise<Schedule> {
    return apiRequest<Schedule>(`${this.baseURL}/schedules/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  static async deleteSchedule(id: string): Promise<void> {
    await apiRequest<void>(`${this.baseURL}/schedules/${id}`, {
      method: 'DELETE',
    });
  }

  static async toggleSchedule(
    id: string,
    is_active: boolean
  ): Promise<Schedule> {
    return apiRequest<Schedule>(`${this.baseURL}/schedules/${id}/toggle`, {
      method: 'PATCH',
      body: JSON.stringify({ is_active }),
    });
  }

  static async runSchedule(id: string): Promise<{ job_id: string }> {
    return apiRequest<{ job_id: string }>(
      `${this.baseURL}/schedules/${id}/run`,
      {
        method: 'POST',
      }
    );
  }

  // Exports
  static async listExports(params?: {
    report_id?: string;
    status?: string;
    page?: number;
    limit?: number;
  }): Promise<{ exports: Export[]; total: number }> {
    const searchParams = new URLSearchParams();
    if (params?.report_id) searchParams.set('report_id', params.report_id);
    if (params?.status) searchParams.set('status', params.status);
    if (params?.page) searchParams.set('page', params.page.toString());
    if (params?.limit) searchParams.set('limit', params.limit.toString());

    const url = `${this.baseURL}/exports${searchParams.toString() ? '?' + searchParams : ''}`;
    return apiRequest<{ exports: Export[]; total: number }>(url);
  }

  static async getExport(id: string): Promise<Export> {
    return apiRequest<Export>(`${this.baseURL}/exports/${id}`);
  }

  static async createExport(data: CreateExportRequest): Promise<Export> {
    return apiRequest<Export>(`${this.baseURL}/exports`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  static async downloadExport(id: string): Promise<Blob> {
    const response = await fetch(`${this.baseURL}/exports/${id}/download`, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('admin_token')}`,
      },
    });

    if (!response.ok) {
      throw new Error(`Download failed: ${response.statusText}`);
    }

    return response.blob();
  }

  static async retryExport(id: string): Promise<Export> {
    return apiRequest<Export>(`${this.baseURL}/exports/${id}/retry`, {
      method: 'POST',
    });
  }

  static async deleteExport(id: string): Promise<void> {
    await apiRequest<void>(`${this.baseURL}/exports/${id}`, {
      method: 'DELETE',
    });
  }

  // Utility methods
  static async validateQuery(
    query_config: QueryConfig
  ): Promise<{ valid: boolean; error?: string; estimated_rows?: number }> {
    return apiRequest<{
      valid: boolean;
      error?: string;
      estimated_rows?: number;
    }>(`${this.baseURL}/validate-query`, {
      method: 'POST',
      body: JSON.stringify({ query_config }),
    });
  }

  static async getAvailableTables(): Promise<{
    tables: { name: string; fields: string[] }[];
  }> {
    return apiRequest<{ tables: { name: string; fields: string[] }[] }>(
      `${this.baseURL}/tables`
    );
  }
}
