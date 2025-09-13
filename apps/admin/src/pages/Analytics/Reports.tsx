import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Calendar, Download, Play, Plus, Edit2 } from 'lucide-react';
import React, { useState } from 'react';

import { ReportsAPI } from '@/api/reports';
import type {
  Report,
  Schedule,
  CreateReportRequest,
  CreateScheduleRequest,
} from '@/api/reports';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';

// Report Builder Component
const ReportBuilder = ({
  report,
  onSave,
  onCancel,
}: {
  report?: Report;
  onSave: (reportData: CreateReportRequest) => void;
  onCancel: () => void;
}) => {
  const [formData, setFormData] = useState({
    name: report?.name || '',
    description: report?.description || '',
    table: report?.query_config?.table || 'usage_events',
    fields: report?.query_config?.fields || ['*'],
    row_limit: report?.row_limit || 10000,
    tags: report?.tags?.join(', ') || '',
  });

  const [availableTables] = useState([
    'usage_events',
    'user_sessions',
    'device_metrics',
    'billing_events',
  ]);

  const [availableFields] = useState({
    usage_events: [
      'user_id',
      'event_type',
      'timestamp',
      'device_id',
      'tenant_id',
    ],
    user_sessions: [
      'session_id',
      'user_id',
      'start_time',
      'end_time',
      'duration',
    ],
    device_metrics: ['device_id', 'metric_type', 'value', 'timestamp'],
    billing_events: [
      'account_id',
      'amount',
      'currency',
      'event_date',
      'description',
    ],
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const reportData = {
      name: formData.name,
      description: formData.description,
      query_config: {
        table: formData.table,
        fields: formData.fields,
        limit: formData.row_limit,
      },
      row_limit: formData.row_limit,
      tags: formData.tags
        .split(',')
        .map((tag: string) => tag.trim())
        .filter(Boolean),
      is_public: false,
    };

    onSave(reportData);
  };

  return (
    <form onSubmit={handleSubmit} className='space-y-6'>
      <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
        <div>
          <Label htmlFor='name'>Report Name</Label>
          <Input
            id='name'
            value={formData.name}
            onChange={e =>
              setFormData(prev => ({ ...prev, name: e.target.value }))
            }
            placeholder='Enter report name'
            required
          />
        </div>

        <div>
          <Label htmlFor='row_limit'>Row Limit</Label>
          <Input
            id='row_limit'
            type='number'
            value={formData.row_limit}
            onChange={e =>
              setFormData(prev => ({
                ...prev,
                row_limit: parseInt(e.target.value),
              }))
            }
            min='1'
            max='100000'
          />
        </div>
      </div>

      <div>
        <Label htmlFor='description'>Description</Label>
        <Textarea
          id='description'
          value={formData.description}
          onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) =>
            setFormData(prev => ({ ...prev, description: e.target.value }))
          }
          placeholder='Enter report description'
          rows={3}
        />
      </div>

      <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
        <div>
          <Label htmlFor='table'>Data Source</Label>
          <Select
            value={formData.table}
            onValueChange={value =>
              setFormData(prev => ({ ...prev, table: value }))
            }
          >
            <SelectTrigger>
              <SelectValue placeholder='Select data source' />
            </SelectTrigger>
            <SelectContent>
              {availableTables.map(table => (
                <SelectItem key={table} value={table}>
                  {table
                    .replace('_', ' ')
                    .replace(/\b\w/g, l => l.toUpperCase())}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div>
          <Label htmlFor='tags'>Tags</Label>
          <Input
            id='tags'
            value={formData.tags}
            onChange={e =>
              setFormData(prev => ({ ...prev, tags: e.target.value }))
            }
            placeholder='Enter tags separated by commas'
          />
        </div>
      </div>

      <div>
        <Label>Fields to Include</Label>
        <div className='mt-2 space-y-2'>
          {availableFields[formData.table as keyof typeof availableFields]?.map(
            field => (
              <div key={field} className='flex items-center space-x-2'>
                <input
                  type='checkbox'
                  id={field}
                  checked={
                    formData.fields.includes(field) ||
                    formData.fields.includes('*')
                  }
                  onChange={e => {
                    if (e.target.checked) {
                      if (
                        !formData.fields.includes(field) &&
                        !formData.fields.includes('*')
                      ) {
                        setFormData(prev => ({
                          ...prev,
                          fields: prev.fields
                            .filter((f: string) => f !== '*')
                            .concat(field),
                        }));
                      }
                    } else {
                      setFormData(prev => ({
                        ...prev,
                        fields: prev.fields.filter(
                          (f: string) => f !== field && f !== '*'
                        ),
                      }));
                    }
                  }}
                  className='rounded'
                />
                <Label htmlFor={field} className='text-sm'>
                  {field}
                </Label>
              </div>
            )
          )}
        </div>
      </div>

      <div className='flex justify-end space-x-2'>
        <Button type='button' variant='outline' onClick={onCancel}>
          Cancel
        </Button>
        <Button type='submit'>
          {report ? 'Update Report' : 'Create Report'}
        </Button>
      </div>
    </form>
  );
};

// Schedule Configuration Component
const ScheduleConfig = ({
  reportId,
  schedule,
  onSave,
  onCancel,
}: {
  reportId: string;
  schedule?: Schedule;
  onSave: (scheduleData: CreateScheduleRequest) => void;
  onCancel: () => void;
}) => {
  const [formData, setFormData] = useState({
    name: schedule?.name || '',
    description: schedule?.description || '',
    cron_expression: schedule?.cron_expression || '0 9 * * 1', // Weekly Monday 9 AM
    timezone: schedule?.timezone || 'UTC',
    format: schedule?.format || ('pdf' as const),
    delivery_method: schedule?.delivery_method || ('email' as const),
    recipients: schedule?.recipients?.join(', ') || '',
    is_active: schedule?.is_active ?? true,
  });

  const commonCronExpressions = [
    { label: 'Daily at 9 AM', value: '0 9 * * *' },
    { label: 'Weekly (Monday 9 AM)', value: '0 9 * * 1' },
    { label: 'Monthly (1st at 9 AM)', value: '0 9 1 * *' },
    { label: 'Every 6 hours', value: '0 */6 * * *' },
  ];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const scheduleData = {
      report_id: reportId,
      name: formData.name,
      description: formData.description,
      cron_expression: formData.cron_expression,
      timezone: formData.timezone,
      format: formData.format,
      delivery_method: formData.delivery_method,
      recipients: formData.recipients
        .split(',')
        .map((email: string) => email.trim())
        .filter(Boolean),
      is_active: formData.is_active,
    };

    onSave(scheduleData);
  };

  return (
    <form onSubmit={handleSubmit} className='space-y-6'>
      <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
        <div>
          <Label htmlFor='schedule_name'>Schedule Name</Label>
          <Input
            id='schedule_name'
            value={formData.name}
            onChange={e =>
              setFormData(prev => ({ ...prev, name: e.target.value }))
            }
            placeholder='Enter schedule name'
            required
          />
        </div>

        <div>
          <Label htmlFor='timezone'>Timezone</Label>
          <Select
            value={formData.timezone}
            onValueChange={value =>
              setFormData(prev => ({ ...prev, timezone: value }))
            }
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value='UTC'>UTC</SelectItem>
              <SelectItem value='America/New_York'>Eastern Time</SelectItem>
              <SelectItem value='America/Chicago'>Central Time</SelectItem>
              <SelectItem value='America/Denver'>Mountain Time</SelectItem>
              <SelectItem value='America/Los_Angeles'>Pacific Time</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <div>
        <Label htmlFor='schedule_description'>Description</Label>
        <Textarea
          id='schedule_description'
          value={formData.description}
          onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) =>
            setFormData(prev => ({ ...prev, description: e.target.value }))
          }
          placeholder='Enter schedule description'
          rows={2}
        />
      </div>

      <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
        <div>
          <Label htmlFor='cron_expression'>Schedule (Cron Expression)</Label>
          <Select
            value={formData.cron_expression}
            onValueChange={value =>
              setFormData(prev => ({ ...prev, cron_expression: value }))
            }
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {commonCronExpressions.map(expr => (
                <SelectItem key={expr.value} value={expr.value}>
                  {expr.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Input
            className='mt-2'
            value={formData.cron_expression}
            onChange={e =>
              setFormData(prev => ({
                ...prev,
                cron_expression: e.target.value,
              }))
            }
            placeholder='Custom cron expression'
          />
        </div>

        <div>
          <Label htmlFor='format'>Export Format</Label>
          <Select
            value={formData.format}
            onValueChange={(value: string) =>
              setFormData(prev => ({
                ...prev,
                format: value as 'csv' | 'pdf' | 'xlsx',
              }))
            }
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value='pdf'>PDF</SelectItem>
              <SelectItem value='csv'>CSV</SelectItem>
              <SelectItem value='xlsx'>Excel</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <div>
        <Label htmlFor='delivery_method'>Delivery Method</Label>
        <Select
          value={formData.delivery_method}
          onValueChange={(value: string) =>
            setFormData(prev => ({
              ...prev,
              delivery_method: value as 'email' | 's3' | 'both',
            }))
          }
        >
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value='email'>Email</SelectItem>
            <SelectItem value='s3'>S3 Storage</SelectItem>
            <SelectItem value='both'>Both Email & S3</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {(formData.delivery_method === 'email' ||
        formData.delivery_method === 'both') && (
        <div>
          <Label htmlFor='recipients'>Email Recipients</Label>
          <Input
            id='recipients'
            value={formData.recipients}
            onChange={e =>
              setFormData(prev => ({ ...prev, recipients: e.target.value }))
            }
            placeholder='Enter email addresses separated by commas'
            type='email'
          />
        </div>
      )}

      <div className='flex items-center space-x-2'>
        <input
          type='checkbox'
          id='is_active'
          checked={formData.is_active}
          onChange={e =>
            setFormData(prev => ({ ...prev, is_active: e.target.checked }))
          }
          className='rounded'
        />
        <Label htmlFor='is_active'>Schedule is active</Label>
      </div>

      <div className='flex justify-end space-x-2'>
        <Button type='button' variant='outline' onClick={onCancel}>
          Cancel
        </Button>
        <Button type='submit'>
          {schedule ? 'Update Schedule' : 'Create Schedule'}
        </Button>
      </div>
    </form>
  );
};

// Main Reports Component
export function Reports() {
  const [activeTab, setActiveTab] = useState('reports');
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  const [showReportBuilder, setShowReportBuilder] = useState(false);
  const [showScheduleConfig, setShowScheduleConfig] = useState(false);
  const [selectedSchedule, setSelectedSchedule] = useState<Schedule | null>(
    null
  );

  const queryClient = useQueryClient();

  // Fetch reports
  const { data: reportsData, isLoading: reportsLoading } = useQuery({
    queryKey: ['reports'],
    queryFn: () => ReportsAPI.listReports(),
  });

  // Fetch schedules
  const { data: schedulesData, isLoading: schedulesLoading } = useQuery({
    queryKey: ['schedules'],
    queryFn: () => ReportsAPI.listSchedules(),
  });

  // Fetch exports
  const { data: exportsData, isLoading: exportsLoading } = useQuery({
    queryKey: ['exports'],
    queryFn: () => ReportsAPI.listExports(),
  });

  // Create report mutation
  const createReportMutation = useMutation({
    mutationFn: ReportsAPI.createReport,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] });
      setShowReportBuilder(false);
    },
  });

  // Create schedule mutation
  const createScheduleMutation = useMutation({
    mutationFn: ReportsAPI.createSchedule,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['schedules'] });
      setShowScheduleConfig(false);
    },
  });

  // Export report mutation
  const exportReportMutation = useMutation({
    mutationFn: ({ reportId, format }: { reportId: string; format: string }) =>
      ReportsAPI.createExport({
        report_id: reportId,
        format: format as 'csv' | 'pdf' | 'xlsx',
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['exports'] });
    },
  });

  const handleCreateReport = (reportData: CreateReportRequest) => {
    createReportMutation.mutate(reportData);
  };

  const handleCreateSchedule = (scheduleData: CreateScheduleRequest) => {
    createScheduleMutation.mutate(scheduleData);
  };

  const handleExportReport = (reportId: string, format: string) => {
    exportReportMutation.mutate({ reportId, format });
  };

  const getStatusBadge = (status: string) => {
    const variants = {
      pending: 'outline',
      processing: 'secondary',
      completed: 'default',
      failed: 'destructive',
    } as const;

    return (
      <Badge variant={variants[status as keyof typeof variants] || 'outline'}>
        {status}
      </Badge>
    );
  };

  return (
    <div className='space-y-6'>
      <div className='flex items-center justify-between'>
        <div>
          <h1 className='text-3xl font-bold tracking-tight'>
            Reports & Exports
          </h1>
          <p className='text-muted-foreground'>
            Create reports and schedule automated exports to email or S3
          </p>
        </div>

        <Button onClick={() => setShowReportBuilder(true)}>
          <Plus className='h-4 w-4 mr-2' />
          New Report
        </Button>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className='grid w-full grid-cols-3'>
          <TabsTrigger value='reports'>Reports</TabsTrigger>
          <TabsTrigger value='schedules'>Schedules</TabsTrigger>
          <TabsTrigger value='exports'>Export History</TabsTrigger>
        </TabsList>

        <TabsContent value='reports' className='space-y-4'>
          <Card>
            <CardHeader>
              <CardTitle>Your Reports</CardTitle>
            </CardHeader>
            <CardContent>
              {reportsLoading ? (
                <div>Loading reports...</div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Data Source</TableHead>
                      <TableHead>Row Limit</TableHead>
                      <TableHead>Created</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {reportsData?.reports?.map(report => (
                      <TableRow key={report.id}>
                        <TableCell className='font-medium'>
                          {report.name}
                        </TableCell>
                        <TableCell>{report.query_config?.table}</TableCell>
                        <TableCell>
                          {report.row_limit.toLocaleString()}
                        </TableCell>
                        <TableCell>
                          {new Date(report.created_at).toLocaleDateString()}
                        </TableCell>
                        <TableCell>
                          <div className='flex space-x-2'>
                            <Button
                              size='sm'
                              variant='outline'
                              onClick={() =>
                                handleExportReport(report.id, 'csv')
                              }
                            >
                              <Download className='h-4 w-4' />
                            </Button>
                            <Button
                              size='sm'
                              variant='outline'
                              onClick={() => {
                                setSelectedReport(report);
                                setShowScheduleConfig(true);
                              }}
                            >
                              <Calendar className='h-4 w-4' />
                            </Button>
                            <Button
                              size='sm'
                              variant='outline'
                              onClick={() => {
                                setSelectedReport(report);
                                setShowReportBuilder(true);
                              }}
                            >
                              <Edit2 className='h-4 w-4' />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value='schedules' className='space-y-4'>
          <Card>
            <CardHeader>
              <CardTitle>Scheduled Reports</CardTitle>
            </CardHeader>
            <CardContent>
              {schedulesLoading ? (
                <div>Loading schedules...</div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Format</TableHead>
                      <TableHead>Schedule</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Next Run</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {schedulesData?.schedules?.map(schedule => (
                      <TableRow key={schedule.id}>
                        <TableCell className='font-medium'>
                          {schedule.name}
                        </TableCell>
                        <TableCell>
                          <Badge variant='secondary'>
                            {schedule.format.toUpperCase()}
                          </Badge>
                        </TableCell>
                        <TableCell>{schedule.cron_expression}</TableCell>
                        <TableCell>
                          <Badge
                            variant={schedule.is_active ? 'default' : 'outline'}
                          >
                            {schedule.is_active ? 'Active' : 'Inactive'}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {schedule.next_run_at
                            ? new Date(schedule.next_run_at).toLocaleString()
                            : 'N/A'}
                        </TableCell>
                        <TableCell>
                          <div className='flex space-x-2'>
                            <Button size='sm' variant='outline'>
                              <Play className='h-4 w-4' />
                            </Button>
                            <Button size='sm' variant='outline'>
                              <Edit2 className='h-4 w-4' />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value='exports' className='space-y-4'>
          <Card>
            <CardHeader>
              <CardTitle>Export History</CardTitle>
            </CardHeader>
            <CardContent>
              {exportsLoading ? (
                <div>Loading exports...</div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Format</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Rows</TableHead>
                      <TableHead>Size</TableHead>
                      <TableHead>Created</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {exportsData?.exports?.map(exportItem => (
                      <TableRow key={exportItem.id}>
                        <TableCell>
                          <Badge variant='secondary'>
                            {exportItem.format.toUpperCase()}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {getStatusBadge(exportItem.status)}
                        </TableCell>
                        <TableCell>
                          {exportItem.row_count?.toLocaleString() || 'N/A'}
                        </TableCell>
                        <TableCell>
                          {exportItem.file_size
                            ? `${(exportItem.file_size / 1024 / 1024).toFixed(2)} MB`
                            : 'N/A'}
                        </TableCell>
                        <TableCell>
                          {new Date(exportItem.created_at).toLocaleString()}
                        </TableCell>
                        <TableCell>
                          {exportItem.status === 'completed' &&
                            exportItem.download_url && (
                              <a
                                href={exportItem.download_url}
                                target='_blank'
                                rel='noopener noreferrer'
                              >
                                <Button size='sm' variant='outline'>
                                  <Download className='h-4 w-4' />
                                </Button>
                              </a>
                            )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Report Builder Dialog */}
      <Dialog open={showReportBuilder} onOpenChange={setShowReportBuilder}>
        <DialogContent className='max-w-4xl max-h-[80vh] overflow-y-auto'>
          <DialogHeader>
            <DialogTitle>
              {selectedReport ? 'Edit Report' : 'Create New Report'}
            </DialogTitle>
          </DialogHeader>
          <ReportBuilder
            report={selectedReport || undefined}
            onSave={handleCreateReport}
            onCancel={() => {
              setShowReportBuilder(false);
              setSelectedReport(null);
            }}
          />
        </DialogContent>
      </Dialog>

      {/* Schedule Configuration Dialog */}
      <Dialog open={showScheduleConfig} onOpenChange={setShowScheduleConfig}>
        <DialogContent className='max-w-2xl'>
          <DialogHeader>
            <DialogTitle>Schedule Report</DialogTitle>
          </DialogHeader>
          <ScheduleConfig
            reportId={selectedReport?.id || ''}
            schedule={selectedSchedule || undefined}
            onSave={handleCreateSchedule}
            onCancel={() => {
              setShowScheduleConfig(false);
              setSelectedReport(null);
              setSelectedSchedule(null);
            }}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
}
