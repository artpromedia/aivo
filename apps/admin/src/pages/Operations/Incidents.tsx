import React, { useState, useEffect, useCallback } from 'react';

// Types
interface Incident {
  id: string;
  title: string;
  description?: string;
  status: 'investigating' | 'identified' | 'monitoring' | 'resolved';
  severity: 'low' | 'medium' | 'high' | 'critical';
  started_at: string;
  resolved_at?: string;
  affected_services: string[];
  statuspage_incident_id?: string;
  statuspage_status?: string;
  auto_resolved: boolean;
  notifications_sent: boolean;
  last_notification_at?: string;
  resolution_summary?: string;
  created_by: string;
  tenant_id: string;
  created_at: string;
  updated_at: string;
}

interface CreateIncidentForm {
  title: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  affected_services: string[];
  auto_create_banner: boolean;
  banner_message_override: string;
}

interface UpdateIncidentForm {
  title: string;
  description: string;
  status: 'investigating' | 'identified' | 'monitoring' | 'resolved';
  severity: 'low' | 'medium' | 'high' | 'critical';
  affected_services: string[];
  resolution_summary: string;
  update_message: string;
}

// API service
class IncidentService {
  private baseUrl = '/api/v1/incidents';

  async getIncidents(
    filters: {
      tenant_id?: string;
      status?: string;
      severity?: string;
      service?: string;
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
      throw new Error('Failed to fetch incidents');
    }
    return response.json();
  }

