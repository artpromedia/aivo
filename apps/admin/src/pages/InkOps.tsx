import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Search,
  Filter,
  RefreshCw,
  Play,
  Square,
  Eye,
  AlertTriangle,
  CheckCircle,
  Clock,
  Pen,
  BarChart3,
} from 'lucide-react';
import { useState } from 'react';

import { DeviceAPI } from '@/api/device';
import { InkOpsAPI, type InkSession } from '@/api/ink';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

interface SessionFilters {
  device_id: string;
  status: string;
  session_type: string;
  start_date: string;
  end_date: string;
}

export function InkOps() {
  const [currentPage, setCurrentPage] = useState(1);
  const [filters, setFilters] = useState<SessionFilters>({
    device_id: '',
    status: '',
    session_type: '',
    start_date: '',
    end_date: '',
  });
  const [selectedSession, setSelectedSession] = useState<InkSession | null>(
    null
  );
  const [showDebugInfo, setShowDebugInfo] = useState(false);
  const [showAnalytics, setShowAnalytics] = useState(false);
  const [selectedSessions, setSelectedSessions] = useState<string[]>([]);

  const queryClient = useQueryClient();

  const { data: sessionsData, isLoading } = useQuery({
    queryKey: ['ink-sessions', currentPage, filters],
    queryFn: () =>
      InkOpsAPI.getSessions({
        page: currentPage,
        limit: 20,
        device_id: filters.device_id || undefined,
        status: filters.status || undefined,
        session_type: filters.session_type || undefined,
        start_date: filters.start_date || undefined,
        end_date: filters.end_date || undefined,
      }),
  });

  const { data: devicesData } = useQuery({
    queryKey: ['devices-for-ink'],
    queryFn: () => DeviceAPI.getDevices({ limit: 100 }),
  });

  const { data: analyticsData } = useQuery({
    queryKey: ['ink-analytics'],
    queryFn: () => InkOpsAPI.getAnalytics(),
    enabled: showAnalytics,
  });

  const { data: debugData } = useQuery({
    queryKey: ['session-debug', selectedSession?.id],
    queryFn: () =>
      selectedSession
        ? InkOpsAPI.getSessionDebugInfo(selectedSession.id)
        : null,
    enabled: showDebugInfo && !!selectedSession,
  });

  const terminateSessionMutation = useMutation({
    mutationFn: ({
      sessionId,
      reason,
    }: {
      sessionId: string;
      reason?: string;
    }) => InkOpsAPI.terminateSession(sessionId, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ink-sessions'] });
    },
  });

  const bulkTerminateMutation = useMutation({
    mutationFn: ({
      sessionIds,
      reason,
    }: {
      sessionIds: string[];
      reason?: string;
    }) => InkOpsAPI.bulkTerminateSessions(sessionIds, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ink-sessions'] });
      setSelectedSessions([]);
    },
  });

  const exportSessionMutation = useMutation({
    mutationFn: ({
      sessionId,
      format,
    }: {
      sessionId: string;
      format: 'json' | 'svg' | 'pdf';
    }) => InkOpsAPI.exportSessionData(sessionId, format),
    onSuccess: data => {
      // Open download URL in new tab
      window.open(data.download_url, '_blank');
    },
  });

  const handleTerminateSession = (sessionId: string) => {
    const reason = window.prompt('Reason for termination (optional):');
    terminateSessionMutation.mutate({ sessionId, reason: reason || undefined });
  };

  const handleBulkTerminate = () => {
    if (selectedSessions.length === 0) return;

    const reason = window.prompt('Reason for bulk termination (optional):');
    if (window.confirm(`Terminate ${selectedSessions.length} sessions?`)) {
      bulkTerminateMutation.mutate({
        sessionIds: selectedSessions,
        reason: reason || undefined,
      });
    }
  };

  const handleExportSession = (
    sessionId: string,
    format: 'json' | 'svg' | 'pdf'
  ) => {
    exportSessionMutation.mutate({ sessionId, format });
  };

  const getStatusIcon = (status: InkSession['status']) => {
    switch (status) {
      case 'active':
        return <Play className='h-4 w-4 text-green-500' />;
      case 'completed':
        return <CheckCircle className='h-4 w-4 text-blue-500' />;
      case 'failed':
        return <AlertTriangle className='h-4 w-4 text-red-500' />;
      case 'timeout':
        return <Clock className='h-4 w-4 text-yellow-500' />;
      default:
        return <Square className='h-4 w-4 text-gray-500' />;
    }
  };

  const getStatusBadge = (status: InkSession['status']) => {
    const variants = {
      active: 'default',
      completed: 'secondary',
      failed: 'destructive',
      timeout: 'outline',
    } as const;

    return <Badge variant={variants[status] || 'outline'}>{status}</Badge>;
  };

  const formatDuration = (ms?: number) => {
    if (!ms) return '-';
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) return `${hours}h ${minutes % 60}m`;
    if (minutes > 0) return `${minutes}m ${seconds % 60}s`;
    return `${seconds}s`;
  };

  return (
    <div className='space-y-6'>
      {/* Header */}
      <div className='flex items-center justify-between'>
        <div>
          <h1 className='text-3xl font-bold tracking-tight'>Ink Operations</h1>
          <p className='text-muted-foreground'>
            Monitor and debug ink sessions across devices
          </p>
        </div>
        <div className='flex items-center gap-4'>
          <Button
            variant='outline'
            onClick={() => setShowAnalytics(!showAnalytics)}
          >
            <BarChart3 className='h-4 w-4 mr-2' />
            Analytics
          </Button>
          <Button
            variant='outline'
            onClick={() =>
              queryClient.invalidateQueries({ queryKey: ['ink-sessions'] })
            }
          >
            <RefreshCw className='h-4 w-4 mr-2' />
            Refresh
          </Button>
          {selectedSessions.length > 0 && (
            <Button
              variant='destructive'
              onClick={handleBulkTerminate}
              disabled={bulkTerminateMutation.isPending}
            >
              <Square className='h-4 w-4 mr-2' />
              Terminate Selected ({selectedSessions.length})
            </Button>
          )}
        </div>
      </div>

      {/* Analytics Cards */}
      {showAnalytics && analyticsData && (
        <div className='grid grid-cols-1 md:grid-cols-4 gap-4'>
          <Card className='p-4'>
            <div className='flex items-center gap-3'>
              <Pen className='h-8 w-8 text-blue-500' />
              <div>
                <p className='text-sm text-muted-foreground'>Total Sessions</p>
                <p className='text-2xl font-bold'>
                  {analyticsData.total_sessions}
                </p>
              </div>
            </div>
          </Card>
          <Card className='p-4'>
            <div className='flex items-center gap-3'>
              <Play className='h-8 w-8 text-green-500' />
              <div>
                <p className='text-sm text-muted-foreground'>Active Sessions</p>
                <p className='text-2xl font-bold'>
                  {analyticsData.active_sessions}
                </p>
              </div>
            </div>
          </Card>
          <Card className='p-4'>
            <div className='flex items-center gap-3'>
              <Clock className='h-8 w-8 text-orange-500' />
              <div>
                <p className='text-sm text-muted-foreground'>Avg Duration</p>
                <p className='text-2xl font-bold'>
                  {formatDuration(analyticsData.avg_session_duration)}
                </p>
              </div>
            </div>
          </Card>
          <Card className='p-4'>
            <div className='flex items-center gap-3'>
              <Pen className='h-8 w-8 text-purple-500' />
              <div>
                <p className='text-sm text-muted-foreground'>Total Strokes</p>
                <p className='text-2xl font-bold'>
                  {analyticsData.total_strokes.toLocaleString()}
                </p>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Filters */}
      <Card className='p-4'>
        <div className='grid grid-cols-1 md:grid-cols-5 gap-4'>
          <div className='relative'>
            <Search className='h-4 w-4 absolute left-3 top-3 text-muted-foreground' />
            <Input placeholder='Search sessions...' className='pl-10' />
          </div>
          <Select
            value={filters.device_id}
            onChange={e =>
              setFilters(prev => ({ ...prev, device_id: e.target.value }))
            }
          >
            <option value=''>All Devices</option>
            {devicesData?.devices.map(device => (
              <option key={device.id} value={device.id}>
                {device.serial_number}
              </option>
            ))}
          </Select>
          <Select
            value={filters.status}
            onChange={e =>
              setFilters(prev => ({ ...prev, status: e.target.value }))
            }
          >
            <option value=''>All Status</option>
            <option value='active'>Active</option>
            <option value='completed'>Completed</option>
            <option value='failed'>Failed</option>
            <option value='timeout'>Timeout</option>
          </Select>
          <Select
            value={filters.session_type}
            onChange={e =>
              setFilters(prev => ({ ...prev, session_type: e.target.value }))
            }
          >
            <option value=''>All Types</option>
            <option value='handwriting'>Handwriting</option>
            <option value='drawing'>Drawing</option>
            <option value='annotation'>Annotation</option>
          </Select>
          <Button variant='outline'>
            <Filter className='h-4 w-4 mr-2' />
            More Filters
          </Button>
        </div>
      </Card>

      {/* Sessions Table */}
      <Card>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className='w-12'>
                <input
                  type='checkbox'
                  onChange={e => {
                    if (e.target.checked) {
                      setSelectedSessions(
                        sessionsData?.sessions.map(s => s.id) || []
                      );
                    } else {
                      setSelectedSessions([]);
                    }
                  }}
                />
              </TableHead>
              <TableHead>Session</TableHead>
              <TableHead>Device</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Duration</TableHead>
              <TableHead>Strokes</TableHead>
              <TableHead>Started</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={9} className='text-center py-8'>
                  <RefreshCw className='h-6 w-6 animate-spin mx-auto mb-2' />
                  Loading sessions...
                </TableCell>
              </TableRow>
            ) : sessionsData?.sessions.length === 0 ? (
              <TableRow>
                <TableCell colSpan={9} className='text-center py-8'>
                  <Pen className='h-12 w-12 text-muted-foreground mx-auto mb-4' />
                  <p className='text-lg font-medium'>No ink sessions found</p>
                  <p className='text-muted-foreground'>
                    Sessions will appear here as users interact with ink-enabled
                    devices
                  </p>
                </TableCell>
              </TableRow>
            ) : (
              sessionsData?.sessions.map(session => (
                <TableRow key={session.id}>
                  <TableCell>
                    <input
                      type='checkbox'
                      checked={selectedSessions.includes(session.id)}
                      onChange={e => {
                        if (e.target.checked) {
                          setSelectedSessions(prev => [...prev, session.id]);
                        } else {
                          setSelectedSessions(prev =>
                            prev.filter(id => id !== session.id)
                          );
                        }
                      }}
                    />
                  </TableCell>
                  <TableCell>
                    <div className='flex items-center gap-3'>
                      {getStatusIcon(session.status)}
                      <div>
                        <p className='font-medium'>
                          {session.id.slice(0, 8)}...
                        </p>
                        <p className='text-sm text-muted-foreground'>
                          {session.canvas_dimensions.width}×
                          {session.canvas_dimensions.height}
                        </p>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <code className='text-sm'>
                      {session.device_id.slice(0, 8)}...
                    </code>
                  </TableCell>
                  <TableCell>
                    <Badge variant='outline'>{session.session_type}</Badge>
                  </TableCell>
                  <TableCell>{getStatusBadge(session.status)}</TableCell>
                  <TableCell>{formatDuration(session.duration_ms)}</TableCell>
                  <TableCell>
                    <div className='text-center'>
                      <p className='font-medium'>{session.stroke_count}</p>
                      <p className='text-xs text-muted-foreground'>
                        {session.total_ink_points} points
                      </p>
                    </div>
                  </TableCell>
                  <TableCell>
                    {new Date(session.started_at).toLocaleString()}
                  </TableCell>
                  <TableCell>
                    <div className='flex items-center gap-1'>
                      <Button
                        size='sm'
                        variant='outline'
                        onClick={() => {
                          setSelectedSession(session);
                          setShowDebugInfo(true);
                        }}
                      >
                        <Eye className='h-3 w-3' />
                      </Button>

                      <Select
                        onChange={e => {
                          const format = e.target.value as
                            | 'json'
                            | 'svg'
                            | 'pdf'
                            | '';
                          if (format) {
                            handleExportSession(session.id, format);
                            e.target.value = '';
                          }
                        }}
                      >
                        <option value=''>Export</option>
                        <option value='json'>JSON</option>
                        <option value='svg'>SVG</option>
                        <option value='pdf'>PDF</option>
                      </Select>

                      {session.status === 'active' && (
                        <Button
                          size='sm'
                          variant='destructive'
                          onClick={() => handleTerminateSession(session.id)}
                          disabled={terminateSessionMutation.isPending}
                        >
                          <Square className='h-3 w-3' />
                        </Button>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </Card>

      {/* Pagination */}
      {sessionsData && sessionsData.totalPages > 1 && (
        <div className='flex items-center justify-between'>
          <p className='text-sm text-muted-foreground'>
            Showing {(currentPage - 1) * 20 + 1} to{' '}
            {Math.min(currentPage * 20, sessionsData.total)} of{' '}
            {sessionsData.total} sessions
          </p>
          <div className='flex items-center gap-2'>
            <Button
              variant='outline'
              disabled={currentPage === 1}
              onClick={() => setCurrentPage(prev => prev - 1)}
            >
              Previous
            </Button>
            <span className='text-sm'>
              Page {currentPage} of {sessionsData.totalPages}
            </span>
            <Button
              variant='outline'
              disabled={currentPage === sessionsData.totalPages}
              onClick={() => setCurrentPage(prev => prev + 1)}
            >
              Next
            </Button>
          </div>
        </div>
      )}

      {/* Debug Info Modal */}
      {showDebugInfo && selectedSession && (
        <div className='fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50'>
          <Card className='w-full max-w-4xl p-6 max-h-[90vh] overflow-y-auto'>
            <div className='flex items-center justify-between mb-4'>
              <h2 className='text-lg font-semibold'>
                Session Debug Info: {selectedSession.id}
              </h2>
              <Button variant='outline' onClick={() => setShowDebugInfo(false)}>
                Close
              </Button>
            </div>

            {debugData && (
              <div className='space-y-6'>
                {/* Session Info */}
                <div>
                  <h3 className='font-medium mb-2'>Session Details</h3>
                  <div className='grid grid-cols-2 gap-4 text-sm'>
                    <div>
                      <span className='text-muted-foreground'>Type:</span>{' '}
                      {debugData.session.session_type}
                    </div>
                    <div>
                      <span className='text-muted-foreground'>Status:</span>{' '}
                      {debugData.session.status}
                    </div>
                    <div>
                      <span className='text-muted-foreground'>Duration:</span>{' '}
                      {formatDuration(debugData.session.duration_ms)}
                    </div>
                    <div>
                      <span className='text-muted-foreground'>Strokes:</span>{' '}
                      {debugData.session.stroke_count}
                    </div>
                  </div>
                </div>

                {/* Performance Metrics */}
                <div>
                  <h3 className='font-medium mb-2'>Performance Metrics</h3>
                  <div className='grid grid-cols-2 md:grid-cols-4 gap-4'>
                    <Card className='p-3'>
                      <div className='text-center'>
                        <p className='text-2xl font-bold'>
                          {debugData.performance_metrics.latency_ms}ms
                        </p>
                        <p className='text-xs text-muted-foreground'>Latency</p>
                      </div>
                    </Card>
                    <Card className='p-3'>
                      <div className='text-center'>
                        <p className='text-2xl font-bold'>
                          {debugData.performance_metrics.frame_drops}
                        </p>
                        <p className='text-xs text-muted-foreground'>
                          Frame Drops
                        </p>
                      </div>
                    </Card>
                    <Card className='p-3'>
                      <div className='text-center'>
                        <p className='text-2xl font-bold'>
                          {debugData.performance_metrics.memory_usage_mb}MB
                        </p>
                        <p className='text-xs text-muted-foreground'>Memory</p>
                      </div>
                    </Card>
                    <Card className='p-3'>
                      <div className='text-center'>
                        <p className='text-2xl font-bold'>
                          {debugData.performance_metrics.cpu_usage_percent}%
                        </p>
                        <p className='text-xs text-muted-foreground'>CPU</p>
                      </div>
                    </Card>
                  </div>
                </div>

                {/* Error Logs */}
                {debugData.error_logs.length > 0 && (
                  <div>
                    <h3 className='font-medium mb-2'>Error Logs</h3>
                    <div className='space-y-2 max-h-48 overflow-y-auto'>
                      {debugData.error_logs.map((log, index) => (
                        <div
                          key={index}
                          className={`p-2 rounded text-sm ${
                            log.level === 'error'
                              ? 'bg-red-50 text-red-800'
                              : log.level === 'warning'
                                ? 'bg-yellow-50 text-yellow-800'
                                : 'bg-blue-50 text-blue-800'
                          }`}
                        >
                          <div className='flex items-center gap-2'>
                            <span className='font-medium'>
                              {log.level.toUpperCase()}
                            </span>
                            <span className='text-xs'>
                              {new Date(log.timestamp).toLocaleString()}
                            </span>
                          </div>
                          <p>{log.message}</p>
                          {log.stack_trace && (
                            <pre className='text-xs mt-1 overflow-x-auto'>
                              {log.stack_trace}
                            </pre>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Stroke Data Preview */}
                <div>
                  <h3 className='font-medium mb-2'>
                    Stroke Data ({debugData.strokes.length} strokes)
                  </h3>
                  <div className='bg-gray-50 p-4 rounded-md max-h-32 overflow-y-auto'>
                    <pre className='text-xs'>
                      {JSON.stringify(debugData.strokes.slice(0, 3), null, 2)}
                      {debugData.strokes.length > 3 && '\n... and more'}
                    </pre>
                  </div>
                </div>
              </div>
            )}
          </Card>
        </div>
      )}
    </div>
  );
}
