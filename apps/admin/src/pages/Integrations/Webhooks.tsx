import React, { useState, useEffect } from 'react';

interface Webhook {
  id: string;
  tenant_id: string;
  name: string;
  description?: string;
  url: string;
  secret_key: string;
  events: string[];
  is_active: boolean;
  max_retries: number;
  retry_delay_seconds: number;
  created_at: string;
  updated_at: string;
  created_by?: string;
}

interface WebhookCreateData {
  name: string;
  description?: string;
  url: string;
  events: string[];
  max_retries?: number;
  retry_delay_seconds?: number;
}

interface WebhookDelivery {
  id: string;
  webhook_id: string;
  event_type: string;
  status: 'pending' | 'delivered' | 'failed' | 'dead_letter';
  payload: Record<string, unknown>;
  response_status?: number;
  response_body?: string;
  attempts: number;
  next_retry_at?: string;
  delivered_at?: string;
  created_at: string;
}

interface WebhookTestData {
  event_type: string;
  payload: Record<string, unknown>;
}

const AVAILABLE_EVENTS = [
  'user.created',
  'user.updated',
  'user.deleted',
  'api_key.created',
  'api_key.rotated',
  'api_key.deleted',
  'webhook.created',
  'webhook.updated',
  'webhook.deleted',
];

