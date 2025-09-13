import React, { useState, useEffect } from 'react';

import {
  integrationHubAPI,
  type ConnectorConfig,
  type Integration,
  type ConnectionLog,
  type IntegrationTest,
  type ConnectorTypeValue,
  type ConnectionStatus,
  type LogLevel,
  type IntegrationCreateData,
  type ConnectRequest,
} from '@/api/integrations';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
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

const CONNECTOR_ICONS: Record<ConnectorTypeValue, string> = {
  google_classroom: '🎓',
  canvas_lti: '📚',
  zoom_lti: '📹',
  clever: '🎯',
  oneroster: '📊',
};

const STATUS_COLORS: Record<ConnectionStatus, string> = {
  disconnected: 'bg-gray-500',
  connecting: 'bg-yellow-500',
  connected: 'bg-green-500',
  error: 'bg-red-500',
  expired: 'bg-orange-500',
};

const LOG_LEVEL_COLORS: Record<LogLevel, string> = {
  debug: 'bg-gray-500',
  info: 'bg-blue-500',
  warning: 'bg-yellow-500',
  error: 'bg-red-500',
};

const Hub: React.FC = () => {
  const [connectorTypes, setConnectorTypes] = useState<ConnectorConfig[]>([]);
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [selectedIntegration, setSelectedIntegration] =
    useState<Integration | null>(null);
  const [logs, setLogs] = useState<ConnectionLog[]>([]);
  const [tests, setTests] = useState<IntegrationTest[]>([]);
  const [loading, setLoading] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showConnectForm, setShowConnectForm] = useState(false);
  const [showLogs, setShowLogs] = useState(false);
  const [showTests, setShowTests] = useState(false);
  const [message, setMessage] = useState<{
    text: string;
    type: 'success' | 'error';
  } | null>(null);

  // Form states
  const [newIntegration, setNewIntegration] = useState<IntegrationCreateData>({
    name: '',
    description: '',
    connector_type: 'google_classroom',
    config: {},
  });
  const [connectConfig, setConnectConfig] = useState<Record<string, string>>(
    {}
  );

  useEffect(() => {
    loadConnectorTypes();
    loadIntegrations();
  }, []);

  const loadConnectorTypes = async () => {
    try {
      setLoading(true);
      const types = await integrationHubAPI.getConnectorTypes();
      setConnectorTypes(types);
    } catch (err) {
      setMessage({
        text:
          err instanceof Error ? err.message : 'Failed to load connector types',
        type: 'error',
      });
    } finally {
      setLoading(false);
    }
  };

  const loadIntegrations = async () => {
    try {
      setLoading(true);
      const response = await integrationHubAPI.getIntegrations();
      setIntegrations(response.integrations);
    } catch {
      setMessage({ text: 'Failed to load integrations', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const createIntegration = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      await integrationHubAPI.createIntegration(newIntegration);
      setMessage({ text: 'Integration created successfully', type: 'success' });
      setShowCreateForm(false);
      setNewIntegration({
        name: '',
        description: '',
        connector_type: 'google_classroom',
        config: {},
      });
      await loadIntegrations();
    } catch {
      setMessage({ text: 'Failed to create integration', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const connectIntegration = async (integration: Integration) => {
    if (!selectedIntegration) return;

    try {
      setLoading(true);
      const connectData: ConnectRequest = {
        config: connectConfig,
        test_connection: true,
      };

      const response = await integrationHubAPI.connectIntegration(
        integration.id,
        connectData
      );

      if (response.oauth_url) {
        // Open OAuth URL in new window
        window.open(response.oauth_url, '_blank', 'width=600,height=600');
        setMessage({
          text: 'Please complete OAuth authorization in the new window',
          type: 'success',
        });
      } else {
        setMessage({ text: response.message, type: 'success' });
      }

      setShowConnectForm(false);
      setConnectConfig({});
      await loadIntegrations();
    } catch {
      setMessage({ text: 'Failed to connect integration', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const testConnection = async (integration: Integration) => {
    try {
      setLoading(true);
      const response = await integrationHubAPI.testConnection(integration.id, {
        test_types: ['connection', 'auth'],
      });
      setMessage({
        text: response.overall_message,
        type: response.success ? 'success' : 'error',
      });
      await loadIntegrations();
    } catch {
      setMessage({ text: 'Failed to test connection', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const loadLogs = async (integration: Integration) => {
    try {
      setLoading(true);
      const response = await integrationHubAPI.getIntegrationLogs(
        integration.id,
        { size: 20 }
      );
      setLogs(response.logs);
      setSelectedIntegration(integration);
      setShowLogs(true);
    } catch {
      setMessage({ text: 'Failed to load logs', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const loadTests = async (integration: Integration) => {
    try {
      setLoading(true);
      const response = await integrationHubAPI.getIntegrationTests(
        integration.id,
        { size: 10 }
      );
      setTests(response.tests);
      setSelectedIntegration(integration);
      setShowTests(true);
    } catch {
      setMessage({ text: 'Failed to load tests', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const renderConfigFields = (connectorConfig: ConnectorConfig) => {
    const schema = connectorConfig.config_schema;
    if (!schema?.properties) return null;

    return Object.entries(schema.properties).map(
      ([key, fieldSchema]: [string, Record<string, unknown>]) => (
        <div key={key} className='space-y-2'>
          <Label htmlFor={key}>
            {(fieldSchema.description as string) || key}
            {Array.isArray(schema.required) &&
              schema.required.includes(key) && (
                <span className='text-red-500'>*</span>
              )}
          </Label>
          {fieldSchema.enum ? (
            <Select
              value={connectConfig[key] || ''}
              onValueChange={value =>
                setConnectConfig(prev => ({ ...prev, [key]: value }))
              }
            >
              <SelectTrigger>
                <SelectValue
                  placeholder={`Select ${(fieldSchema.description as string) || key}`}
                />
              </SelectTrigger>
              <SelectContent>
                {(fieldSchema.enum as string[]).map((option: string) => (
                  <SelectItem key={option} value={option}>
                    {option}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          ) : (
            <Input
              id={key}
              type={
                fieldSchema.type === 'string'
                  ? 'text'
                  : (fieldSchema.type as string)
              }
              placeholder={(fieldSchema.description as string) || key}
              value={connectConfig[key] || ''}
              onChange={e =>
                setConnectConfig(prev => ({ ...prev, [key]: e.target.value }))
              }
              required={
                Array.isArray(schema.required) && schema.required.includes(key)
              }
            />
          )}
        </div>
      )
    );
  };

  return (
    <div className='space-y-6'>
      <div className='flex justify-between items-center'>
        <div>
          <h1 className='text-3xl font-bold'>Integrations Hub</h1>
          <p className='text-gray-600'>
            Manage your LMS, Zoom, and Roster integrations
          </p>
        </div>
        <Dialog open={showCreateForm} onOpenChange={setShowCreateForm}>
          <DialogTrigger>
            <Button>Add Integration</Button>
          </DialogTrigger>
          <DialogContent className='max-w-md'>
            <DialogHeader>
              <DialogTitle>Create New Integration</DialogTitle>
              <DialogDescription>
                Add a new integration connector to your workspace.
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={createIntegration} className='space-y-4'>
              <div className='space-y-2'>
                <Label htmlFor='name'>Name*</Label>
                <Input
                  id='name'
                  value={newIntegration.name}
                  onChange={e =>
                    setNewIntegration(prev => ({
                      ...prev,
                      name: e.target.value,
                    }))
                  }
                  placeholder='My Integration'
                  required
                />
              </div>

              <div className='space-y-2'>
                <Label htmlFor='description'>Description</Label>
                <Input
                  id='description'
                  value={newIntegration.description || ''}
                  onChange={e =>
                    setNewIntegration(prev => ({
                      ...prev,
                      description: e.target.value,
                    }))
                  }
                  placeholder='Optional description'
                />
              </div>

              <div className='space-y-2'>
                <Label htmlFor='connector_type'>Connector Type*</Label>
                <Select
                  value={newIntegration.connector_type}
                  onValueChange={value =>
                    setNewIntegration(prev => ({
                      ...prev,
                      connector_type: value as ConnectorTypeValue,
                    }))
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {connectorTypes.map(type => (
                      <SelectItem
                        key={type.connector_type}
                        value={type.connector_type}
                      >
                        {CONNECTOR_ICONS[type.connector_type]}{' '}
                        {type.display_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className='flex justify-end space-x-2'>
                <Button
                  type='button'
                  variant='outline'
                  onClick={() => setShowCreateForm(false)}
                >
                  Cancel
                </Button>
                <Button type='submit' disabled={loading}>
                  {loading ? 'Creating...' : 'Create'}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {message && (
        <Alert
          className={
            message.type === 'error'
              ? 'border-red-500 bg-red-50'
              : 'border-green-500 bg-green-50'
          }
        >
          <AlertDescription
            className={
              message.type === 'error' ? 'text-red-700' : 'text-green-700'
            }
          >
            {message.text}
          </AlertDescription>
        </Alert>
      )}

      {/* Available Connectors */}
      <div className='space-y-4'>
        <h2 className='text-xl font-semibold'>Available Connectors</h2>
        <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4'>
          {connectorTypes.map(connector => (
            <Card key={connector.connector_type} className='h-full'>
              <CardHeader>
                <CardTitle className='flex items-center space-x-2'>
                  <span>{CONNECTOR_ICONS[connector.connector_type]}</span>
                  <span>{connector.display_name}</span>
                </CardTitle>
                <CardDescription>{connector.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className='space-y-2'>
                  <div className='flex items-center space-x-2'>
                    <Badge
                      variant={connector.is_enabled ? 'default' : 'secondary'}
                    >
                      {connector.is_enabled ? 'Enabled' : 'Disabled'}
                    </Badge>
                    {connector.oauth_provider && (
                      <Badge variant='outline'>OAuth</Badge>
                    )}
                  </div>
                  {connector.documentation_url && (
                    <a
                      href={connector.documentation_url}
                      target='_blank'
                      rel='noopener noreferrer'
                      className='text-blue-600 hover:underline text-sm'
                    >
                      View Documentation
                    </a>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Active Integrations */}
      <div className='space-y-4'>
        <h2 className='text-xl font-semibold'>Active Integrations</h2>
        {integrations.length === 0 ? (
          <Card>
            <CardContent className='text-center py-8'>
              <p className='text-gray-500'>
                No integrations configured yet. Create your first integration
                above.
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className='grid grid-cols-1 lg:grid-cols-2 gap-4'>
            {integrations.map(integration => (
              <Card key={integration.id}>
                <CardHeader>
                  <CardTitle className='flex items-center justify-between'>
                    <div className='flex items-center space-x-2'>
                      <span>{CONNECTOR_ICONS[integration.connector_type]}</span>
                      <span>{integration.name}</span>
                    </div>
                    <Badge className={STATUS_COLORS[integration.status]}>
                      {integration.status}
                    </Badge>
                  </CardTitle>
                  <CardDescription>
                    {integration.description ||
                      `${integration.connector_type} integration`}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className='space-y-3'>
                    <div className='grid grid-cols-2 gap-4 text-sm'>
                      <div>
                        <span className='font-medium'>Last Connected:</span>
                        <div className='text-gray-600'>
                          {integration.last_connected_at
                            ? new Date(
                                integration.last_connected_at
                              ).toLocaleDateString()
                            : 'Never'}
                        </div>
                      </div>
                      <div>
                        <span className='font-medium'>Requests Today:</span>
                        <div className='text-gray-600'>
                          {integration.requests_today}
                        </div>
                      </div>
                    </div>

                    {integration.last_error_message && (
                      <Alert className='border-red-500 bg-red-50'>
                        <AlertDescription className='text-red-700 text-sm'>
                          {integration.last_error_message}
                        </AlertDescription>
                      </Alert>
                    )}

                    <div className='flex flex-wrap gap-2'>
                      {integration.status === 'disconnected' && (
                        <Dialog
                          open={
                            showConnectForm &&
                            selectedIntegration?.id === integration.id
                          }
                          onOpenChange={open => {
                            setShowConnectForm(open);
                            if (open) {
                              setSelectedIntegration(integration);
                              setConnectConfig({});
                            }
                          }}
                        >
                          <DialogTrigger>
                            <Button size='sm'>Connect</Button>
                          </DialogTrigger>
                          <DialogContent>
                            <DialogHeader>
                              <DialogTitle>
                                Connect {integration.name}
                              </DialogTitle>
                              <DialogDescription>
                                Configure connection settings for your{' '}
                                {integration.connector_type} integration.
                              </DialogDescription>
                            </DialogHeader>
                            <div className='space-y-4'>
                              {connectorTypes.find(
                                type =>
                                  type.connector_type ===
                                  integration.connector_type
                              ) &&
                                renderConfigFields(
                                  connectorTypes.find(
                                    type =>
                                      type.connector_type ===
                                      integration.connector_type
                                  )!
                                )}
                              <div className='flex justify-end space-x-2'>
                                <Button
                                  variant='outline'
                                  onClick={() => setShowConnectForm(false)}
                                >
                                  Cancel
                                </Button>
                                <Button
                                  onClick={() =>
                                    connectIntegration(integration)
                                  }
                                  disabled={loading}
                                >
                                  {loading ? 'Connecting...' : 'Connect'}
                                </Button>
                              </div>
                            </div>
                          </DialogContent>
                        </Dialog>
                      )}

                      <Button
                        size='sm'
                        variant='outline'
                        onClick={() => testConnection(integration)}
                        disabled={loading}
                      >
                        Test Connection
                      </Button>

                      <Button
                        size='sm'
                        variant='outline'
                        onClick={() => loadLogs(integration)}
                      >
                        View Logs
                      </Button>

                      <Button
                        size='sm'
                        variant='outline'
                        onClick={() => loadTests(integration)}
                      >
                        Test Results
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Logs Dialog */}
      <Dialog open={showLogs} onOpenChange={setShowLogs}>
        <DialogContent className='max-w-4xl max-h-[80vh] overflow-y-auto'>
          <DialogHeader>
            <DialogTitle>
              Connection Logs - {selectedIntegration?.name}
            </DialogTitle>
            <DialogDescription>
              Recent connection activity and error logs
            </DialogDescription>
          </DialogHeader>
          <div className='space-y-2'>
            {logs.map(log => (
              <div
                key={log.id}
                className='flex items-start space-x-3 p-3 border rounded'
              >
                <Badge className={LOG_LEVEL_COLORS[log.level]}>
                  {log.level}
                </Badge>
                <div className='flex-1 min-w-0'>
                  <div className='text-sm font-medium'>{log.message}</div>
                  {log.operation && (
                    <div className='text-xs text-gray-500'>
                      Operation: {log.operation}
                    </div>
                  )}
                  <div className='text-xs text-gray-500'>
                    {new Date(log.created_at).toLocaleString()}
                    {log.duration_ms && ` • ${log.duration_ms}ms`}
                  </div>
                  {log.details && (
                    <pre className='text-xs text-gray-600 mt-1 overflow-x-auto'>
                      {JSON.stringify(log.details, null, 2)}
                    </pre>
                  )}
                </div>
              </div>
            ))}
          </div>
        </DialogContent>
      </Dialog>

      {/* Tests Dialog */}
      <Dialog open={showTests} onOpenChange={setShowTests}>
        <DialogContent className='max-w-3xl max-h-[80vh] overflow-y-auto'>
          <DialogHeader>
            <DialogTitle>
              Test Results - {selectedIntegration?.name}
            </DialogTitle>
            <DialogDescription>
              Recent connection test results and diagnostics
            </DialogDescription>
          </DialogHeader>
          <div className='space-y-2'>
            {tests.map(test => (
              <div
                key={test.id}
                className='flex items-start space-x-3 p-3 border rounded'
              >
                <Badge className={test.success ? 'bg-green-500' : 'bg-red-500'}>
                  {test.success ? '✓' : '✗'}
                </Badge>
                <div className='flex-1 min-w-0'>
                  <div className='text-sm font-medium'>{test.test_name}</div>
                  <div className='text-xs text-gray-500'>
                    Type: {test.test_type}
                  </div>
                  {test.message && (
                    <div className='text-sm text-gray-700 mt-1'>
                      {test.message}
                    </div>
                  )}
                  {test.error_message && (
                    <div className='text-sm text-red-600 mt-1'>
                      {test.error_message}
                    </div>
                  )}
                  <div className='text-xs text-gray-500 mt-1'>
                    {new Date(test.created_at).toLocaleString()}
                    {test.duration_ms && ` • ${test.duration_ms}ms`}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Hub;
