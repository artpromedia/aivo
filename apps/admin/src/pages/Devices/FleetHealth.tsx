import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Activity,
  AlertTriangle,
  Bell,
  CheckCircle,
  Clock,
  Plus,
  RefreshCw,
  Server,
  Shield,
  TrendingUp,
  Wifi,
  WifiOff,
  X,
} from 'lucide-react';
import React, { useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

import {
  FleetAPI,
  type AlertRule,
  type AlertRuleRequest,
} from '../../api/fleet';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

export function FleetHealth() {
  const [selectedTab, setSelectedTab] = useState('overview');
  const [timeRange, setTimeRange] = useState('30');
  const [showAlertModal, setShowAlertModal] = useState(false);
  const [editingRule, setEditingRule] = useState<AlertRule | null>(null);

  const queryClient = useQueryClient();

  // Fleet health data
  const {
    data: fleetHealth,
    isLoading: healthLoading,
    error: healthError,
  } = useQuery({
    queryKey: ['fleet-health', timeRange],
    queryFn: () => FleetAPI.getFleetHealth({ rangeDays: parseInt(timeRange) }),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Alert rules data
  const { data: alertRules, isLoading: rulesLoading } = useQuery({
    queryKey: ['alert-rules'],
    queryFn: () => FleetAPI.getAlertRules(),
  });

  // Alert metrics (available options)
  const { data: alertMetrics } = useQuery({
    queryKey: ['alert-metrics'],
    queryFn: () => FleetAPI.getAlertMetrics(),
  });

  // Mutations
  const createRuleMutation = useMutation({
    mutationFn: (data: AlertRuleRequest) => FleetAPI.createAlertRule(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alert-rules'] });
      setShowAlertModal(false);
      setEditingRule(null);
    },
  });

  const updateRuleMutation = useMutation({
    mutationFn: ({
      ruleId,
      data,
    }: {
      ruleId: string;
      data: AlertRuleRequest;
    }) => FleetAPI.updateAlertRule(ruleId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alert-rules'] });
      setShowAlertModal(false);
      setEditingRule(null);
    },
  });

  const deleteRuleMutation = useMutation({
    mutationFn: (ruleId: string) => FleetAPI.deleteAlertRule(ruleId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alert-rules'] });
    },
  });

  const toggleRuleMutation = useMutation({
    mutationFn: ({ ruleId, enabled }: { ruleId: string; enabled: boolean }) =>
      FleetAPI.toggleAlertRule(ruleId, enabled),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alert-rules'] });
    },
  });

  const handleCreateRule = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);

    const ruleData: AlertRuleRequest = {
      name: formData.get('name') as string,
      description: formData.get('description') as string,
      metric: formData.get('metric') as string,
      condition: formData.get('condition') as string,
      threshold: formData.get('threshold') as string,
      window_minutes: parseInt(formData.get('window_minutes') as string),
      actions: (formData.get('actions') as string)
        .split(',')
        .map(a => a.trim()),
      action_config: {
        email_recipients: ['admin@aivo.com'],
        slack_channel: '#alerts',
      },
    };
    if (editingRule) {
      updateRuleMutation.mutate({
        ruleId: editingRule.rule_id,
        data: ruleData,
      });
    } else {
      createRuleMutation.mutate(ruleData);
    }
  };

  const handleDeleteRule = (ruleId: string) => {
    if (window.confirm('Are you sure you want to delete this alert rule?')) {
      deleteRuleMutation.mutate(ruleId);
    }
  };

  const handleToggleRule = (ruleId: string, enabled: boolean) => {
    toggleRuleMutation.mutate({ ruleId, enabled });
  };

  if (healthError) {
    return (
      <div className='flex items-center justify-center h-64'>
        <div className='text-center'>
          <AlertTriangle className='h-12 w-12 text-red-500 mx-auto mb-4' />
          <h3 className='text-lg font-semibold text-gray-900 mb-2'>
            Failed to load fleet health
          </h3>
          <p className='text-gray-600'>
            {healthError instanceof Error
              ? healthError.message
              : 'Unknown error occurred'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className='space-y-6'>
      {/* Header */}
      <div className='flex items-center justify-between'>
        <div>
          <h1 className='text-3xl font-bold tracking-tight'>
            Fleet Health & Alerts
          </h1>
          <p className='text-muted-foreground'>
            Monitor device fleet health and manage alert rules
          </p>
        </div>
        <div className='flex items-center gap-4'>
          <Select
            value={timeRange}
            onChange={e => setTimeRange(e.target.value)}
          >
            <option value='7'>Last 7 days</option>
            <option value='30'>Last 30 days</option>
            <option value='90'>Last 90 days</option>
          </Select>
          <Button
            variant='outline'
            onClick={() =>
              queryClient.invalidateQueries({ queryKey: ['fleet-health'] })
            }
          >
            <RefreshCw className='h-4 w-4 mr-2' />
            Refresh
          </Button>
          <Button onClick={() => setShowAlertModal(true)}>
            <Plus className='h-4 w-4 mr-2' />
            New Alert Rule
          </Button>
        </div>
      </div>

      <Tabs value={selectedTab} onValueChange={setSelectedTab}>
        <TabsList className='grid w-full grid-cols-3'>
          <TabsTrigger value='overview'>Overview</TabsTrigger>
          <TabsTrigger value='alerts'>Alert Rules</TabsTrigger>
          <TabsTrigger value='trends'>Trends</TabsTrigger>
        </TabsList>

        <TabsContent value='overview' className='space-y-6'>
          {/* Key Metrics */}
          {fleetHealth && (
            <>
              <div className='grid grid-cols-1 md:grid-cols-4 gap-4'>
                <Card>
                  <CardContent className='p-4'>
                    <div className='flex items-center gap-3'>
                      <Server className='h-8 w-8 text-blue-500' />
                      <div>
                        <p className='text-sm text-muted-foreground'>
                          Total Devices
                        </p>
                        <p className='text-2xl font-bold'>
                          {fleetHealth.summary.total_devices}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className='p-4'>
                    <div className='flex items-center gap-3'>
                      {fleetHealth.summary.online_percentage >= 95 ? (
                        <CheckCircle className='h-8 w-8 text-green-500' />
                      ) : fleetHealth.summary.online_percentage >= 85 ? (
                        <Wifi className='h-8 w-8 text-yellow-500' />
                      ) : (
                        <WifiOff className='h-8 w-8 text-red-500' />
                      )}
                      <div>
                        <p className='text-sm text-muted-foreground'>Online</p>
                        <p className='text-2xl font-bold'>
                          {fleetHealth.summary.online_percentage.toFixed(1)}%
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className='p-4'>
                    <div className='flex items-center gap-3'>
                      <Activity className='h-8 w-8 text-purple-500' />
                      <div>
                        <p className='text-sm text-muted-foreground'>
                          Avg Heartbeat
                        </p>
                        <p className='text-2xl font-bold'>
                          {fleetHealth.summary.mean_heartbeat_minutes.toFixed(
                            1
                          )}
                          m
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className='p-4'>
                    <div className='flex items-center gap-3'>
                      <Shield className='h-8 w-8 text-orange-500' />
                      <div>
                        <p className='text-sm text-muted-foreground'>
                          FW Versions
                        </p>
                        <p className='text-2xl font-bold'>
                          {fleetHealth.summary.firmware_versions}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Status Distribution */}
              <div className='grid grid-cols-1 lg:grid-cols-2 gap-6'>
                <Card>
                  <CardHeader>
                    <CardTitle>Device Status Distribution</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className='grid grid-cols-2 gap-4'>
                      {Object.entries(fleetHealth.status_distribution).map(
                        ([status, count]) => (
                          <div
                            key={status}
                            className='flex items-center justify-between p-3 bg-gray-50 rounded-lg'
                          >
                            <span className='capitalize font-medium'>
                              {status}
                            </span>
                            <Badge variant='outline'>{count}</Badge>
                          </div>
                        )
                      )}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Firmware Version Distribution</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className='space-y-3'>
                      {fleetHealth.firmware_drift.slice(0, 5).map(item => (
                        <div
                          key={item.version}
                          className='flex items-center justify-between py-2'
                        >
                          <div className='flex items-center space-x-2'>
                            <div className='h-2 w-2 rounded-full bg-blue-400' />
                            <span className='text-sm'>{item.version}</span>
                            {item.is_latest && (
                              <Badge variant='secondary' className='text-xs'>
                                Latest
                              </Badge>
                            )}
                          </div>
                          <div className='text-right'>
                            <div className='text-sm font-medium'>
                              {item.device_count}
                            </div>
                            <div className='text-xs text-muted-foreground'>
                              {item.percentage.toFixed(1)}%
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Alerts */}
              <Card>
                <CardHeader>
                  <CardTitle className='flex items-center gap-2'>
                    <AlertTriangle className='h-5 w-5' />
                    Active Alerts
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {fleetHealth.alerts.critical.length === 0 &&
                  fleetHealth.alerts.warnings.length === 0 ? (
                    <div className='text-center py-8'>
                      <CheckCircle className='h-12 w-12 text-green-500 mx-auto mb-4' />
                      <p className='text-lg font-medium'>All systems healthy</p>
                      <p className='text-muted-foreground'>No active alerts</p>
                    </div>
                  ) : (
                    <div className='space-y-4'>
                      {fleetHealth.alerts.critical.map(alert => (
                        <div
                          key={alert.id}
                          className='p-4 border border-red-200 bg-red-50 rounded-lg'
                        >
                          <div className='flex items-center gap-2'>
                            <AlertTriangle className='h-5 w-5 text-red-500' />
                            <span className='font-medium text-red-800'>
                              {alert.message}
                            </span>
                          </div>
                        </div>
                      ))}
                      {fleetHealth.alerts.warnings.map(alert => (
                        <div
                          key={alert.id}
                          className='p-4 border border-yellow-200 bg-yellow-50 rounded-lg'
                        >
                          <div className='flex items-center gap-2'>
                            <Clock className='h-5 w-5 text-yellow-500' />
                            <span className='font-medium text-yellow-800'>
                              {alert.message}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </>
          )}

          {healthLoading && (
            <div className='flex items-center justify-center h-64'>
              <RefreshCw className='h-6 w-6 animate-spin mr-2' />
              Loading fleet health...
            </div>
          )}
        </TabsContent>

        <TabsContent value='alerts' className='space-y-6'>
          <Card>
            <CardHeader>
              <CardTitle>Alert Rules</CardTitle>
            </CardHeader>
            <CardContent>
              {rulesLoading ? (
                <div className='flex items-center justify-center h-32'>
                  <RefreshCw className='h-6 w-6 animate-spin mr-2' />
                  Loading alert rules...
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Metric</TableHead>
                      <TableHead>Condition</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Triggered</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {alertRules?.rules.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={6} className='text-center py-8'>
                          <Bell className='h-12 w-12 text-muted-foreground mx-auto mb-4' />
                          <p className='text-lg font-medium'>
                            No alert rules configured
                          </p>
                          <p className='text-muted-foreground'>
                            Create your first alert rule to monitor fleet health
                          </p>
                        </TableCell>
                      </TableRow>
                    ) : (
                      alertRules?.rules.map((rule: AlertRule) => (
                        <TableRow key={rule.rule_id}>
                          <TableCell>
                            <div>
                              <p className='font-medium'>{rule.name}</p>
                              <p className='text-sm text-muted-foreground'>
                                {rule.description}
                              </p>
                            </div>
                          </TableCell>
                          <TableCell>
                            <code className='text-sm'>{rule.metric}</code>
                          </TableCell>
                          <TableCell>
                            <span className='text-sm'>
                              {rule.condition} {rule.threshold}
                            </span>
                          </TableCell>
                          <TableCell>
                            <Badge
                              variant={
                                rule.is_enabled ? 'default' : 'secondary'
                              }
                            >
                              {rule.is_enabled ? 'Enabled' : 'Disabled'}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <div className='text-sm'>
                              <p>{rule.trigger_count} times</p>
                              {rule.last_triggered_at && (
                                <p className='text-muted-foreground'>
                                  Last:{' '}
                                  {new Date(
                                    rule.last_triggered_at
                                  ).toLocaleDateString()}
                                </p>
                              )}
                            </div>
                          </TableCell>
                          <TableCell>
                            <div className='flex items-center gap-2'>
                              <Button
                                size='sm'
                                variant='outline'
                                onClick={() =>
                                  handleToggleRule(
                                    rule.rule_id,
                                    !rule.is_enabled
                                  )
                                }
                              >
                                {rule.is_enabled ? 'Disable' : 'Enable'}
                              </Button>
                              <Button
                                size='sm'
                                variant='outline'
                                onClick={() => {
                                  setEditingRule(rule);
                                  setShowAlertModal(true);
                                }}
                              >
                                Edit
                              </Button>
                              <Button
                                size='sm'
                                variant='destructive'
                                onClick={() => handleDeleteRule(rule.rule_id)}
                              >
                                Delete
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value='trends' className='space-y-6'>
          {fleetHealth && (
            <Card>
              <CardHeader>
                <CardTitle>Fleet Health Trends</CardTitle>
              </CardHeader>
              <CardContent>
                {fleetHealth.health_trends.length > 0 ? (
                  <div style={{ width: '100%', height: 300 }}>
                    <ResponsiveContainer>
                      <LineChart data={fleetHealth.health_trends}>
                        <CartesianGrid strokeDasharray='3 3' />
                        <XAxis dataKey='date' />
                        <YAxis />
                        <Tooltip />
                        <Line
                          type='monotone'
                          dataKey='online_percentage'
                          stroke='#8884d8'
                          strokeWidth={2}
                          name='Online %'
                        />
                        <Line
                          type='monotone'
                          dataKey='total_devices'
                          stroke='#82ca9d'
                          strokeWidth={2}
                          name='Total Devices'
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <div className='text-center py-8'>
                    <TrendingUp className='h-12 w-12 text-muted-foreground mx-auto mb-4' />
                    <p className='text-lg font-medium'>
                      No trend data available
                    </p>
                    <p className='text-muted-foreground'>
                      Trends will appear as data is collected
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>

      {/* Alert Rule Modal */}
      {showAlertModal && (
        <div className='fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50'>
          <Card className='w-full max-w-2xl'>
            <CardHeader>
              <div className='flex items-center justify-between'>
                <CardTitle>
                  {editingRule ? 'Edit Alert Rule' : 'Create Alert Rule'}
                </CardTitle>
                <Button
                  variant='ghost'
                  size='sm'
                  onClick={() => {
                    setShowAlertModal(false);
                    setEditingRule(null);
                  }}
                >
                  <X className='h-4 w-4' />
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleCreateRule} className='space-y-4'>
                <div className='grid grid-cols-2 gap-4'>
                  <div>
                    <label className='block text-sm font-medium mb-2'>
                      Name
                    </label>
                    <Input
                      name='name'
                      required
                      defaultValue={editingRule?.name}
                      placeholder='Alert rule name'
                    />
                  </div>
                  <div>
                    <label className='block text-sm font-medium mb-2'>
                      Metric
                    </label>
                    <Select
                      name='metric'
                      required
                      defaultValue={editingRule?.metric}
                    >
                      <option value=''>Select metric</option>
                      {alertMetrics?.metrics.map(metric => (
                        <option key={metric.key} value={metric.key}>
                          {metric.name}
                        </option>
                      ))}
                    </Select>
                  </div>
                </div>

                <div>
                  <label className='block text-sm font-medium mb-2'>
                    Description
                  </label>
                  <Input
                    name='description'
                    defaultValue={editingRule?.description}
                    placeholder='Alert rule description'
                  />
                </div>

                <div className='grid grid-cols-3 gap-4'>
                  <div>
                    <label className='block text-sm font-medium mb-2'>
                      Condition
                    </label>
                    <Select
                      name='condition'
                      required
                      defaultValue={editingRule?.condition}
                    >
                      <option value=''>Select condition</option>
                      {alertMetrics?.conditions.map(condition => (
                        <option key={condition.key} value={condition.key}>
                          {condition.name}
                        </option>
                      ))}
                    </Select>
                  </div>
                  <div>
                    <label className='block text-sm font-medium mb-2'>
                      Threshold
                    </label>
                    <Input
                      name='threshold'
                      required
                      defaultValue={editingRule?.threshold}
                      placeholder='Threshold value'
                    />
                  </div>
                  <div>
                    <label className='block text-sm font-medium mb-2'>
                      Window (min)
                    </label>
                    <Input
                      name='window_minutes'
                      type='number'
                      required
                      defaultValue={editingRule?.window_minutes || 15}
                      min='1'
                      max='1440'
                    />
                  </div>
                </div>

                <div>
                  <label className='block text-sm font-medium mb-2'>
                    Actions
                  </label>
                  <Select name='actions' required multiple>
                    {alertMetrics?.actions.map(action => (
                      <option key={action.key} value={action.key}>
                        {action.name}
                      </option>
                    ))}
                  </Select>
                  <p className='text-sm text-muted-foreground mt-1'>
                    Hold Ctrl/Cmd to select multiple actions
                  </p>
                </div>

                <div className='flex justify-end gap-2'>
                  <Button
                    type='button'
                    variant='outline'
                    onClick={() => {
                      setShowAlertModal(false);
                      setEditingRule(null);
                    }}
                  >
                    Cancel
                  </Button>
                  <Button
                    type='submit'
                    disabled={
                      createRuleMutation.isPending ||
                      updateRuleMutation.isPending
                    }
                  >
                    {editingRule ? 'Update Rule' : 'Create Rule'}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