const Webhooks: React.FC = () => {
  const [webhooks, setWebhooks] = useState<Webhook[]>([]);
  const [loading, setLoading] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showTestForm, setShowTestForm] = useState(false);
  const [selectedWebhook, setSelectedWebhook] = useState<Webhook | null>(null);
  const [selectedDeliveries, setSelectedDeliveries] = useState<
    WebhookDelivery[]
  >([]);
  const [showDeliveries, setShowDeliveries] = useState(false);
  const [newWebhook, setNewWebhook] = useState<WebhookCreateData>({
    name: '',
    description: '',
    url: '',
    events: ['user.created'],
    max_retries: 3,
    retry_delay_seconds: 5,
  });
  const [testData, setTestData] = useState<WebhookTestData>({
    event_type: 'user.created',
    payload: {
      user_id: 'user-123',
      email: 'test@example.com',
      name: 'Test User',
    },
  });
  const [message, setMessage] = useState<{
    text: string;
    type: 'success' | 'error' | 'info';
  } | null>(null);

  // Mock tenant ID - replace with actual tenant selection
  const tenantId = 'tenant-123';

  useEffect(() => {
    fetchWebhooks();
  }, []);

  const fetchWebhooks = async (): Promise<void> => {
    setLoading(true);
    try {
      // Mock API call - replace with actual API integration
      const response = await fetch(`/api/v1/tenants/${tenantId}/webhooks`);
      if (response.ok) {
        const data = await response.json();
        setWebhooks(data.webhooks);
      } else {
        throw new Error('Failed to fetch webhooks');
      }
    } catch {
      setMessage({ text: 'Failed to load webhooks', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const fetchWebhookDeliveries = async (webhookId: string): Promise<void> => {
    try {
      const response = await fetch(
        `/api/v1/tenants/${tenantId}/webhooks/${webhookId}/deliveries`
      );
      if (response.ok) {
        const data = await response.json();
        setSelectedDeliveries(data.deliveries);
        setShowDeliveries(true);
      } else {
        throw new Error('Failed to fetch deliveries');
      }
    } catch {
      setMessage({ text: 'Failed to load webhook deliveries', type: 'error' });
    }
  };

  const handleCreateWebhook = async (): Promise<void> => {
    try {
      const response = await fetch(`/api/v1/tenants/${tenantId}/webhooks`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newWebhook),
      });

      if (response.ok) {
        const data: Webhook = await response.json();
        setWebhooks([data, ...webhooks]);
        setShowCreateForm(false);
        setNewWebhook({
          name: '',
          description: '',
          url: '',
          events: ['user.created'],
          max_retries: 3,
          retry_delay_seconds: 5,
        });
        setMessage({ text: 'Webhook created successfully', type: 'success' });
      } else {
        throw new Error('Failed to create webhook');
      }
    } catch {
      setMessage({ text: 'Failed to create webhook', type: 'error' });
    }
  };

  const handleTestWebhook = async (): Promise<void> => {
    if (!selectedWebhook) return;

    try {
      const response = await fetch(
        `/api/v1/tenants/${tenantId}/webhooks/${selectedWebhook.id}/test`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(testData),
        }
      );

      if (response.ok) {
        const data = await response.json();
        setMessage({
          text: `Test webhook sent successfully. Delivery ID: ${data.delivery_id}`,
          type: 'success',
        });
        setShowTestForm(false);
      } else {
        throw new Error('Failed to test webhook');
      }
    } catch {
      setMessage({ text: 'Failed to test webhook', type: 'error' });
    }
  };

  const handleReplayDelivery = async (
    delivery: WebhookDelivery
  ): Promise<void> => {
    try {
      const response = await fetch(
        `/api/v1/tenants/${tenantId}/webhook-deliveries/${delivery.id}/replay`,
        {
          method: 'POST',
        }
      );

      if (response.ok) {
        setMessage({
          text: 'Webhook delivery replayed successfully',
          type: 'success',
        });
        // Refresh deliveries
        if (selectedWebhook) {
          fetchWebhookDeliveries(selectedWebhook.id);
        }
      } else {
        throw new Error('Failed to replay delivery');
      }
    } catch {
      setMessage({ text: 'Failed to replay webhook delivery', type: 'error' });
    }
  };

  const handleDeleteWebhook = async (webhook: Webhook): Promise<void> => {
    if (!confirm(`Are you sure you want to delete "${webhook.name}"?`)) {
      return;
    }

    try {
      const response = await fetch(
        `/api/v1/tenants/${tenantId}/webhooks/${webhook.id}`,
        {
          method: 'DELETE',
        }
      );

      if (response.ok) {
        setWebhooks(webhooks.filter(w => w.id !== webhook.id));
        setMessage({ text: 'Webhook deleted successfully', type: 'success' });
      } else {
        throw new Error('Failed to delete webhook');
      }
    } catch {
      setMessage({ text: 'Failed to delete webhook', type: 'error' });
    }
  };

  const toggleWebhookStatus = async (webhook: Webhook): Promise<void> => {
    try {
      const response = await fetch(
        `/api/v1/tenants/${tenantId}/webhooks/${webhook.id}`,
        {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ is_active: !webhook.is_active }),
        }
      );

      if (response.ok) {
        const updatedWebhook: Webhook = await response.json();
        setWebhooks(
          webhooks.map(w => (w.id === webhook.id ? updatedWebhook : w))
        );
        setMessage({
          text: `Webhook ${updatedWebhook.is_active ? 'enabled' : 'disabled'} successfully`,
          type: 'success',
        });
      } else {
        throw new Error('Failed to update webhook');
      }
    } catch {
      setMessage({ text: 'Failed to update webhook status', type: 'error' });
    }
  };

  const formatDate = (dateString?: string): string => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleDateString();
  };

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'delivered':
        return '#10b981';
      case 'failed':
        return '#ef4444';
      case 'pending':
        return '#f59e0b';
      case 'dead_letter':
        return '#6b7280';
      default:
        return '#6b7280';
    }
  };

  const getStatusIcon = (status: string): string => {
    switch (status) {
      case 'delivered':
        return '✅';
      case 'failed':
        return '❌';
      case 'pending':
        return '⏳';
      case 'dead_letter':
        return '💀';
      default:
        return '❓';
    }
  };

  return (
    <div style={{ padding: '24px' }}>
      <div
        style={{
          backgroundColor: 'white',
          borderRadius: '8px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
        }}
      >
        <div
          style={{
            padding: '16px',
            borderBottom: '1px solid #e5e7eb',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <h2 style={{ margin: 0, fontSize: '24px', fontWeight: '600' }}>
            🪝 Webhooks
          </h2>
          <div style={{ display: 'flex', gap: '12px' }}>
            <button
              onClick={fetchWebhooks}
              disabled={loading}
              style={{
                padding: '8px 16px',
                border: '1px solid #d1d5db',
                backgroundColor: 'white',
                borderRadius: '6px',
                cursor: loading ? 'not-allowed' : 'pointer',
              }}
            >
              🔄 Refresh
            </button>
            <button
              onClick={() => setShowCreateForm(true)}
              style={{
                padding: '8px 16px',
                border: 'none',
                backgroundColor: '#3b82f6',
                color: 'white',
                borderRadius: '6px',
                cursor: 'pointer',
              }}
            >
              ➕ Create Webhook
            </button>
          </div>
        </div>

        {message && (
          <div
            style={{
              padding: '12px 16px',
              backgroundColor:
                message.type === 'success'
                  ? '#dcfce7'
                  : message.type === 'error'
                    ? '#fef2f2'
                    : '#f0f9ff',
              color:
                message.type === 'success'
                  ? '#166534'
                  : message.type === 'error'
                    ? '#991b1b'
                    : '#1e40af',
              borderBottom: '1px solid #e5e7eb',
            }}
          >
            {message.text}
          </div>
        )}

        <div style={{ padding: '16px' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #e5e7eb' }}>
                <th
                  style={{
                    textAlign: 'left',
                    padding: '12px 8px',
                    fontWeight: '600',
                  }}
                >
                  Name
                </th>
                <th
                  style={{
                    textAlign: 'left',
                    padding: '12px 8px',
                    fontWeight: '600',
                  }}
                >
                  URL
                </th>
                <th
                  style={{
                    textAlign: 'left',
                    padding: '12px 8px',
                    fontWeight: '600',
                  }}
                >
                  Events
                </th>
                <th
                  style={{
                    textAlign: 'left',
                    padding: '12px 8px',
                    fontWeight: '600',
                  }}
                >
                  Status
                </th>
                <th
                  style={{
                    textAlign: 'left',
                    padding: '12px 8px',
                    fontWeight: '600',
                  }}
                >
                  Retries
                </th>
                <th
                  style={{
                    textAlign: 'left',
                    padding: '12px 8px',
                    fontWeight: '600',
                  }}
                >
                  Created
                </th>
                <th
                  style={{
                    textAlign: 'left',
                    padding: '12px 8px',
                    fontWeight: '600',
                  }}
                >
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {webhooks.map(webhook => (
                <tr
                  key={webhook.id}
                  style={{ borderBottom: '1px solid #f3f4f6' }}
                >
                  <td style={{ padding: '12px 8px' }}>
                    <div>
                      <div style={{ fontWeight: '500' }}>{webhook.name}</div>
                      {webhook.description && (
                        <div style={{ fontSize: '14px', color: '#6b7280' }}>
                          {webhook.description}
                        </div>
                      )}
                    </div>
                  </td>
                  <td style={{ padding: '12px 8px' }}>
                    <span style={{ fontFamily: 'monospace', fontSize: '14px' }}>
                      {webhook.url}
                    </span>
                  </td>
                  <td style={{ padding: '12px 8px' }}>
                    <div
                      style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}
                    >
                      {webhook.events.slice(0, 2).map(event => (
                        <span
                          key={event}
                          style={{
                            padding: '2px 8px',
                            backgroundColor: '#f3f4f6',
                            borderRadius: '12px',
                            fontSize: '12px',
                          }}
                        >
                          {event}
                        </span>
                      ))}
                      {webhook.events.length > 2 && (
                        <span
                          style={{
                            padding: '2px 8px',
                            backgroundColor: '#e5e7eb',
                            borderRadius: '12px',
                            fontSize: '12px',
                          }}
                        >
                          +{webhook.events.length - 2} more
                        </span>
                      )}
                    </div>
                  </td>
                  <td style={{ padding: '12px 8px' }}>
                    <span
                      style={{
                        padding: '4px 8px',
                        borderRadius: '12px',
                        fontSize: '12px',
                        backgroundColor: webhook.is_active
                          ? '#dcfce7'
                          : '#fef2f2',
                        color: webhook.is_active ? '#166534' : '#991b1b',
                        fontWeight: '500',
                      }}
                    >
                      {webhook.is_active ? '🟢 Active' : '🔴 Inactive'}
                    </span>
                  </td>
                  <td style={{ padding: '12px 8px' }}>
                    <div style={{ fontSize: '14px' }}>
                      Max: {webhook.max_retries}
                    </div>
                    <div style={{ fontSize: '12px', color: '#6b7280' }}>
                      Delay: {webhook.retry_delay_seconds}s
                    </div>
                  </td>
                  <td style={{ padding: '12px 8px' }}>
                    <div style={{ fontSize: '14px' }}>
                      {formatDate(webhook.created_at)}
                    </div>
                  </td>
                  <td style={{ padding: '12px 8px' }}>
                    <div
                      style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}
                    >
                      <button
                        onClick={() => {
                          setSelectedWebhook(webhook);
                          setShowTestForm(true);
                        }}
                        style={{
                          background: 'none',
                          border: '1px solid #10b981',
                          borderRadius: '4px',
                          padding: '4px 8px',
                          cursor: 'pointer',
                          color: '#10b981',
                          fontSize: '12px',
                        }}
                      >
                        🧪 Test
                      </button>
                      <button
                        onClick={() => fetchWebhookDeliveries(webhook.id)}
                        style={{
                          background: 'none',
                          border: '1px solid #3b82f6',
                          borderRadius: '4px',
                          padding: '4px 8px',
                          cursor: 'pointer',
                          color: '#3b82f6',
                          fontSize: '12px',
                        }}
                      >
                        📋 Logs
                      </button>
                      <button
                        onClick={() => toggleWebhookStatus(webhook)}
                        style={{
                          background: 'none',
                          border: '1px solid #f59e0b',
                          borderRadius: '4px',
                          padding: '4px 8px',
                          cursor: 'pointer',
                          color: '#f59e0b',
                          fontSize: '12px',
                        }}
                      >
                        {webhook.is_active ? '⏸️' : '▶️'}
                      </button>
                      <button
                        onClick={() => handleDeleteWebhook(webhook)}
                        style={{
                          background: 'none',
                          border: '1px solid #ef4444',
                          borderRadius: '4px',
                          padding: '4px 8px',
                          cursor: 'pointer',
                          color: '#ef4444',
                          fontSize: '12px',
                        }}
                      >
                        🗑️
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create Webhook Form */}
      {showCreateForm && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
        >
          <div
            style={{
              backgroundColor: 'white',
              padding: '24px',
              borderRadius: '8px',
              width: '600px',
              maxHeight: '80vh',
              overflow: 'auto',
            }}
          >
            <h3 style={{ margin: '0 0 16px 0' }}>Create New Webhook</h3>
            <div
              style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}
            >
              <div>
                <label
                  style={{
                    display: 'block',
                    marginBottom: '4px',
                    fontWeight: '500',
                  }}
                >
                  Name *
                </label>
                <input
                  type='text'
                  value={newWebhook.name}
                  onChange={e =>
                    setNewWebhook({ ...newWebhook, name: e.target.value })
                  }
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    border: '1px solid #d1d5db',
                    borderRadius: '6px',
                  }}
                  required
                />
              </div>
              <div>
                <label
                  style={{
                    display: 'block',
                    marginBottom: '4px',
                    fontWeight: '500',
                  }}
                >
                  Description
                </label>
                <textarea
                  value={newWebhook.description}
                  onChange={e =>
                    setNewWebhook({
                      ...newWebhook,
                      description: e.target.value,
                    })
                  }
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    border: '1px solid #d1d5db',
                    borderRadius: '6px',
                    minHeight: '60px',
                  }}
                />
              </div>
              <div>
                <label
                  style={{
                    display: 'block',
                    marginBottom: '4px',
                    fontWeight: '500',
                  }}
                >
                  Webhook URL *
                </label>
                <input
                  type='url'
                  value={newWebhook.url}
                  onChange={e =>
                    setNewWebhook({ ...newWebhook, url: e.target.value })
                  }
                  placeholder='https://your-app.com/webhooks/aivo'
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    border: '1px solid #d1d5db',
                    borderRadius: '6px',
                  }}
                  required
                />
              </div>
              <div>
                <label
                  style={{
                    display: 'block',
                    marginBottom: '4px',
                    fontWeight: '500',
                  }}
                >
                  Events
                </label>
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                  {AVAILABLE_EVENTS.map(event => (
                    <label
                      key={event}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                      }}
                    >
                      <input
                        type='checkbox'
                        checked={newWebhook.events.includes(event)}
                        onChange={e => {
                          if (e.target.checked) {
                            setNewWebhook({
                              ...newWebhook,
                              events: [...newWebhook.events, event],
                            });
                          } else {
                            setNewWebhook({
                              ...newWebhook,
                              events: newWebhook.events.filter(
                                e => e !== event
                              ),
                            });
                          }
                        }}
                      />
                      {event}
                    </label>
                  ))}
                </div>
              </div>
              <div style={{ display: 'flex', gap: '16px' }}>
                <div style={{ flex: 1 }}>
                  <label
                    style={{
                      display: 'block',
                      marginBottom: '4px',
                      fontWeight: '500',
                    }}
                  >
                    Max Retries
                  </label>
                  <input
                    type='number'
                    value={newWebhook.max_retries || ''}
                    onChange={e =>
                      setNewWebhook({
                        ...newWebhook,
                        max_retries: parseInt(e.target.value) || 3,
                      })
                    }
                    min='0'
                    max='10'
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      border: '1px solid #d1d5db',
                      borderRadius: '6px',
                    }}
                  />
                </div>
                <div style={{ flex: 1 }}>
                  <label
                    style={{
                      display: 'block',
                      marginBottom: '4px',
                      fontWeight: '500',
                    }}
                  >
                    Retry Delay (seconds)
                  </label>
                  <input
                    type='number'
                    value={newWebhook.retry_delay_seconds || ''}
                    onChange={e =>
                      setNewWebhook({
                        ...newWebhook,
                        retry_delay_seconds: parseInt(e.target.value) || 5,
                      })
                    }
                    min='1'
                    max='3600'
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      border: '1px solid #d1d5db',
                      borderRadius: '6px',
                    }}
                  />
                </div>
              </div>
            </div>
            <div
              style={{
                display: 'flex',
                gap: '12px',
                justifyContent: 'flex-end',
                marginTop: '24px',
              }}
            >
              <button
                onClick={() => setShowCreateForm(false)}
                style={{
                  padding: '8px 16px',
                  border: '1px solid #d1d5db',
                  backgroundColor: 'white',
                  borderRadius: '6px',
                  cursor: 'pointer',
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleCreateWebhook}
                disabled={!newWebhook.name || !newWebhook.url}
                style={{
                  padding: '8px 16px',
                  border: 'none',
                  backgroundColor:
                    newWebhook.name && newWebhook.url ? '#3b82f6' : '#9ca3af',
                  color: 'white',
                  borderRadius: '6px',
                  cursor:
                    newWebhook.name && newWebhook.url
                      ? 'pointer'
                      : 'not-allowed',
                }}
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Test Webhook Form */}
      {showTestForm && selectedWebhook && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
        >
          <div
            style={{
              backgroundColor: 'white',
              padding: '24px',
              borderRadius: '8px',
              width: '600px',
              maxHeight: '80vh',
              overflow: 'auto',
            }}
          >
            <h3 style={{ margin: '0 0 16px 0' }}>
              Test Webhook: {selectedWebhook.name}
            </h3>
            <div
              style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}
            >
              <div>
                <label
                  style={{
                    display: 'block',
                    marginBottom: '4px',
                    fontWeight: '500',
                  }}
                >
                  Event Type
                </label>
                <select
                  value={testData.event_type}
                  onChange={e =>
                    setTestData({ ...testData, event_type: e.target.value })
                  }
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    border: '1px solid #d1d5db',
                    borderRadius: '6px',
                  }}
                >
                  {selectedWebhook.events.map(event => (
                    <option key={event} value={event}>
                      {event}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label
                  style={{
                    display: 'block',
                    marginBottom: '4px',
                    fontWeight: '500',
                  }}
                >
                  Test Payload (JSON)
                </label>
                <textarea
                  value={JSON.stringify(testData.payload, null, 2)}
                  onChange={e => {
                    try {
                      const payload = JSON.parse(e.target.value);
                      setTestData({ ...testData, payload });
                    } catch {
                      // Invalid JSON, don't update
                    }
                  }}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    border: '1px solid #d1d5db',
                    borderRadius: '6px',
                    minHeight: '150px',
                    fontFamily: 'monospace',
                    fontSize: '14px',
                  }}
                />
              </div>
              <div
                style={{
                  padding: '12px',
                  backgroundColor: '#f0f9ff',
                  borderRadius: '6px',
                  border: '1px solid #3b82f6',
                }}
              >
                <strong>📡 Target:</strong> {selectedWebhook.url}
              </div>
            </div>
            <div
              style={{
                display: 'flex',
                gap: '12px',
                justifyContent: 'flex-end',
                marginTop: '24px',
              }}
            >
              <button
                onClick={() => setShowTestForm(false)}
                style={{
                  padding: '8px 16px',
                  border: '1px solid #d1d5db',
                  backgroundColor: 'white',
                  borderRadius: '6px',
                  cursor: 'pointer',
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleTestWebhook}
                style={{
                  padding: '8px 16px',
                  border: 'none',
                  backgroundColor: '#10b981',
                  color: 'white',
                  borderRadius: '6px',
                  cursor: 'pointer',
                }}
              >
                🧪 Send Test
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Webhook Deliveries Modal */}
      {showDeliveries && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
        >
          <div
            style={{
              backgroundColor: 'white',
              padding: '24px',
              borderRadius: '8px',
              width: '90%',
              maxWidth: '1000px',
              maxHeight: '80vh',
              overflow: 'auto',
            }}
          >
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '16px',
              }}
            >
              <h3 style={{ margin: 0 }}>Webhook Deliveries</h3>
              <button
                onClick={() => setShowDeliveries(false)}
                style={{
                  background: 'none',
                  border: 'none',
                  fontSize: '18px',
                  cursor: 'pointer',
                }}
              >
                ✕
              </button>
            </div>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #e5e7eb' }}>
                  <th
                    style={{
                      textAlign: 'left',
                      padding: '12px 8px',
                      fontWeight: '600',
                    }}
                  >
                    Event
                  </th>
                  <th
                    style={{
                      textAlign: 'left',
                      padding: '12px 8px',
                      fontWeight: '600',
                    }}
                  >
                    Status
                  </th>
                  <th
                    style={{
                      textAlign: 'left',
                      padding: '12px 8px',
                      fontWeight: '600',
                    }}
                  >
                    Attempts
                  </th>
                  <th
                    style={{
                      textAlign: 'left',
                      padding: '12px 8px',
                      fontWeight: '600',
                    }}
                  >
                    Response
                  </th>
                  <th
                    style={{
                      textAlign: 'left',
                      padding: '12px 8px',
                      fontWeight: '600',
                    }}
                  >
                    Created
                  </th>
                  <th
                    style={{
                      textAlign: 'left',
                      padding: '12px 8px',
                      fontWeight: '600',
                    }}
                  >
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {selectedDeliveries.map(delivery => (
                  <tr
                    key={delivery.id}
                    style={{ borderBottom: '1px solid #f3f4f6' }}
                  >
                    <td style={{ padding: '12px 8px' }}>
                      <div style={{ fontWeight: '500' }}>
                        {delivery.event_type}
                      </div>
                    </td>
                    <td style={{ padding: '12px 8px' }}>
                      <span
                        style={{
                          padding: '4px 8px',
                          borderRadius: '12px',
                          fontSize: '12px',
                          backgroundColor:
                            getStatusColor(delivery.status) + '20',
                          color: getStatusColor(delivery.status),
                          fontWeight: '500',
                        }}
                      >
                        {getStatusIcon(delivery.status)} {delivery.status}
                      </span>
                    </td>
                    <td style={{ padding: '12px 8px' }}>
                      <div style={{ fontSize: '14px' }}>
                        {delivery.attempts}
                      </div>
                      {delivery.next_retry_at && (
                        <div style={{ fontSize: '12px', color: '#6b7280' }}>
                          Next: {formatDate(delivery.next_retry_at)}
                        </div>
                      )}
                    </td>
                    <td style={{ padding: '12px 8px' }}>
                      {delivery.response_status && (
                        <div style={{ fontSize: '14px' }}>
                          Status: {delivery.response_status}
                        </div>
                      )}
                      {delivery.delivered_at && (
                        <div style={{ fontSize: '12px', color: '#6b7280' }}>
                          {formatDate(delivery.delivered_at)}
                        </div>
                      )}
                    </td>
                    <td style={{ padding: '12px 8px' }}>
                      <div style={{ fontSize: '14px' }}>
                        {formatDate(delivery.created_at)}
                      </div>
                    </td>
                    <td style={{ padding: '12px 8px' }}>
                      {delivery.status === 'failed' && (
                        <button
                          onClick={() => handleReplayDelivery(delivery)}
                          style={{
                            background: 'none',
                            border: '1px solid #f59e0b',
                            borderRadius: '4px',
                            padding: '4px 8px',
                            cursor: 'pointer',
                            color: '#f59e0b',
                            fontSize: '12px',
                          }}
                        >
                          🔄 Replay
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default Webhooks;
