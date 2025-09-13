/**
 * Admin UI component for audit logs management.
 */

import {
  Search,
  Download,
  Shield,
  Clock,
  User,
  Activity,
  FileText,
  CheckCircle,
  XCircle,
  AlertCircle,
  RefreshCw,
} from 'lucide-react';
import { useState, useEffect, useCallback } from 'react';

import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

interface AuditEvent {
  id: string;
  event_type: string;
  resource_type: string;
  resource_id: string;
  user_id: string;
  action: string;
  details: Record<string, string | number | boolean>;
  ip_address: string;
  user_agent: string;
  session_id?: string;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  hash: string;
  previous_hash?: string;
  created_at: string;
}

interface ExportJob {
  id: string;
  job_name: string;
  requested_by: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  export_format: 'csv' | 'json' | 'xlsx';
  total_records?: number;
  file_size_bytes?: number;
  download_url?: string;
  started_at?: string;
  completed_at?: string;
  expires_at?: string;
  error_message?: string;
  created_at: string;
}

interface AuditStats {
  total_events: number;
  events_last_24h: number;
  unique_users_last_24h: number;
  high_risk_events_last_24h: number;
  hash_chain_verified: boolean;
  last_verification: string;
}

const AUDIT_SERVICE_URL =
  typeof window !== 'undefined'
    ? (window as { env?: { NEXT_PUBLIC_AUDIT_SERVICE_URL?: string } }).env
        ?.NEXT_PUBLIC_AUDIT_SERVICE_URL || 'http://localhost:8000'
    : 'http://localhost:8000';

