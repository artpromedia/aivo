import React, { useState, useEffect } from 'react';

interface ApiKey {
  id: string;
  tenant_id: string;
  name: string;
  description?: string;
  key_prefix: string;
  scopes: string[];
  is_active: boolean;
  is_revoked: boolean;
  expires_at?: string;
  last_used_at?: string;
  usage_count: number;
  rate_limit_per_minute?: number;
  created_at: string;
  updated_at: string;
  created_by?: string;
}

interface ApiKeyCreateData {
  name: string;
  description?: string;
  scopes: string[];
  expires_in_days?: number;
  rate_limit_per_minute?: number;
}

interface ApiKeyCreateResponse extends ApiKey {
  api_key: string;
}

const AVAILABLE_SCOPES = ['read', 'write', 'admin', 'webhooks', 'analytics'];

const ApiKeys: React.FC = () => {
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showRotateForm, setShowRotateForm] = useState(false);
  const [selectedApiKey, setSelectedApiKey] = useState<ApiKey | null>(null);
  const [newApiKey, setNewApiKey] = useState<ApiKeyCreateData>({
    name: '',
    description: '',
    scopes: ['read', 'write'],
    expires_in_days: 365,
    rate_limit_per_minute: undefined,
  });
  const [rotateExpiryDays, setRotateExpiryDays] = useState(365);
  const [showNewKey, setShowNewKey] = useState<string | null>(null);
  const [message, setMessage] = useState<{
    text: string;
    type: 'success' | 'error' | 'info';
  } | null>(null);
  const [showKeyValues, setShowKeyValues] = useState<Record<string, boolean>>(
    {}
  );

  // Mock tenant ID - replace with actual tenant selection
  const tenantId = 'tenant-123';

  useEffect(() => {
    fetchApiKeys();
  }, []);

  const fetchApiKeys = async (): Promise<void> => {
    setLoading(true);
    try {
      // Mock API call - replace with actual API integration
      const response = await fetch(`/api/v1/tenants/${tenantId}/api-keys`);
      if (response.ok) {
        const data = await response.json();
        setApiKeys(data.api_keys);
      } else {
        throw new Error('Failed to fetch API keys');
      }
    } catch {
      // Handle error appropriately
      setMessage({ text: 'Failed to load API keys', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handleCreateApiKey = async (): Promise<void> => {
    try {
      const response = await fetch(`/api/v1/tenants/${tenantId}/api-keys`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newApiKey),
      });

      if (response.ok) {
        const data: ApiKeyCreateResponse = await response.json();
        setApiKeys([data, ...apiKeys]);
        setShowNewKey(data.api_key);
        setShowCreateForm(false);
        setNewApiKey({
          name: '',
          description: '',
          scopes: ['read', 'write'],
          expires_in_days: 365,
          rate_limit_per_minute: undefined,
        });
        setMessage({ text: 'API key created successfully', type: 'success' });
      } else {
        throw new Error('Failed to create API key');
      }
    } catch {
      setMessage({ text: 'Failed to create API key', type: 'error' });
    }
  };

  const handleRotateApiKey = async (): Promise<void> => {
    if (!selectedApiKey) return;

    try {
      const response = await fetch(
        `/api/v1/tenants/${tenantId}/api-keys/${selectedApiKey.id}/rotate`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ expires_in_days: rotateExpiryDays }),
        }
      );

      if (response.ok) {
        const data: ApiKeyCreateResponse = await response.json();
        setApiKeys(
          apiKeys.map(key => (key.id === selectedApiKey.id ? data : key))
        );
        setShowNewKey(data.api_key);
        setShowRotateForm(false);
        setSelectedApiKey(null);
        setMessage({ text: 'API key rotated successfully', type: 'success' });
      } else {
        throw new Error('Failed to rotate API key');
      }
    } catch {
      setMessage({ text: 'Failed to rotate API key', type: 'error' });
    }
  };

  const handleDeleteApiKey = async (apiKey: ApiKey): Promise<void> => {
    if (!confirm(`Are you sure you want to delete "${apiKey.name}"?`)) {
      return;
    }

    try {
      const response = await fetch(
        `/api/v1/tenants/${tenantId}/api-keys/${apiKey.id}`,
        {
          method: 'DELETE',
        }
      );

      if (response.ok) {
        setApiKeys(apiKeys.filter(key => key.id !== apiKey.id));
        setMessage({ text: 'API key deleted successfully', type: 'success' });
      } else {
        throw new Error('Failed to delete API key');
      }
    } catch {
      setMessage({ text: 'Failed to delete API key', type: 'error' });
    }
  };

  const copyToClipboard = (text: string): void => {
    navigator.clipboard.writeText(text);
    setMessage({ text: 'Copied to clipboard', type: 'success' });
  };

  const toggleKeyVisibility = (keyId: string): void => {
    setShowKeyValues(prev => ({
      ...prev,
      [keyId]: !prev[keyId],
    }));
  };

  const formatDate = (dateString?: string): string => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleDateString();
  };

  const getStatusColor = (apiKey: ApiKey): string => {
    if (apiKey.is_revoked) return '#ef4444';
    if (!apiKey.is_active) return '#f59e0b';
    if (apiKey.expires_at && new Date(apiKey.expires_at) < new Date())
      return '#ef4444';
    return '#10b981';
  };

  const getStatusText = (apiKey: ApiKey): string => {
    if (apiKey.is_revoked) return 'Revoked';
    if (!apiKey.is_active) return 'Inactive';
    if (apiKey.expires_at && new Date(apiKey.expires_at) < new Date())
      return 'Expired';
    return 'Active';
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
            🔑 API Keys
          </h2>
          <div style={{ display: 'flex', gap: '12px' }}>
            <button
              onClick={fetchApiKeys}
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
              ➕ Create API Key
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
                  Key
                </th>
                <th
                  style={{
                    textAlign: 'left',
                    padding: '12px 8px',
                    fontWeight: '600',
                  }}
                >
                  Scopes
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
                  Usage
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
              {apiKeys.map(apiKey => (
                <tr
                  key={apiKey.id}
                  style={{ borderBottom: '1px solid #f3f4f6' }}
                >
                  <td style={{ padding: '12px 8px' }}>
                    <div>
                      <div style={{ fontWeight: '500' }}>{apiKey.name}</div>
                      {apiKey.description && (
                        <div style={{ fontSize: '14px', color: '#6b7280' }}>
                          {apiKey.description}
                        </div>
                      )}
                    </div>
                  </td>
                  <td style={{ padding: '12px 8px' }}>
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                      }}
                    >
                      <span
                        style={{ fontFamily: 'monospace', fontSize: '14px' }}
                      >
                        {showKeyValues[apiKey.id]
                          ? apiKey.key_prefix + '...'
                          : '••••••••••••'}
                      </span>
                      <button
                        onClick={() => toggleKeyVisibility(apiKey.id)}
                        style={{
                          background: 'none',
                          border: 'none',
                          cursor: 'pointer',
                          fontSize: '16px',
                        }}
                      >
                        {showKeyValues[apiKey.id] ? '🙈' : '👁️'}
                      </button>
                    </div>
                  </td>
                  <td style={{ padding: '12px 8px' }}>
                    <div
                      style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}
                    >
                      {apiKey.scopes.map(scope => (
                        <span
                          key={scope}
                          style={{
                            padding: '2px 8px',
                            backgroundColor: '#f3f4f6',
                            borderRadius: '12px',
                            fontSize: '12px',
                          }}
                        >
                          {scope}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td style={{ padding: '12px 8px' }}>
                    <span
                      style={{
                        padding: '4px 8px',
                        borderRadius: '12px',
                        fontSize: '12px',
                        backgroundColor: getStatusColor(apiKey) + '20',
                        color: getStatusColor(apiKey),
                        fontWeight: '500',
                      }}
                    >
                      {getStatusText(apiKey)}
                    </span>
                  </td>
                  <td style={{ padding: '12px 8px' }}>
                    <div>
                      <div style={{ fontSize: '14px' }}>
                        {apiKey.usage_count} requests
                      </div>
                      <div style={{ fontSize: '12px', color: '#6b7280' }}>
                        Last used: {formatDate(apiKey.last_used_at)}
                      </div>
                    </div>
                  </td>
                  <td style={{ padding: '12px 8px' }}>
                    <div>
                      <div style={{ fontSize: '14px' }}>
                        {formatDate(apiKey.created_at)}
                      </div>
                      {apiKey.expires_at && (
                        <div style={{ fontSize: '12px', color: '#6b7280' }}>
                          Expires: {formatDate(apiKey.expires_at)}
                        </div>
                      )}
                    </div>
                  </td>
                  <td style={{ padding: '12px 8px' }}>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <button
                        onClick={() => {
                          setSelectedApiKey(apiKey);
                          setShowRotateForm(true);
                        }}
                        disabled={apiKey.is_revoked}
                        style={{
                          background: 'none',
                          border: '1px solid #d1d5db',
                          borderRadius: '4px',
                          padding: '4px 8px',
                          cursor: apiKey.is_revoked ? 'not-allowed' : 'pointer',
                          opacity: apiKey.is_revoked ? 0.5 : 1,
                        }}
                      >
                        🔄
                      </button>
                      <button
                        onClick={() => handleDeleteApiKey(apiKey)}
                        style={{
                          background: 'none',
                          border: '1px solid #ef4444',
                          borderRadius: '4px',
                          padding: '4px 8px',
                          cursor: 'pointer',
                          color: '#ef4444',
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

      {/* Create API Key Form */}
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
              width: '500px',
              maxHeight: '80vh',
              overflow: 'auto',
            }}
          >
            <h3 style={{ margin: '0 0 16px 0' }}>Create New API Key</h3>
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
                  value={newApiKey.name}
                  onChange={e =>
                    setNewApiKey({ ...newApiKey, name: e.target.value })
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
                  value={newApiKey.description}
                  onChange={e =>
                    setNewApiKey({ ...newApiKey, description: e.target.value })
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
                  Scopes
                </label>
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                  {AVAILABLE_SCOPES.map(scope => (
                    <label
                      key={scope}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                      }}
                    >
                      <input
                        type='checkbox'
                        checked={newApiKey.scopes.includes(scope)}
                        onChange={e => {
                          if (e.target.checked) {
                            setNewApiKey({
                              ...newApiKey,
                              scopes: [...newApiKey.scopes, scope],
                            });
                          } else {
                            setNewApiKey({
                              ...newApiKey,
                              scopes: newApiKey.scopes.filter(s => s !== scope),
                            });
                          }
                        }}
                      />
                      {scope}
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
                    Expires in Days
                  </label>
                  <input
                    type='number'
                    value={newApiKey.expires_in_days || ''}
                    onChange={e =>
                      setNewApiKey({
                        ...newApiKey,
                        expires_in_days: parseInt(e.target.value) || undefined,
                      })
                    }
                    min='1'
                    max='365'
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
                    Rate Limit (per minute)
                  </label>
                  <input
                    type='number'
                    value={newApiKey.rate_limit_per_minute || ''}
                    onChange={e =>
                      setNewApiKey({
                        ...newApiKey,
                        rate_limit_per_minute:
                          parseInt(e.target.value) || undefined,
                      })
                    }
                    min='1'
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
                onClick={handleCreateApiKey}
                disabled={!newApiKey.name}
                style={{
                  padding: '8px 16px',
                  border: 'none',
                  backgroundColor: newApiKey.name ? '#3b82f6' : '#9ca3af',
                  color: 'white',
                  borderRadius: '6px',
                  cursor: newApiKey.name ? 'pointer' : 'not-allowed',
                }}
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Rotate API Key Form */}
      {showRotateForm && selectedApiKey && (
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
              width: '400px',
            }}
          >
            <h3 style={{ margin: '0 0 16px 0' }}>Rotate API Key</h3>
            <p style={{ color: '#6b7280', marginBottom: '16px' }}>
              This will generate a new API key and revoke the current one.
            </p>
            <div>
              <label
                style={{
                  display: 'block',
                  marginBottom: '4px',
                  fontWeight: '500',
                }}
              >
                New Key Expires in Days
              </label>
              <input
                type='number'
                value={rotateExpiryDays}
                onChange={e =>
                  setRotateExpiryDays(parseInt(e.target.value) || 365)
                }
                min='1'
                max='365'
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                }}
              />
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
                onClick={() => setShowRotateForm(false)}
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
                onClick={handleRotateApiKey}
                style={{
                  padding: '8px 16px',
                  border: 'none',
                  backgroundColor: '#f59e0b',
                  color: 'white',
                  borderRadius: '6px',
                  cursor: 'pointer',
                }}
              >
                Rotate
              </button>
            </div>
          </div>
        </div>
      )}

      {/* New API Key Display */}
      {showNewKey && (
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
            }}
          >
            <h3
              style={{
                margin: '0 0 16px 0',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              🔐 API Key Created
            </h3>
            <div
              style={{
                padding: '12px',
                backgroundColor: '#fef3cd',
                borderRadius: '6px',
                marginBottom: '16px',
                border: '1px solid #f59e0b',
              }}
            >
              <strong>⚠️ Warning:</strong> This is the only time you'll see the
              full API key. Make sure to copy and store it securely.
            </div>
            <div>
              <label
                style={{
                  display: 'block',
                  marginBottom: '4px',
                  fontWeight: '500',
                }}
              >
                API Key
              </label>
              <div style={{ display: 'flex', gap: '8px' }}>
                <input
                  type='text'
                  value={showNewKey}
                  readOnly
                  style={{
                    flex: 1,
                    padding: '8px 12px',
                    border: '1px solid #d1d5db',
                    borderRadius: '6px',
                    fontFamily: 'monospace',
                    backgroundColor: '#f9fafb',
                  }}
                />
                <button
                  onClick={() => copyToClipboard(showNewKey)}
                  style={{
                    padding: '8px 12px',
                    border: '1px solid #d1d5db',
                    backgroundColor: 'white',
                    borderRadius: '6px',
                    cursor: 'pointer',
                  }}
                >
                  📋 Copy
                </button>
              </div>
            </div>
            <div
              style={{
                display: 'flex',
                justifyContent: 'flex-end',
                marginTop: '24px',
              }}
            >
              <button
                onClick={() => setShowNewKey(null)}
                style={{
                  padding: '8px 16px',
                  border: 'none',
                  backgroundColor: '#3b82f6',
                  color: 'white',
                  borderRadius: '6px',
                  cursor: 'pointer',
                }}
              >
                I've Saved the Key
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ApiKeys;
