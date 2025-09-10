import { http, HttpResponse } from 'msw';

/**
 * Ink Operations MSW Handlers
 */

const mockInkSessions = [
  {
    id: 'session_001',
    device_id: 'device_001',
    session_type: 'handwriting',
    status: 'active',
    duration_ms: 45000,
    stroke_count: 156,
    total_ink_points: 2847,
    started_at: '2024-09-09T08:30:00Z',
    canvas_dimensions: { width: 1024, height: 768 },
  },
  {
    id: 'session_002',
    device_id: 'device_002',
    session_type: 'drawing',
    status: 'completed',
    duration_ms: 180000,
    stroke_count: 89,
    total_ink_points: 1923,
    started_at: '2024-09-09T07:15:00Z',
    canvas_dimensions: { width: 800, height: 600 },
  },
] as Array<{
  id: string;
  device_id: string;
  session_type: string;
  status: string;
  duration_ms: number;
  stroke_count: number;
  total_ink_points: number;
  started_at: string;
  canvas_dimensions: { width: number; height: number };
}>;

const mockAnalytics = {
  total_sessions: 245,
  active_sessions: 12,
  avg_session_duration: 92000,
  total_strokes: 15743,
};

export const inkHandlers = [
  // Get sessions
  http.get('http://localhost:8000/admin/ink/sessions', ({ request }) => {
    const url = new URL(request.url);
    const page = parseInt(url.searchParams.get('page') || '1');
    const limit = parseInt(url.searchParams.get('limit') || '20');
    const status = url.searchParams.get('status');
    const deviceId = url.searchParams.get('device_id');

    let filteredSessions = [...mockInkSessions];

    if (status) {
      filteredSessions = filteredSessions.filter(s => s.status === status);
    }

    if (deviceId) {
      filteredSessions = filteredSessions.filter(s => s.device_id === deviceId);
    }

    const startIndex = (page - 1) * limit;
    const endIndex = startIndex + limit;
    const paginatedSessions = filteredSessions.slice(startIndex, endIndex);

    return HttpResponse.json({
      sessions: paginatedSessions,
      total: filteredSessions.length,
      page,
      limit,
      pages: Math.ceil(filteredSessions.length / limit),
    });
  }),

  // Get analytics
  http.get('http://localhost:8000/admin/ink/analytics', () => {
    return HttpResponse.json(mockAnalytics);
  }),

  // Get session debug info
  http.get(
    'http://localhost:8000/admin/ink/sessions/:sessionId/debug',
    ({ params }) => {
      return HttpResponse.json({
        session_id: params.sessionId,
        debug_info: {
          latency_ms: 45,
          memory_usage_mb: 23.5,
          error_count: 0,
          last_error: null,
        },
        events: [
          {
            timestamp: '2024-09-09T08:30:05Z',
            event_type: 'stroke_start',
            details: { x: 100, y: 150 },
          },
          {
            timestamp: '2024-09-09T08:30:08Z',
            event_type: 'stroke_end',
            details: { stroke_length: 156 },
          },
        ],
      });
    }
  ),

  // Terminate session
  http.post(
    'http://localhost:8000/admin/ink/sessions/:sessionId/terminate',
    ({ params }) => {
      const session = mockInkSessions.find(s => s.id === params.sessionId);
      if (session) {
        session.status = 'terminated';
      }
      return HttpResponse.json({ success: true });
    }
  ),

  // Bulk terminate sessions
  http.post(
    'http://localhost:8000/admin/ink/sessions/bulk-terminate',
    async ({ request }) => {
      const body = (await request.json()) as {
        session_ids: string[];
        reason?: string;
      };

      body.session_ids.forEach(sessionId => {
        const session = mockInkSessions.find(s => s.id === sessionId);
        if (session) {
          session.status = 'terminated';
        }
      });

      return HttpResponse.json({
        success: true,
        terminated_count: body.session_ids.length,
      });
    }
  ),

  // Export session data
  http.post(
    'http://localhost:8000/admin/ink/sessions/:sessionId/export',
    async ({ params, request }) => {
      const body = (await request.json()) as { format: string };

      return HttpResponse.json({
        download_url: `http://localhost:8000/exports/${params.sessionId}.${body.format}`,
        expires_at: new Date(Date.now() + 3600000).toISOString(), // 1 hour
      });
    }
  ),
];