export default function AuditLogs() {
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [exportJobs, setExportJobs] = useState<ExportJob[]>([]);
  const [auditStats, setAuditStats] = useState<AuditStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedEvent, setSelectedEvent] = useState<AuditEvent | null>(null);
  const [showExportDialog, setShowExportDialog] = useState(false);

  // Filters
  const [filters, setFilters] = useState({
    search: '',
    event_type: '',
    user_id: '',
    risk_level: '',
    start_date: '',
    end_date: '',
  });

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(50);
  const [totalEvents, setTotalEvents] = useState(0);

  // Export form
  const [exportForm, setExportForm] = useState({
    job_name: '',
    export_format: 'csv' as 'csv' | 'json' | 'xlsx',
    include_details: true,
  });

  // Fetch audit events
  const fetchAuditEvents = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      params.append('page', currentPage.toString());
      params.append('page_size', pageSize.toString());

      Object.entries(filters).forEach(([key, value]) => {
        if (value) {
          params.append(key, value);
        }
      });

      const response = await fetch(
        `${AUDIT_SERVICE_URL}/api/v1/audit?${params}`
      );
      if (!response.ok) {
        throw new Error('Failed to fetch audit events');
      }

      const data = await response.json();
      setAuditEvents(data.events);
      setTotalEvents(data.pagination.total);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to fetch audit events'
      );
    } finally {
      setLoading(false);
    }
  }, [currentPage, pageSize, filters]);

  // Fetch export jobs
  const fetchExportJobs = useCallback(async () => {
    try {
      const response = await fetch(`${AUDIT_SERVICE_URL}/api/v1/export`);
      if (!response.ok) {
        throw new Error('Failed to fetch export jobs');
      }

      const data = await response.json();
      setExportJobs(data.jobs);
      // Silent error for non-critical functionality
    } catch {
      // Log error without console for production
    }
  }, []);

  // Fetch audit statistics
  const fetchAuditStats = useCallback(async () => {
    try {
      const response = await fetch(`${AUDIT_SERVICE_URL}/api/v1/audit/stats`);
      if (!response.ok) {
        throw new Error('Failed to fetch audit stats');
      }

      const data = await response.json();
      setAuditStats(data);
    } catch {
      // Silent error for non-critical functionality
    }
  }, []);

  // Initial load
  useEffect(() => {
    fetchAuditEvents();
    fetchExportJobs();
    fetchAuditStats();
  }, [fetchAuditEvents, fetchExportJobs, fetchAuditStats]);

  // Handle filter change
  const handleFilterChange = (key: string, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setCurrentPage(1); // Reset to first page when filtering
  };

  // Handle search
  const handleSearch = () => {
    fetchAuditEvents();
  };

  // Create export job
  const handleCreateExport = async () => {
    try {
      const exportData = {
        job_name: exportForm.job_name,
        export_format: exportForm.export_format,
        filters: exportForm.include_details ? filters : {},
        start_date: filters.start_date || null,
        end_date: filters.end_date || null,
      };

      const response = await fetch(
        `${AUDIT_SERVICE_URL}/api/v1/export?requested_by=admin`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(exportData),
        }
      );

      if (!response.ok) {
        throw new Error('Failed to create export job');
      }

      setShowExportDialog(false);
      setExportForm({
        job_name: '',
        export_format: 'csv',
        include_details: true,
      });
      fetchExportJobs();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create export');
    }
  };

  // Verify hash chain
  const handleVerifyHashChain = async () => {
    try {
      const response = await fetch(`${AUDIT_SERVICE_URL}/api/v1/audit/verify`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ verify_all: true }),
      });

      if (!response.ok) {
        throw new Error('Failed to verify hash chain');
      }

      const result = await response.json();
      if (result.is_valid) {
        alert(
          'Hash chain verification successful! Audit log integrity confirmed.'
        );
      } else {
        alert(`Hash chain verification failed! ${result.errors?.join(', ')}`);
      }

      fetchAuditStats();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to verify hash chain'
      );
    }
  };

  const getRiskLevelColor = (level: string) => {
    switch (level) {
      case 'critical':
        return 'bg-red-100 text-red-800';
      case 'high':
        return 'bg-orange-100 text-orange-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'low':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className='h-4 w-4 text-green-500' />;
      case 'failed':
        return <XCircle className='h-4 w-4 text-red-500' />;
      case 'processing':
        return <RefreshCw className='h-4 w-4 text-blue-500 animate-spin' />;
      default:
        return <Clock className='h-4 w-4 text-gray-500' />;
    }
  };

  const formatDateTime = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    } catch {
      return dateString;
    }
  };

  const formatTimeAgo = (dateString: string) => {
    try {
      const date = new Date(dateString);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffMins = Math.floor(diffMs / (1000 * 60));
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
      const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

      if (diffMins < 60) return `${diffMins}m ago`;
      if (diffHours < 24) return `${diffHours}h ago`;
      return `${diffDays}d ago`;
    } catch {
      return dateString;
    }
  };

  return (
    <div className='space-y-6'>
      {/* Header */}
      <div className='flex items-center justify-between'>
        <div>
          <h1 className='text-3xl font-bold tracking-tight'>Audit Logs</h1>
          <p className='text-muted-foreground'>
            Immutable audit trail with WORM compliance and hash chain
            verification
          </p>
        </div>
        <div className='flex gap-2'>
          <Button onClick={handleVerifyHashChain} variant='outline'>
            <Shield className='h-4 w-4 mr-2' />
            Verify Integrity
          </Button>
          <Button onClick={() => setShowExportDialog(true)}>
            <Download className='h-4 w-4 mr-2' />
            Export Data
          </Button>
        </div>
      </div>

      {/* Statistics Cards */}
      {auditStats && (
        <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4'>
          <Card>
            <CardContent className='p-4'>
              <div className='flex items-center justify-between'>
                <div>
                  <p className='text-sm text-muted-foreground'>Total Events</p>
                  <p className='text-2xl font-bold'>
                    {auditStats.total_events.toLocaleString()}
                  </p>
                </div>
                <Activity className='h-8 w-8 text-blue-500' />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className='p-4'>
              <div className='flex items-center justify-between'>
                <div>
                  <p className='text-sm text-muted-foreground'>Events (24h)</p>
                  <p className='text-2xl font-bold'>
                    {auditStats.events_last_24h}
                  </p>
                </div>
                <Clock className='h-8 w-8 text-green-500' />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className='p-4'>
              <div className='flex items-center justify-between'>
                <div>
                  <p className='text-sm text-muted-foreground'>
                    Active Users (24h)
                  </p>
                  <p className='text-2xl font-bold'>
                    {auditStats.unique_users_last_24h}
                  </p>
                </div>
                <User className='h-8 w-8 text-purple-500' />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className='p-4'>
              <div className='flex items-center justify-between'>
                <div>
                  <p className='text-sm text-muted-foreground'>
                    High Risk (24h)
                  </p>
                  <p className='text-2xl font-bold'>
                    {auditStats.high_risk_events_last_24h}
                  </p>
                </div>
                <AlertCircle className='h-8 w-8 text-red-500' />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Hash Chain Status */}
      {auditStats && (
        <Alert>
          <Shield className='h-4 w-4' />
          <AlertDescription>
            Hash chain integrity:{' '}
            {auditStats.hash_chain_verified ? 'Verified' : 'Failed'}
            {auditStats.last_verification &&
              ` (last check: ${formatTimeAgo(auditStats.last_verification)})`}
          </AlertDescription>
        </Alert>
      )}

      <Tabs value='events' className='space-y-4'>
        <TabsList>
          <TabsTrigger value='events'>Audit Events</TabsTrigger>
          <TabsTrigger value='exports'>Export Jobs</TabsTrigger>
        </TabsList>

        <TabsContent value='events' className='space-y-4'>
          {/* Filters */}
          <Card>
            <CardHeader>
              <CardTitle>Filters & Search</CardTitle>
            </CardHeader>
            <CardContent>
              <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4'>
                <div>
                  <Label htmlFor='search'>Search</Label>
                  <div className='flex gap-2'>
                    <Input
                      id='search'
                      placeholder='Search events...'
                      value={filters.search}
                      onChange={e =>
                        handleFilterChange('search', e.target.value)
                      }
                    />
                    <Button onClick={handleSearch}>
                      <Search className='h-4 w-4' />
                    </Button>
                  </div>
                </div>
                <div>
                  <Label htmlFor='event_type'>Event Type</Label>
                  <Input
                    id='event_type'
                    placeholder='e.g., user.login'
                    value={filters.event_type}
                    onChange={e =>
                      handleFilterChange('event_type', e.target.value)
                    }
                  />
                </div>
                <div>
                  <Label htmlFor='user_id'>User ID</Label>
                  <Input
                    id='user_id'
                    placeholder='Filter by user'
                    value={filters.user_id}
                    onChange={e =>
                      handleFilterChange('user_id', e.target.value)
                    }
                  />
                </div>
                <div>
                  <Label htmlFor='risk_level'>Risk Level</Label>
                  <select
                    id='risk_level'
                    className='flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background'
                    value={filters.risk_level}
                    onChange={e =>
                      handleFilterChange('risk_level', e.target.value)
                    }
                  >
                    <option value=''>All levels</option>
                    <option value='low'>Low</option>
                    <option value='medium'>Medium</option>
                    <option value='high'>High</option>
                    <option value='critical'>Critical</option>
                  </select>
                </div>
                <div>
                  <Label htmlFor='start_date'>Start Date</Label>
                  <Input
                    id='start_date'
                    type='datetime-local'
                    value={filters.start_date}
                    onChange={e =>
                      handleFilterChange('start_date', e.target.value)
                    }
                  />
                </div>
                <div>
                  <Label htmlFor='end_date'>End Date</Label>
                  <Input
                    id='end_date'
                    type='datetime-local'
                    value={filters.end_date}
                    onChange={e =>
                      handleFilterChange('end_date', e.target.value)
                    }
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Error Display */}
          {error && (
            <Alert variant='destructive'>
              <AlertCircle className='h-4 w-4' />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Events Table */}
          <Card>
            <CardHeader>
              <CardTitle>
                Audit Events ({totalEvents.toLocaleString()} total)
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className='flex items-center justify-center p-8'>
                  <RefreshCw className='h-8 w-8 animate-spin' />
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Timestamp</TableHead>
                      <TableHead>Event Type</TableHead>
                      <TableHead>User</TableHead>
                      <TableHead>Action</TableHead>
                      <TableHead>Risk Level</TableHead>
                      <TableHead>Resource</TableHead>
                      <TableHead>Details</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {auditEvents.map(event => (
                      <TableRow
                        key={event.id}
                        className='cursor-pointer hover:bg-muted/50'
                        onClick={() => setSelectedEvent(event)}
                      >
                        <TableCell>
                          <div className='text-sm'>
                            {formatDateTime(event.created_at)}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant='outline'>{event.event_type}</Badge>
                        </TableCell>
                        <TableCell>{event.user_id}</TableCell>
                        <TableCell>{event.action}</TableCell>
                        <TableCell>
                          <Badge
                            className={getRiskLevelColor(event.risk_level)}
                          >
                            {event.risk_level}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className='text-sm'>
                            <div>{event.resource_type}</div>
                            <div className='text-muted-foreground text-xs'>
                              {event.resource_id}
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Button variant='ghost' size='sm'>
                            <FileText className='h-4 w-4' />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}

              {/* Pagination */}
              <div className='flex items-center justify-between mt-4'>
                <div className='text-sm text-muted-foreground'>
                  Page {currentPage} of {Math.ceil(totalEvents / pageSize)}
                </div>
                <div className='flex gap-2'>
                  <Button
                    variant='outline'
                    onClick={() =>
                      setCurrentPage(prev => Math.max(1, prev - 1))
                    }
                    disabled={currentPage === 1}
                  >
                    Previous
                  </Button>
                  <Button
                    variant='outline'
                    onClick={() => setCurrentPage(prev => prev + 1)}
                    disabled={currentPage >= Math.ceil(totalEvents / pageSize)}
                  >
                    Next
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value='exports' className='space-y-4'>
          <Card>
            <CardHeader>
              <CardTitle>Export Jobs</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Job Name</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Format</TableHead>
                    <TableHead>Records</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {exportJobs.map(job => (
                    <TableRow key={job.id}>
                      <TableCell>{job.job_name}</TableCell>
                      <TableCell>
                        <div className='flex items-center gap-2'>
                          {getStatusIcon(job.status)}
                          <span className='capitalize'>{job.status}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant='outline'>
                          {job.export_format.toUpperCase()}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {job.total_records
                          ? job.total_records.toLocaleString()
                          : '-'}
                      </TableCell>
                      <TableCell>{formatTimeAgo(job.created_at)}</TableCell>
                      <TableCell>
                        {job.status === 'completed' && job.download_url && (
                          <Button
                            variant='outline'
                            size='sm'
                            onClick={() =>
                              window.open(job.download_url, '_blank')
                            }
                          >
                            <Download className='h-4 w-4 mr-2' />
                            Download
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Export Dialog */}
      {showExportDialog && (
        <div className='fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50'>
          <div className='bg-white p-6 rounded-lg max-w-md w-full mx-4'>
            <h2 className='text-lg font-semibold mb-4'>Export Audit Logs</h2>
            <p className='text-sm text-gray-600 mb-4'>
              Create a downloadable export of audit log data with current
              filters applied.
            </p>
            <div className='space-y-4'>
              <div>
                <Label htmlFor='export_job_name'>Export Name</Label>
                <Input
                  id='export_job_name'
                  value={exportForm.job_name}
                  onChange={e =>
                    setExportForm(prev => ({
                      ...prev,
                      job_name: e.target.value,
                    }))
                  }
                  placeholder='Enter export job name'
                />
              </div>
              <div>
                <Label htmlFor='export_format'>Format</Label>
                <select
                  id='export_format'
                  className='flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background'
                  value={exportForm.export_format}
                  onChange={e =>
                    setExportForm(prev => ({
                      ...prev,
                      export_format: e.target.value as 'csv' | 'json' | 'xlsx',
                    }))
                  }
                >
                  <option value='csv'>CSV</option>
                  <option value='json'>JSON</option>
                  <option value='xlsx'>Excel</option>
                </select>
              </div>
              <div className='flex items-center space-x-2'>
                <input
                  type='checkbox'
                  id='export_include_details'
                  checked={exportForm.include_details}
                  onChange={e =>
                    setExportForm(prev => ({
                      ...prev,
                      include_details: e.target.checked,
                    }))
                  }
                />
                <Label htmlFor='export_include_details'>
                  Apply current filters
                </Label>
              </div>
              <div className='flex gap-2 pt-4'>
                <Button onClick={handleCreateExport} className='flex-1'>
                  Create Export
                </Button>
                <Button
                  variant='outline'
                  onClick={() => setShowExportDialog(false)}
                  className='flex-1'
                >
                  Cancel
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Event Details Modal */}
      {selectedEvent && (
        <div className='fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50'>
          <div className='bg-white p-6 rounded-lg max-w-4xl max-h-[80vh] overflow-y-auto mx-4'>
            <div className='flex justify-between items-start mb-4'>
              <div>
                <h2 className='text-lg font-semibold'>Audit Event Details</h2>
                <p className='text-sm text-gray-600'>
                  Event ID: {selectedEvent.id}
                </p>
              </div>
              <Button variant='outline' onClick={() => setSelectedEvent(null)}>
                ×
              </Button>
            </div>
            <div className='space-y-4'>
              <div className='grid grid-cols-2 gap-4'>
                <div>
                  <Label>Timestamp</Label>
                  <p className='text-sm'>
                    {formatDateTime(selectedEvent.created_at)}
                  </p>
                </div>
                <div>
                  <Label>Event Type</Label>
                  <p className='text-sm'>{selectedEvent.event_type}</p>
                </div>
                <div>
                  <Label>User ID</Label>
                  <p className='text-sm'>{selectedEvent.user_id}</p>
                </div>
                <div>
                  <Label>Action</Label>
                  <p className='text-sm'>{selectedEvent.action}</p>
                </div>
                <div>
                  <Label>Risk Level</Label>
                  <Badge
                    className={getRiskLevelColor(selectedEvent.risk_level)}
                  >
                    {selectedEvent.risk_level}
                  </Badge>
                </div>
                <div>
                  <Label>IP Address</Label>
                  <p className='text-sm'>{selectedEvent.ip_address}</p>
                </div>
                <div>
                  <Label>Resource Type</Label>
                  <p className='text-sm'>{selectedEvent.resource_type}</p>
                </div>
                <div>
                  <Label>Resource ID</Label>
                  <p className='text-sm'>{selectedEvent.resource_id}</p>
                </div>
              </div>

              {selectedEvent.session_id && (
                <div>
                  <Label>Session ID</Label>
                  <p className='text-sm'>{selectedEvent.session_id}</p>
                </div>
              )}

              <div>
                <Label>User Agent</Label>
                <p className='text-sm break-all'>{selectedEvent.user_agent}</p>
              </div>

              <div>
                <Label>Hash</Label>
                <p className='text-sm font-mono break-all'>
                  {selectedEvent.hash}
                </p>
              </div>

              {selectedEvent.previous_hash && (
                <div>
                  <Label>Previous Hash</Label>
                  <p className='text-sm font-mono break-all'>
                    {selectedEvent.previous_hash}
                  </p>
                </div>
              )}

              <div>
                <Label>Event Details</Label>
                <pre className='text-sm bg-gray-100 p-4 rounded-md overflow-x-auto'>
                  {JSON.stringify(selectedEvent.details, null, 2)}
                </pre>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