  async createIncident(
    incident: CreateIncidentForm & { created_by: string; tenant_id: string }
  ) {
    const response = await fetch(this.baseUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(incident),
    });
    if (!response.ok) {
      throw new Error('Failed to create incident');
    }
    return response.json();
  }

  async updateIncident(id: string, updates: Partial<UpdateIncidentForm>) {
    const response = await fetch(`${this.baseUrl}/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates),
    });
    if (!response.ok) {
      throw new Error('Failed to update incident');
    }
    return response.json();
  }

  async deleteIncident(id: string) {
    const response = await fetch(`${this.baseUrl}/${id}`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      throw new Error('Failed to delete incident');
    }
  }

  async getActiveCount(tenant_id?: string) {
    const params = tenant_id ? `?tenant_id=${tenant_id}` : '';
    const response = await fetch(`${this.baseUrl}/active/count${params}`);
    if (!response.ok) {
      throw new Error('Failed to get active count');
    }
    return response.json();
  }
}

const incidentService = new IncidentService();

// Helper functions
const getSeverityColor = (severity: string): string => {
  switch (severity) {
    case 'low':
      return '#2196f3';
    case 'medium':
      return '#ff9800';
    case 'high':
      return '#f44336';
    case 'critical':
      return '#d32f2f';
    default:
      return '#666';
  }
};

const getStatusColor = (status: string): string => {
  switch (status) {
    case 'investigating':
      return '#f44336';
    case 'identified':
      return '#ff9800';
    case 'monitoring':
      return '#2196f3';
    case 'resolved':
      return '#4caf50';
    default:
      return '#666';
  }
};

const formatDateTime = (dateString: string): string => {
  return new Date(dateString).toLocaleString();
};

const calculateDuration = (startTime: string, endTime?: string): string => {
  const start = new Date(startTime);
  const end = endTime ? new Date(endTime) : new Date();
  const diff = end.getTime() - start.getTime();

  const hours = Math.floor(diff / (1000 * 60 * 60));
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }
  return `${minutes}m`;
};

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
  cardGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '16px',
    marginBottom: '24px',
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
  textarea: {
    width: '100%',
    padding: '8px',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '14px',
    resize: 'vertical' as const,
    minHeight: '80px',
    boxSizing: 'border-box' as const,
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
const IncidentsPage: React.FC = () => {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [totalCount, setTotalCount] = useState(0);
  const [activeCount, setActiveCount] = useState(0);

  // Filters
  const [statusFilter, setStatusFilter] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const [serviceFilter, setServiceFilter] = useState('');

  // Pagination
  const [page, setPage] = useState(0);
  const [rowsPerPage] = useState(25);

  // Dialogs
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(
    null
  );

  // Form states
  const [createForm, setCreateForm] = useState<CreateIncidentForm>({
    title: '',
    description: '',
    severity: 'medium',
    affected_services: [],
    auto_create_banner: true,
    banner_message_override: '',
  });

  const [updateForm, setUpdateForm] = useState<UpdateIncidentForm>({
    title: '',
    description: '',
    status: 'investigating',
    severity: 'medium',
    affected_services: [],
    resolution_summary: '',
    update_message: '',
  });

  // Available services
  const availableServices = [
    'Authentication Service',
    'Payment Service',
    'User Management',
    'Analytics Service',
    'Gateway',
    'Admin Panel',
    'Blog Service',
  ];

  // Load incidents
  const loadIncidents = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await incidentService.getIncidents({
        status: statusFilter || undefined,
        severity: severityFilter || undefined,
        service: serviceFilter || undefined,
        page: page + 1,
        page_size: rowsPerPage,
      });

      setIncidents(response.incidents);
      setTotalCount(response.pagination.total);

      // Get active count
      const countResponse = await incidentService.getActiveCount();
      setActiveCount(countResponse.active_incidents);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load incidents');
    } finally {
      setLoading(false);
    }
  }, [page, rowsPerPage, statusFilter, severityFilter, serviceFilter]);

  // Effects
  useEffect(() => {
    loadIncidents();
  }, [loadIncidents]);

  // Event handlers
  const handleCreateIncident = async () => {
    try {
      setLoading(true);

      await incidentService.createIncident({
        ...createForm,
        created_by: 'current-user',
        tenant_id: 'current-tenant',
      });

      setCreateDialogOpen(false);
      setCreateForm({
        title: '',
        description: '',
        severity: 'medium',
        affected_services: [],
        auto_create_banner: true,
        banner_message_override: '',
      });

      await loadIncidents();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to create incident'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateIncident = async () => {
    if (!selectedIncident) return;

    try {
      setLoading(true);

      await incidentService.updateIncident(selectedIncident.id, updateForm);

      setEditDialogOpen(false);
      setSelectedIncident(null);

      await loadIncidents();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to update incident'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteIncident = async (incident: Incident) => {
    if (
      !confirm(`Are you sure you want to delete incident "${incident.title}"?`)
    ) {
      return;
    }

    try {
      setLoading(true);
      await incidentService.deleteIncident(incident.id);
      await loadIncidents();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to delete incident'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleEditClick = (incident: Incident) => {
    setSelectedIncident(incident);
    setUpdateForm({
      title: incident.title,
      description: incident.description || '',
      status: incident.status,
      severity: incident.severity,
      affected_services: incident.affected_services,
      resolution_summary: incident.resolution_summary || '',
      update_message: '',
    });
    setEditDialogOpen(true);
  };

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <h1 style={styles.title}>Incident Center</h1>
        <p style={styles.subtitle}>
          Monitor and manage system incidents and maintenance windows
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

      {/* Summary Cards */}
      <div style={styles.cardGrid}>
        <div style={styles.card}>
          <h3 style={{ margin: 0, color: '#f44336' }}>🚨 {activeCount}</h3>
          <p style={{ margin: '4px 0 0 0', color: '#666' }}>Active Incidents</p>
        </div>

        <div style={styles.card}>
          <h3 style={{ margin: 0, color: '#2196f3' }}>📊 {totalCount}</h3>
          <p style={{ margin: '4px 0 0 0', color: '#666' }}>Total Incidents</p>
        </div>
      </div>

      {/* Filters */}
      <div style={styles.filters}>
        <div style={styles.filterGrid}>
          <div>
            <label style={styles.label}>Status</label>
            <select
              style={styles.select}
              value={statusFilter}
              onChange={e => setStatusFilter(e.target.value)}
            >
              <option value=''>All</option>
              <option value='investigating'>Investigating</option>
              <option value='identified'>Identified</option>
              <option value='monitoring'>Monitoring</option>
              <option value='resolved'>Resolved</option>
            </select>
          </div>

          <div>
            <label style={styles.label}>Severity</label>
            <select
              style={styles.select}
              value={severityFilter}
              onChange={e => setSeverityFilter(e.target.value)}
            >
              <option value=''>All</option>
              <option value='low'>Low</option>
              <option value='medium'>Medium</option>
              <option value='high'>High</option>
              <option value='critical'>Critical</option>
            </select>
          </div>

          <div>
            <label style={styles.label}>Service</label>
            <select
              style={styles.select}
              value={serviceFilter}
              onChange={e => setServiceFilter(e.target.value)}
            >
              <option value=''>All Services</option>
              {availableServices.map(service => (
                <option key={service} value={service}>
                  {service}
                </option>
              ))}
            </select>
          </div>

          <div>
            <button
              style={{ ...styles.button, ...styles.secondaryButton }}
              onClick={loadIncidents}
              disabled={loading}
            >
              🔄 Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Incidents Table */}
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
              <th style={styles.th}>Title</th>
              <th style={styles.th}>Status</th>
              <th style={styles.th}>Severity</th>
              <th style={styles.th}>Services</th>
              <th style={styles.th}>Duration</th>
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
            ) : incidents.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ ...styles.td, textAlign: 'center' }}>
                  No incidents found
                </td>
              </tr>
            ) : (
              incidents.map(incident => (
                <tr key={incident.id}>
                  <td style={styles.td}>
                    <strong>{incident.title}</strong>
                    {incident.description && (
                      <div
                        style={{
                          fontSize: '12px',
                          color: '#666',
                          marginTop: '4px',
                        }}
                      >
                        {incident.description.substring(0, 100)}
                        {incident.description.length > 100 && '...'}
                      </div>
                    )}
                  </td>

                  <td style={styles.td}>
                    <span
                      style={{
                        ...styles.chip,
                        backgroundColor: getStatusColor(incident.status),
                      }}
                    >
                      {incident.status.toUpperCase()}
                    </span>
                  </td>

                  <td style={styles.td}>
                    <span
                      style={{
                        ...styles.chip,
                        backgroundColor: getSeverityColor(incident.severity),
                      }}
                    >
                      {incident.severity.toUpperCase()}
                    </span>
                  </td>

                  <td style={styles.td}>
                    {incident.affected_services.slice(0, 2).map(service => (
                      <span
                        key={service}
                        style={{
                          ...styles.chip,
                          backgroundColor: '#e0e0e0',
                          color: '#333',
                          marginRight: '4px',
                        }}
                      >
                        {service}
                      </span>
                    ))}
                    {incident.affected_services.length > 2 && (
                      <span style={{ fontSize: '12px', color: '#666' }}>
                        +{incident.affected_services.length - 2} more
                      </span>
                    )}
                  </td>

                  <td style={styles.td}>
                    {calculateDuration(
                      incident.started_at,
                      incident.resolved_at
                    )}
                  </td>

                  <td style={styles.td}>
                    {formatDateTime(incident.created_at)}
                  </td>

                  <td style={styles.td}>
                    <button
                      style={{
                        ...styles.button,
                        ...styles.secondaryButton,
                        marginRight: '4px',
                        padding: '4px 8px',
                      }}
                      onClick={() => handleEditClick(incident)}
                    >
                      ✎
                    </button>

                    <button
                      style={{
                        ...styles.button,
                        backgroundColor: '#f44336',
                        color: '#fff',
                        padding: '4px 8px',
                      }}
                      onClick={() => handleDeleteIncident(incident)}
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
        title='Create New Incident'
      >
        +
      </button>

      {/* Create Incident Modal */}
      {createDialogOpen && (
        <div style={styles.modal} onClick={() => setCreateDialogOpen(false)}>
          <div style={styles.modalContent} onClick={e => e.stopPropagation()}>
            <h2>Create New Incident</h2>

            <div style={styles.formGroup}>
              <label style={styles.label}>Title *</label>
              <input
                style={styles.input}
                type='text'
                value={createForm.title}
                onChange={e =>
                  setCreateForm({ ...createForm, title: e.target.value })
                }
                required
              />
            </div>

            <div style={styles.formGroup}>
              <label style={styles.label}>Description</label>
              <textarea
                style={styles.textarea}
                value={createForm.description}
                onChange={e =>
                  setCreateForm({ ...createForm, description: e.target.value })
                }
              />
            </div>

            <div style={styles.formGroup}>
              <label style={styles.label}>Severity</label>
              <select
                style={styles.select}
                value={createForm.severity}
                onChange={e =>
                  setCreateForm({
                    ...createForm,
                    severity: e.target.value as
                      | 'low'
                      | 'medium'
                      | 'high'
                      | 'critical',
                  })
                }
              >
                <option value='low'>Low</option>
                <option value='medium'>Medium</option>
                <option value='high'>High</option>
                <option value='critical'>Critical</option>
              </select>
            </div>

            <div style={styles.formGroup}>
              <label style={styles.label}>Banner Message Override</label>
              <input
                style={styles.input}
                type='text'
                value={createForm.banner_message_override}
                onChange={e =>
                  setCreateForm({
                    ...createForm,
                    banner_message_override: e.target.value,
                  })
                }
                placeholder='Custom message for the incident banner'
              />
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
                onClick={handleCreateIncident}
                disabled={!createForm.title || loading}
              >
                Create Incident
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Incident Modal */}
      {editDialogOpen && selectedIncident && (
        <div style={styles.modal} onClick={() => setEditDialogOpen(false)}>
          <div style={styles.modalContent} onClick={e => e.stopPropagation()}>
            <h2>Update Incident</h2>

            <div style={styles.formGroup}>
              <label style={styles.label}>Title *</label>
              <input
                style={styles.input}
                type='text'
                value={updateForm.title}
                onChange={e =>
                  setUpdateForm({ ...updateForm, title: e.target.value })
                }
                required
              />
            </div>

            <div style={styles.formGroup}>
              <label style={styles.label}>Description</label>
              <textarea
                style={styles.textarea}
                value={updateForm.description}
                onChange={e =>
                  setUpdateForm({ ...updateForm, description: e.target.value })
                }
              />
            </div>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '16px',
              }}
            >
              <div style={styles.formGroup}>
                <label style={styles.label}>Status</label>
                <select
                  style={styles.select}
                  value={updateForm.status}
                  onChange={e =>
                    setUpdateForm({
                      ...updateForm,
                      status: e.target.value as
                        | 'investigating'
                        | 'identified'
                        | 'monitoring'
                        | 'resolved',
                    })
                  }
                >
                  <option value='investigating'>Investigating</option>
                  <option value='identified'>Identified</option>
                  <option value='monitoring'>Monitoring</option>
                  <option value='resolved'>Resolved</option>
                </select>
              </div>

              <div style={styles.formGroup}>
                <label style={styles.label}>Severity</label>
                <select
                  style={styles.select}
                  value={updateForm.severity}
                  onChange={e =>
                    setUpdateForm({
                      ...updateForm,
                      severity: e.target.value as
                        | 'low'
                        | 'medium'
                        | 'high'
                        | 'critical',
                    })
                  }
                >
                  <option value='low'>Low</option>
                  <option value='medium'>Medium</option>
                  <option value='high'>High</option>
                  <option value='critical'>Critical</option>
                </select>
              </div>
            </div>

            <div style={styles.formGroup}>
              <label style={styles.label}>Update Message</label>
              <textarea
                style={styles.textarea}
                value={updateForm.update_message}
                onChange={e =>
                  setUpdateForm({
                    ...updateForm,
                    update_message: e.target.value,
                  })
                }
                placeholder='Optional update message to send to subscribers'
              />
            </div>

            {updateForm.status === 'resolved' && (
              <div style={styles.formGroup}>
                <label style={styles.label}>Resolution Summary</label>
                <textarea
                  style={styles.textarea}
                  value={updateForm.resolution_summary}
                  onChange={e =>
                    setUpdateForm({
                      ...updateForm,
                      resolution_summary: e.target.value,
                    })
                  }
                  placeholder='Summary of how the incident was resolved'
                />
              </div>
            )}

            <div style={{ textAlign: 'right', marginTop: '24px' }}>
              <button
                style={{
                  ...styles.button,
                  ...styles.secondaryButton,
                  marginRight: '8px',
                }}
                onClick={() => setEditDialogOpen(false)}
              >
                Cancel
              </button>
              <button
                style={{ ...styles.button, ...styles.primaryButton }}
                onClick={handleUpdateIncident}
                disabled={!updateForm.title || loading}
              >
                Update Incident
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default IncidentsPage;
