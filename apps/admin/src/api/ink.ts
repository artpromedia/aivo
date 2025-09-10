import { apiRequest } from './base';

export interface InkSession {
  id: string;
  device_id: string;
  user_id?: string;
  session_type: 'handwriting' | 'drawing' | 'annotation';
  started_at: string;
  ended_at?: string;
  duration_ms?: number;
  status: 'active' | 'completed' | 'failed' | 'timeout';
  stroke_count: number;
  total_ink_points: number;
  canvas_dimensions: {
    width: number;
    height: number;
  };
  metadata: {
    app_context?: string;
    page_reference?: string;
    exercise_id?: string;
    pressure_levels?: number[];
    tilt_data?: boolean;
  };
}

export interface InkStroke {
  id: string;
  session_id: string;
  stroke_index: number;
  points: Array<{
    x: number;
    y: number;
    timestamp: number;
    pressure?: number;
    tilt_x?: number;
    tilt_y?: number;
  }>;
  color: string;
  width: number;
  tool_type: 'pen' | 'pencil' | 'marker' | 'eraser';
  created_at: string;
}

export interface InkAnalytics {
  total_sessions: number;
  active_sessions: number;
  avg_session_duration: number;
  total_strokes: number;
  total_ink_points: number;
  device_breakdown: Array<{
    device_id: string;
    session_count: number;
    avg_duration: number;
  }>;
  session_types: Array<{
    type: string;
    count: number;
    percentage: number;
  }>;
  daily_activity: Array<{
    date: string;
    session_count: number;
    stroke_count: number;
  }>;
}

export interface SessionDebugInfo {
  session: InkSession;
  strokes: InkStroke[];
  performance_metrics: {
    latency_ms: number;
    frame_drops: number;
    memory_usage_mb: number;
    cpu_usage_percent: number;
  };
  error_logs: Array<{
    timestamp: string;
    level: 'error' | 'warning' | 'info';
    message: string;
    stack_trace?: string;
  }>;
}

export class InkOpsAPI {
  static async getSessions(params?: {
    page?: number;
    limit?: number;
    device_id?: string;
    status?: string;
    session_type?: string;
    start_date?: string;
    end_date?: string;
  }) {
    const queryParams = new URLSearchParams();
    if (params?.page) queryParams.set('page', params.page.toString());
    if (params?.limit) queryParams.set('limit', params.limit.toString());
    if (params?.device_id) queryParams.set('device_id', params.device_id);
    if (params?.status) queryParams.set('status', params.status);
    if (params?.session_type)
      queryParams.set('session_type', params.session_type);
    if (params?.start_date) queryParams.set('start_date', params.start_date);
    if (params?.end_date) queryParams.set('end_date', params.end_date);

    return apiRequest<{
      sessions: InkSession[];
      total: number;
      page: number;
      totalPages: number;
    }>(`/admin/ink/sessions?${queryParams.toString()}`);
  }

  static async getSession(sessionId: string) {
    return apiRequest<InkSession>(`/admin/ink/sessions/${sessionId}`);
  }

  static async getSessionDebugInfo(sessionId: string) {
    return apiRequest<SessionDebugInfo>(
      `/admin/ink/sessions/${sessionId}/debug`
    );
  }

  static async getSessionStrokes(sessionId: string) {
    return apiRequest<{
      strokes: InkStroke[];
    }>(`/admin/ink/sessions/${sessionId}/strokes`);
  }

  static async terminateSession(sessionId: string, reason?: string) {
    return apiRequest<InkSession>(
      `/admin/ink/sessions/${sessionId}/terminate`,
      {
        method: 'POST',
        body: JSON.stringify({ reason }),
      }
    );
  }

  static async getAnalytics(params?: {
    start_date?: string;
    end_date?: string;
    device_ids?: string[];
  }) {
    const queryParams = new URLSearchParams();
    if (params?.start_date) queryParams.set('start_date', params.start_date);
    if (params?.end_date) queryParams.set('end_date', params.end_date);
    if (params?.device_ids) {
      params.device_ids.forEach(id => queryParams.append('device_ids', id));
    }

    return apiRequest<InkAnalytics>(
      `/admin/ink/analytics?${queryParams.toString()}`
    );
  }

  static async exportSessionData(
    sessionId: string,
    format: 'json' | 'svg' | 'pdf'
  ) {
    return apiRequest<{
      download_url: string;
      expires_at: string;
    }>(`/admin/ink/sessions/${sessionId}/export`, {
      method: 'POST',
      body: JSON.stringify({ format }),
    });
  }

  static async bulkTerminateSessions(sessionIds: string[], reason?: string) {
    return apiRequest<{
      terminated: string[];
      failed: Array<{ session_id: string; error: string }>;
    }>('/admin/ink/sessions/bulk-terminate', {
      method: 'POST',
      body: JSON.stringify({
        session_ids: sessionIds,
        reason,
      }),
    });
  }

  static async getDeviceInkStatus(deviceId: string) {
    return apiRequest<{
      device_id: string;
      ink_enabled: boolean;
      active_sessions: number;
      last_activity: string;
      calibration_status: 'calibrated' | 'needs_calibration' | 'calibrating';
      pressure_sensitivity: number;
      palm_rejection: boolean;
    }>(`/admin/devices/${deviceId}/ink-status`);
  }

  static async recalibrateDevice(deviceId: string) {
    return apiRequest<{
      calibration_id: string;
      status: string;
    }>(`/admin/devices/${deviceId}/recalibrate`, {
      method: 'POST',
    });
  }
}
