import React, { useState, useEffect, useCallback } from 'react';

// Types
interface Banner {
  id: string;
  message: string;
  type: 'info' | 'warning' | 'critical';
  is_active: boolean;
  start_time?: string;
  end_time?: string;
  target_audience: 'all' | 'admins' | 'tenants';
  incident_id?: string;
  created_by: string;
  tenant_id: string;
  created_at: string;
  updated_at: string;
}

interface CreateBannerForm {
  message: string;
  type: 'info' | 'warning' | 'critical';
  start_time: string;
  end_time: string;
  target_audience: 'all' | 'admins' | 'tenants';
  incident_id: string;
}

// API service
class BannerService {
  private baseUrl = '/api/v1/banners';

  async getBanners(
    filters: {
      tenant_id?: string;
      type?: string;
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
      throw new Error('Failed to fetch banners');
    }
    return response.json();
  }

  async createBanner(
    banner: CreateBannerForm & { created_by: string; tenant_id: string }
  ) {
    const response = await fetch(this.baseUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(banner),
    });
    if (!response.ok) {
      throw new Error('Failed to create banner');
    }
    return response.json();
  }

  async updateBanner(id: string, updates: Partial<Banner>) {
    const response = await fetch(`${this.baseUrl}/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates),
    });
    if (!response.ok) {
      throw new Error('Failed to update banner');
    }
    return response.json();
  }

  async deleteBanner(id: string) {
    const response = await fetch(`${this.baseUrl}/${id}`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      throw new Error('Failed to delete banner');
    }
  }

  async getActiveBanners(audience?: string) {
    const params = audience ? `?target_audience=${audience}` : '';
    const response = await fetch(`${this.baseUrl}/active${params}`);
    if (!response.ok) {
      throw new Error('Failed to get active banners');
    }
    return response.json();
  }
}

const bannerService = new BannerService();

// Helper functions
const getTypeColor = (type: string): string => {
  switch (type) {
    case 'info':
      return '#2196f3';
    case 'warning':
      return '#ff9800';
    case 'critical':
      return '#f44336';
    default:
      return '#666';
  }
};

const formatDateTime = (dateString: string): string => {
  return new Date(dateString).toLocaleString();
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
  bannerPreview: {
    padding: '12px',
    borderRadius: '4px',
    marginBottom: '16px',
    fontWeight: 'bold' as const,
    textAlign: 'center' as const,
  },
};

// Main component
const BannersPage: React.FC = () => {
  const [banners, setBanners] = useState<Banner[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [totalCount, setTotalCount] = useState(0);

  // Filters
  const [typeFilter, setTypeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  // Pagination
  const [page, setPage] = useState(0);
  const [rowsPerPage] = useState(25);

  // Dialogs
  const [createDialogOpen, setCreateDialogOpen] = useState(false);

  // Form state
  const [createForm, setCreateForm] = useState<CreateBannerForm>({
    message: '',
    type: 'info',
    start_time: '',
    end_time: '',
    target_audience: 'all',
    incident_id: '',
  });

  // Load banners
  const loadBanners = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await bannerService.getBanners({
        type: typeFilter || undefined,
        is_active:
          statusFilter === 'active'
            ? true
            : statusFilter === 'inactive'
              ? false
              : undefined,
        page: page + 1,
        page_size: rowsPerPage,
      });

      setBanners(response.banners);
      setTotalCount(response.pagination.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load banners');
    } finally {
      setLoading(false);
    }
  }, [page, rowsPerPage, typeFilter, statusFilter]);

  // Effects
  useEffect(() => {
    loadBanners();
  }, [loadBanners]);

  // Event handlers
  const handleCreateBanner = async () => {
    try {
      setLoading(true);

      await bannerService.createBanner({
        ...createForm,
        created_by: 'current-user',
        tenant_id: 'current-tenant',
      });

      setCreateDialogOpen(false);
      setCreateForm({
        message: '',
        type: 'info',
        start_time: '',
        end_time: '',
        target_audience: 'all',
        incident_id: '',
      });

      await loadBanners();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create banner');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleActive = async (banner: Banner) => {
    try {
      setLoading(true);
      await bannerService.updateBanner(banner.id, {
        is_active: !banner.is_active,
      });
      await loadBanners();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update banner');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteBanner = async (banner: Banner) => {
    if (!confirm(`Are you sure you want to delete this banner?`)) {
      return;
    }

    try {
      setLoading(true);
      await bannerService.deleteBanner(banner.id);
      await loadBanners();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete banner');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <h1 style={styles.title}>Banner Management</h1>
        <p style={styles.subtitle}>
          Create and manage system-wide announcement banners
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
            <label style={styles.label}>Type</label>
            <select
              style={styles.select}
              value={typeFilter}
              onChange={e => setTypeFilter(e.target.value)}
            >
              <option value=''>All Types</option>
              <option value='info'>Info</option>
              <option value='warning'>Warning</option>
              <option value='critical'>Critical</option>
            </select>
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
              onClick={loadBanners}
              disabled={loading}
            >
              🔄 Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Banners Table */}
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
              <th style={styles.th}>Message</th>
              <th style={styles.th}>Type</th>
              <th style={styles.th}>Audience</th>
              <th style={styles.th}>Status</th>
              <th style={styles.th}>Schedule</th>
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
            ) : banners.length === 0 ? (
              <tr>
                <td colSpan={7} style={{ ...styles.td, textAlign: 'center' }}>
                  No banners found
                </td>
              </tr>
            ) : (
              banners.map(banner => (
                <tr key={banner.id}>
                  <td style={styles.td}>
                    <div
                      style={{
                        ...styles.bannerPreview,
                        backgroundColor: getTypeColor(banner.type),
                        color: '#fff',
                        fontSize: '12px',
                        padding: '6px 12px',
                      }}
                    >
                      {banner.message}
                    </div>
                  </td>

                  <td style={styles.td}>
                    <span
                      style={{
                        ...styles.chip,
                        backgroundColor: getTypeColor(banner.type),
                      }}
                    >
                      {banner.type.toUpperCase()}
                    </span>
                  </td>

                  <td style={styles.td}>
                    <span
                      style={{
                        ...styles.chip,
                        backgroundColor: '#e0e0e0',
                        color: '#333',
                      }}
                    >
                      {banner.target_audience.toUpperCase()}
                    </span>
                  </td>

                  <td style={styles.td}>
                    <span
                      style={{
                        ...styles.chip,
                        backgroundColor: banner.is_active ? '#4caf50' : '#666',
                      }}
                    >
                      {banner.is_active ? 'ACTIVE' : 'INACTIVE'}
                    </span>
                  </td>

                  <td style={styles.td}>
                    {banner.start_time ? (
                      <div style={{ fontSize: '12px' }}>
                        <div>Start: {formatDateTime(banner.start_time)}</div>
                        {banner.end_time && (
                          <div>End: {formatDateTime(banner.end_time)}</div>
                        )}
                      </div>
                    ) : (
                      'Immediate'
                    )}
                  </td>

                  <td style={styles.td}>{formatDateTime(banner.created_at)}</td>

                  <td style={styles.td}>
                    <button
                      style={{
                        ...styles.button,
                        backgroundColor: banner.is_active
                          ? '#ff9800'
                          : '#4caf50',
                        color: '#fff',
                        marginRight: '4px',
                        padding: '4px 8px',
                        fontSize: '12px',
                      }}
                      onClick={() => handleToggleActive(banner)}
                    >
                      {banner.is_active ? 'Deactivate' : 'Activate'}
                    </button>

                    <button
                      style={{
                        ...styles.button,
                        backgroundColor: '#f44336',
                        color: '#fff',
                        padding: '4px 8px',
                      }}
                      onClick={() => handleDeleteBanner(banner)}
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
        title='Create New Banner'
      >
        +
      </button>

      {/* Create Banner Modal */}
      {createDialogOpen && (
        <div style={styles.modal} onClick={() => setCreateDialogOpen(false)}>
          <div style={styles.modalContent} onClick={e => e.stopPropagation()}>
            <h2>Create New Banner</h2>

            <div style={styles.formGroup}>
              <label style={styles.label}>Message *</label>
              <textarea
                style={styles.textarea}
                value={createForm.message}
                onChange={e =>
                  setCreateForm({ ...createForm, message: e.target.value })
                }
                required
                placeholder='Enter the banner message...'
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
                <label style={styles.label}>Type</label>
                <select
                  style={styles.select}
                  value={createForm.type}
                  onChange={e =>
                    setCreateForm({
                      ...createForm,
                      type: e.target.value as 'info' | 'warning' | 'critical',
                    })
                  }
                >
                  <option value='info'>Info</option>
                  <option value='warning'>Warning</option>
                  <option value='critical'>Critical</option>
                </select>
              </div>

              <div style={styles.formGroup}>
                <label style={styles.label}>Target Audience</label>
                <select
                  style={styles.select}
                  value={createForm.target_audience}
                  onChange={e =>
                    setCreateForm({
                      ...createForm,
                      target_audience: e.target.value as
                        | 'all'
                        | 'admins'
                        | 'tenants',
                    })
                  }
                >
                  <option value='all'>All Users</option>
                  <option value='admins'>Admins Only</option>
                  <option value='tenants'>Tenants Only</option>
                </select>
              </div>
            </div>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '16px',
              }}
            >
              <div style={styles.formGroup}>
                <label style={styles.label}>Start Time (Optional)</label>
                <input
                  style={styles.input}
                  type='datetime-local'
                  value={createForm.start_time}
                  onChange={e =>
                    setCreateForm({ ...createForm, start_time: e.target.value })
                  }
                />
              </div>

              <div style={styles.formGroup}>
                <label style={styles.label}>End Time (Optional)</label>
                <input
                  style={styles.input}
                  type='datetime-local'
                  value={createForm.end_time}
                  onChange={e =>
                    setCreateForm({ ...createForm, end_time: e.target.value })
                  }
                />
              </div>
            </div>

            <div style={styles.formGroup}>
              <label style={styles.label}>Related Incident ID (Optional)</label>
              <input
                style={styles.input}
                type='text'
                value={createForm.incident_id}
                onChange={e =>
                  setCreateForm({ ...createForm, incident_id: e.target.value })
                }
                placeholder='Link to an incident if applicable'
              />
            </div>

            {/* Banner Preview */}
            {createForm.message && (
              <div style={styles.formGroup}>
                <label style={styles.label}>Preview</label>
                <div
                  style={{
                    ...styles.bannerPreview,
                    backgroundColor: getTypeColor(createForm.type),
                    color: '#fff',
                  }}
                >
                  {createForm.message}
                </div>
              </div>
            )}

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
                onClick={handleCreateBanner}
                disabled={!createForm.message || loading}
              >
                Create Banner
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BannersPage;
