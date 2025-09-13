import React, { useState, useEffect, useCallback } from 'react';

// Types
interface NotificationSubscription {
  id: string;
  tenant_id: string;
  channels: string[];
  severity_levels: string[];
  incident_types: string[];
  is_active: boolean;
  created_by: string;
  created_at: string;
  updated_at: string;
}

interface CreateSubscriptionForm {
  tenant_id: string;
  channels: string[];
  severity_levels: string[];
  incident_types: string[];
}

// API service
class SubscriptionService {
  private baseUrl = '/api/v1/subscriptions';

  async getSubscriptions(
    filters: {
      tenant_id?: string;
      is_active?: boolean;
      page?: number;
      page_size?: number;
    } = {}
  ) {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== '') {
        params.append(key, String(value));
      }
    });

    const response = await fetch(`${this.baseUrl}?${params}`);
    if (!response.ok) {
      throw new Error('Failed to fetch subscriptions');
    }
    return response.json();
  }

  async createSubscription(
    subscription: CreateSubscriptionForm & { created_by: string }
  ) {
    const response = await fetch(this.baseUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(subscription),
    });
    if (!response.ok) {
      throw new Error('Failed to create subscription');
    }
    return response.json();
  }

  async updateSubscription(
    id: string,
    updates: Partial<NotificationSubscription>
  ) {
    const response = await fetch(`${this.baseUrl}/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates),
    });
    if (!response.ok) {
      throw new Error('Failed to update subscription');
    }
    return response.json();
  }

  async deleteSubscription(id: string) {
    const response = await fetch(`${this.baseUrl}/${id}`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      throw new Error('Failed to delete subscription');
    }
  }
}

const subscriptionService = new SubscriptionService();

// Helper functions
const formatDateTime = (dateString: string): string => {
  return new Date(dateString).toLocaleString();
};

// Available options
const availableChannels = ['email', 'sms', 'webhook', 'slack'];
const availableSeverities = ['low', 'medium', 'high', 'critical'];
const availableIncidentTypes = [
  'outage',
  'degradation',
  'maintenance',
  'security',
];

// Styles
const styles = {
  container: {
    padding: '24px',
    fontFamily: 'Arial, sans-serif',
  },
  header: {
    marginBottom: '24px',
  },
  title: {
    fontSize: '2rem',
    fontWeight: 'bold' as const,
    margin: 0,
    marginBottom: '8px',
  },
  subtitle: {
    color: '#666',
    margin: 0,
  },
  card: {
    border: '1px solid #ddd',
    borderRadius: '8px',
    padding: '16px',
    marginBottom: '16px',
    backgroundColor: '#fff',
  },
  filters: {
    border: '1px solid #ddd',
    borderRadius: '8px',
    padding: '16px',
    marginBottom: '16px',
    backgroundColor: '#f9f9f9',
  },
  filterGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
    gap: '16px',
    alignItems: 'center',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse' as const,
    border: '1px solid #ddd',
    backgroundColor: '#fff',
  },
  th: {
    backgroundColor: '#f5f5f5',
    padding: '12px',
    textAlign: 'left' as const,
    borderBottom: '1px solid #ddd',
    fontWeight: 'bold' as const,
  },
  td: {
    padding: '12px',
    borderBottom: '1px solid #eee',
  },
  chip: {
    display: 'inline-block',
    padding: '4px 8px',
    borderRadius: '16px',
    fontSize: '12px',
    fontWeight: 'bold' as const,
    color: '#fff',
    marginRight: '4px',
    marginBottom: '4px',
  },
  button: {
    padding: '8px 16px',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: 'bold' as const,
  },
  primaryButton: {
    backgroundColor: '#1976d2',
    color: '#fff',
  },
  secondaryButton: {
    backgroundColor: '#f5f5f5',
    color: '#333',
    border: '1px solid #ddd',
  },
  fab: {
    position: 'fixed' as const,
    bottom: '16px',
    right: '16px',
    width: '56px',
    height: '56px',
    borderRadius: '50%',
    backgroundColor: '#1976d2',
    color: '#fff',
    border: 'none',
    fontSize: '24px',
    cursor: 'pointer',
    boxShadow: '0 4px 8px rgba(0,0,0,0.2)',
  },
  modal: {
    position: 'fixed' as const,
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    backgroundColor: 'rgba(0,0,0,0.5)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
  },
  modalContent: {
    backgroundColor: '#fff',
    borderRadius: '8px',
    padding: '24px',
    maxWidth: '600px',
    width: '90%',
    maxHeight: '90%',
    overflow: 'auto',
  },
  formGroup: {
    marginBottom: '16px',
  },
  label: {
    display: 'block',
    marginBottom: '4px',
    fontWeight: 'bold' as const,
  },
  input: {
    width: '100%',
    padding: '8px',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '14px',
    boxSizing: 'border-box' as const,
  },
  select: {
    width: '100%',
    padding: '8px',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '14px',
    backgroundColor: '#fff',
    boxSizing: 'border-box' as const,
  },
  checkboxGroup: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
    gap: '8px',
    border: '1px solid #ddd',
    borderRadius: '4px',
    padding: '12px',
  },
  checkboxItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  alert: {
    padding: '12px',
    borderRadius: '4px',
    marginBottom: '16px',
    backgroundColor: '#f8d7da',
    color: '#721c24',
    border: '1px solid #f5c6cb',
  },
};

// Main component
const NotificationSubscriptionsPage: React.FC = () => {
  const [subscriptions, setSubscriptions] = useState<
    NotificationSubscription[]
  >([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [totalCount, setTotalCount] = useState(0);

  // Filters
  const [tenantFilter, setTenantFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  // Pagination
  const [page, setPage] = useState(0);
  const [rowsPerPage] = useState(25);

  // Dialogs
  const [createDialogOpen, setCreateDialogOpen] = useState(false);

  // Form state
  const [createForm, setCreateForm] = useState<CreateSubscriptionForm>({
    tenant_id: '',
    channels: [],
    severity_levels: [],
    incident_types: [],
  });

  // Load subscriptions
  const loadSubscriptions = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await subscriptionService.getSubscriptions({
        tenant_id: tenantFilter || undefined,
        is_active:
          statusFilter === 'active'
            ? true
            : statusFilter === 'inactive'
              ? false
              : undefined,
        page: page + 1,
        page_size: rowsPerPage,
      });

      setSubscriptions(response.subscriptions);
      setTotalCount(response.pagination.total);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to load subscriptions'
      );
    } finally {
      setLoading(false);
    }
  }, [page, rowsPerPage, tenantFilter, statusFilter]);

  // Effects
  useEffect(() => {
    loadSubscriptions();
  }, [loadSubscriptions]);

  // Event handlers
  const handleCreateSubscription = async () => {
    try {
      setLoading(true);

      await subscriptionService.createSubscription({
        ...createForm,
        created_by: 'current-user',
      });

      setCreateDialogOpen(false);
      setCreateForm({
        tenant_id: '',
        channels: [],
        severity_levels: [],
        incident_types: [],
      });

      await loadSubscriptions();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to create subscription'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleToggleActive = async (subscription: NotificationSubscription) => {
    try {
      setLoading(true);
      await subscriptionService.updateSubscription(subscription.id, {
        is_active: !subscription.is_active,
      });
      await loadSubscriptions();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to update subscription'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteSubscription = async (
    subscription: NotificationSubscription
  ) => {
    if (
      !confirm(
        `Are you sure you want to delete this subscription for ${subscription.tenant_id}?`
      )
    ) {
      return;
    }

    try {
      setLoading(true);
      await subscriptionService.deleteSubscription(subscription.id);
      await loadSubscriptions();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to delete subscription'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleChannelChange = (channel: string, checked: boolean) => {
    if (checked) {
      setCreateForm({
        ...createForm,
        channels: [...createForm.channels, channel],
      });
    } else {
      setCreateForm({
        ...createForm,
        channels: createForm.channels.filter(c => c !== channel),
      });
    }
  };

  const handleSeverityChange = (severity: string, checked: boolean) => {
    if (checked) {
      setCreateForm({
        ...createForm,
        severity_levels: [...createForm.severity_levels, severity],
      });
    } else {
      setCreateForm({
        ...createForm,
        severity_levels: createForm.severity_levels.filter(s => s !== severity),
      });
    }
  };

  const handleIncidentTypeChange = (type: string, checked: boolean) => {
    if (checked) {
      setCreateForm({
        ...createForm,
        incident_types: [...createForm.incident_types, type],
      });
    } else {
      setCreateForm({
        ...createForm,
        incident_types: createForm.incident_types.filter(t => t !== type),
      });
    }
  };

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <h1 style={styles.title}>Notification Subscriptions</h1>
        <p style={styles.subtitle}>
          Manage tenant notification subscriptions for incidents
        </p>
      </div>

      {/* Error Alert */}
      {error && (
        <div style={styles.alert}>
          {error}
          <button
            onClick={() => setError(null)}
            style={{
              float: 'right',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
            }}
          >
            ×
          </button>
        </div>
      )}

      {/* Filters */}
      <div style={styles.filters}>
        <div style={styles.filterGrid}>
          <div>
            <label style={styles.label}>Tenant ID</label>
            <input
              style={styles.input}
              type='text'
              value={tenantFilter}
              onChange={e => setTenantFilter(e.target.value)}
              placeholder='Filter by tenant ID'
            />
          </div>

          <div>
            <label style={styles.label}>Status</label>
            <select
              style={styles.select}
              value={statusFilter}
              onChange={e => setStatusFilter(e.target.value)}
            >
              <option value=''>All</option>
              <option value='active'>Active</option>
              <option value='inactive'>Inactive</option>
            </select>
          </div>

          <div>
            <button
              style={{ ...styles.button, ...styles.secondaryButton }}
              onClick={loadSubscriptions}
              disabled={loading}
            >
              🔄 Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Subscriptions Table */}
      <div
        style={{
          border: '1px solid #ddd',
          borderRadius: '8px',
          overflow: 'hidden',
        }}
      >
        <table style={styles.table}>
          <thead>
            <tr>
              <th style={styles.th}>Tenant ID</th>
              <th style={styles.th}>Channels</th>
              <th style={styles.th}>Severity Levels</th>
              <th style={styles.th}>Incident Types</th>
              <th style={styles.th}>Status</th>
              <th style={styles.th}>Created</th>
              <th style={styles.th}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={7} style={{ ...styles.td, textAlign: 'center' }}>
                  Loading...
                </td>
              </tr>
            ) : subscriptions.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ ...styles.td, textAlign: 'center' }}>
                  No subscriptions found
                </td>
              </tr>
            ) : (
              subscriptions.map(subscription => (
                <tr key={subscription.id}>
                  <td style={styles.td}>
                    <strong>{subscription.tenant_id}</strong>
                  </td>

                  <td style={styles.td}>
                    {subscription.channels.map(channel => (
                      <span
                        key={channel}
                        style={{
                          ...styles.chip,
                          backgroundColor: '#2196f3',
                        }}
                      >
                        {channel.toUpperCase()}
                      </span>
                    ))}
                  </td>

                  <td style={styles.td}>
                    {subscription.severity_levels.map(severity => (
                      <span
                        key={severity}
                        style={{
                          ...styles.chip,
                          backgroundColor:
                            severity === 'critical'
                              ? '#f44336'
                              : severity === 'high'
                                ? '#ff9800'
                                : severity === 'medium'
                                  ? '#2196f3'
                                  : '#4caf50',
                        }}
                      >
                        {severity.toUpperCase()}
                      </span>
                    ))}
                  </td>

                  <td style={styles.td}>
                    {subscription.incident_types.map(type => (
                      <span
                        key={type}
                        style={{
                          ...styles.chip,
                          backgroundColor: '#666',
                        }}
                      >
                        {type.toUpperCase()}
                      </span>
                    ))}
                  </td>

                  <td style={styles.td}>
                    <span
                      style={{
                        ...styles.chip,
                        backgroundColor: subscription.is_active
                          ? '#4caf50'
                          : '#666',
                      }}
                    >
                      {subscription.is_active ? 'ACTIVE' : 'INACTIVE'}
                    </span>
                  </td>

                  <td style={styles.td}>
                    {formatDateTime(subscription.created_at)}
                  </td>

                  <td style={styles.td}>
                    <button
                      style={{
                        ...styles.button,
                        backgroundColor: subscription.is_active
                          ? '#ff9800'
                          : '#4caf50',
                        color: '#fff',
                        marginRight: '4px',
                        padding: '4px 8px',
                        fontSize: '12px',
                      }}
                      onClick={() => handleToggleActive(subscription)}
                    >
                      {subscription.is_active ? 'Deactivate' : 'Activate'}
                    </button>

                    <button
                      style={{
                        ...styles.button,
                        backgroundColor: '#f44336',
                        color: '#fff',
                        padding: '4px 8px',
                      }}
                      onClick={() => handleDeleteSubscription(subscription)}
                    >
                      🗑
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div style={{ marginTop: '16px', textAlign: 'center' }}>
        <button
          style={{
            ...styles.button,
            ...styles.secondaryButton,
            marginRight: '8px',
          }}
          onClick={() => setPage(Math.max(0, page - 1))}
          disabled={page === 0}
        >
          Previous
        </button>

        <span style={{ margin: '0 16px' }}>
          Page {page + 1} of {Math.ceil(totalCount / rowsPerPage)}
        </span>

        <button
          style={{
            ...styles.button,
            ...styles.secondaryButton,
            marginLeft: '8px',
          }}
          onClick={() => setPage(page + 1)}
          disabled={(page + 1) * rowsPerPage >= totalCount}
        >
          Next
        </button>
      </div>

      {/* Floating Action Button */}
      <button
        style={styles.fab}
        onClick={() => setCreateDialogOpen(true)}
        title='Create New Subscription'
      >
        +
      </button>

      {/* Create Subscription Modal */}
      {createDialogOpen && (
        <div style={styles.modal} onClick={() => setCreateDialogOpen(false)}>
          <div style={styles.modalContent} onClick={e => e.stopPropagation()}>
            <h2>Create Notification Subscription</h2>

            <div style={styles.formGroup}>
              <label style={styles.label}>Tenant ID *</label>
              <input
                style={styles.input}
                type='text'
                value={createForm.tenant_id}
                onChange={e =>
                  setCreateForm({ ...createForm, tenant_id: e.target.value })
                }
                required
                placeholder='Enter tenant ID'
              />
            </div>

            <div style={styles.formGroup}>
              <label style={styles.label}>Notification Channels</label>
              <div style={styles.checkboxGroup}>
                {availableChannels.map(channel => (
                  <div key={channel} style={styles.checkboxItem}>
                    <input
                      type='checkbox'
                      id={`channel-${channel}`}
                      checked={createForm.channels.includes(channel)}
                      onChange={e =>
                        handleChannelChange(channel, e.target.checked)
                      }
                    />
                    <label htmlFor={`channel-${channel}`}>
                      {channel.toUpperCase()}
                    </label>
                  </div>
                ))}
              </div>
            </div>

            <div style={styles.formGroup}>
              <label style={styles.label}>Severity Levels</label>
              <div style={styles.checkboxGroup}>
                {availableSeverities.map(severity => (
                  <div key={severity} style={styles.checkboxItem}>
                    <input
                      type='checkbox'
                      id={`severity-${severity}`}
                      checked={createForm.severity_levels.includes(severity)}
                      onChange={e =>
                        handleSeverityChange(severity, e.target.checked)
                      }
                    />
                    <label htmlFor={`severity-${severity}`}>
                      {severity.toUpperCase()}
                    </label>
                  </div>
                ))}
              </div>
            </div>

            <div style={styles.formGroup}>
              <label style={styles.label}>Incident Types</label>
              <div style={styles.checkboxGroup}>
                {availableIncidentTypes.map(type => (
                  <div key={type} style={styles.checkboxItem}>
                    <input
                      type='checkbox'
                      id={`type-${type}`}
                      checked={createForm.incident_types.includes(type)}
                      onChange={e =>
                        handleIncidentTypeChange(type, e.target.checked)
                      }
                    />
                    <label htmlFor={`type-${type}`}>{type.toUpperCase()}</label>
                  </div>
                ))}
              </div>
            </div>

            <div style={{ textAlign: 'right', marginTop: '24px' }}>
              <button
                style={{
                  ...styles.button,
                  ...styles.secondaryButton,
                  marginRight: '8px',
                }}
                onClick={() => setCreateDialogOpen(false)}
              >
                Cancel
              </button>
              <button
                style={{ ...styles.button, ...styles.primaryButton }}
                onClick={handleCreateSubscription}
                disabled={
                  !createForm.tenant_id ||
                  createForm.channels.length === 0 ||
                  loading
                }
              >
                Create Subscription
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default NotificationSubscriptionsPage;
