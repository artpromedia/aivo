import React, { useState, useEffect } from 'react';
import './DataGovernance.css';

// Types
interface RetentionPolicy {
  id: string;
  entity_type: string;
  tenant_id?: string;
  retention_days: number;
  auto_delete_enabled: boolean;
  grace_period_days: number;
  legal_basis?: string;
  compliance_framework?: string;
  description?: string;
  created_at: string;
  updated_at: string;
  created_by: string;
}

interface DSRRequest {
  id: string;
  dsr_type: 'export' | 'delete';
  subject_id: string;
  subject_type: string;
  tenant_id?: string;
  requester_email: string;
  requester_name?: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'blocked';
  progress_percentage: number;
  requested_at: string;
  completed_at?: string;
  error_details?: string;
  export_download_url?: string;
  export_expires_at?: string;
}

interface LegalHold {
  id: string;
  name: string;
  description?: string;
  case_number?: string;
  entity_types: string[];
  subject_ids?: string[];
  tenant_id?: string;
  status: 'active' | 'released' | 'expired';
  effective_date: string;
  expiry_date?: string;
  custodian_name: string;
  custodian_email: string;
  created_at: string;
}

interface DSRStatistics {
  total_requests: number;
  by_type: Record<string, number>;
  by_status: Record<string, number>;
  average_processing_time_hours?: number;
  pending_requests: number;
  blocked_by_legal_holds: number;
  completed_last_30_days: number;
}

const DataGovernance: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'policies' | 'dsr' | 'holds'>(
    'policies'
  );

  // Policies state
  const [policies, setPolicies] = useState<RetentionPolicy[]>([]);
  const [showPolicyModal, setShowPolicyModal] = useState(false);
  const [editingPolicy, setEditingPolicy] = useState<RetentionPolicy | null>(
    null
  );

  // DSR state
  const [dsrRequests, setDsrRequests] = useState<DSRRequest[]>([]);
  const [dsrStats, setDsrStats] = useState<DSRStatistics | null>(null);
  const [showDSRModal, setShowDSRModal] = useState(false);
  const [dsrFilter, setDsrFilter] = useState<string>('all');

  // Legal holds state
  const [legalHolds, setLegalHolds] = useState<LegalHold[]>([]);
  const [showHoldModal, setShowHoldModal] = useState(false);
  const [editingHold, setEditingHold] = useState<LegalHold | null>(null);

  // Loading states
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // API base URL
  const API_BASE = '/api/data-governance';

  useEffect(() => {
    const loadInitialData = async () => {
      setLoading(true);
      try {
        await Promise.all([
          loadPolicies(),
          loadDSRRequests(),
          loadLegalHolds(),
          loadDSRStats(),
        ]);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load data');
      } finally {
        setLoading(false);
      }
    };

    loadInitialData();
  }, []);

  const loadPolicies = async () => {
    try {
      const response = await fetch(`${API_BASE}/policies/retention`);
      if (!response.ok) throw new Error('Failed to load policies');
      const data = await response.json();
      setPolicies(data.policies || []);
    } catch (err) {
       
      console.error('Error loading policies:', err);
    }
  };

  const loadDSRRequests = async () => {
    try {
      const response = await fetch(`${API_BASE}/dsr/requests?limit=50`);
      if (!response.ok) throw new Error('Failed to load DSR requests');
      const data = await response.json();
      setDsrRequests(data.requests || []);
    } catch (err) {
       
      console.error('Error loading DSR requests:', err);
    }
  };

  const loadLegalHolds = async () => {
    try {
      const response = await fetch(`${API_BASE}/holds?limit=50`);
      if (!response.ok) throw new Error('Failed to load legal holds');
      const data = await response.json();
      setLegalHolds(data.holds || []);
    } catch (err) {
       
      console.error('Error loading legal holds:', err);
    }
  };

  const loadDSRStats = async () => {
    try {
      const response = await fetch(`${API_BASE}/dsr/stats`);
      if (!response.ok) throw new Error('Failed to load DSR stats');
      const data = await response.json();
      setDsrStats(data);
    } catch (err) {
       
      console.error('Error loading DSR stats:', err);
    }
  };

  const handleCreatePolicy = async (policyData: Record<string, unknown>) => {
    try {
      const response = await fetch(
        `${API_BASE}/policies/retention/${policyData.entity_type}`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            ...policyData,
            created_by: 'admin', // TODO: Get from auth context
          }),
        }
      );

      if (!response.ok) throw new Error('Failed to create policy');
      await loadPolicies();
      setShowPolicyModal(false);
      setEditingPolicy(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create policy');
    }
  };

  const handleCreateDSRRequest = async (
    requestData: Record<string, unknown>
  ) => {
    try {
      const endpoint = requestData.dsr_type === 'export' ? 'export' : 'delete';
      const response = await fetch(`${API_BASE}/dsr/${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) throw new Error('Failed to create DSR request');
      await loadDSRRequests();
      await loadDSRStats();
      setShowDSRModal(false);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to create DSR request'
      );
    }
  };

  const handleCreateLegalHold = async (holdData: Record<string, unknown>) => {
    try {
      const response = await fetch(`${API_BASE}/holds`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...holdData,
          created_by: 'admin', // TODO: Get from auth context
        }),
      });

      if (!response.ok) throw new Error('Failed to create legal hold');
      await loadLegalHolds();
      setShowHoldModal(false);
      setEditingHold(null);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to create legal hold'
      );
    }
  };

  const handleReleaseLegalHold = async (holdId: string) => {
    if (
      !confirm(
        'Are you sure you want to release this legal hold? This action cannot be undone.'
      )
    ) {
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/holds/${holdId}`, {
        method: 'DELETE',
      });

      if (!response.ok) throw new Error('Failed to release legal hold');
      await loadLegalHolds();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to release legal hold'
      );
    }
  };

  const handleDownloadExport = async (request: DSRRequest) => {
    try {
      const response = await fetch(
        `${API_BASE}/requests/${request.id}/download`
      );
      if (!response.ok) throw new Error('Failed to download export');

      // Create download link
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `export_${request.subject_id}.zip`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to download export'
      );
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
      case 'completed':
        return 'success';
      case 'pending':
      case 'processing':
        return 'warning';
      case 'failed':
      case 'blocked':
        return 'danger';
      default:
        return 'secondary';
    }
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const filteredDSRRequests = dsrRequests.filter(request => {
    if (dsrFilter === 'all') return true;
    return request.status === dsrFilter;
  });

  if (loading) {
    return (
      <div className='data-governance-page'>
        <div className='loading-spinner'>
          <div className='spinner'></div>
          <p>Loading data governance...</p>
        </div>
      </div>
    );
  }

  return (
    <div className='data-governance-page'>
      <div className='page-header'>
        <h1>Data Governance & Privacy</h1>
        <p>
          Manage data retention policies, subject rights requests, and legal
          holds
        </p>
      </div>

      {error && (
        <div className='error-banner'>
          <span className='error-icon'>⚠️</span>
          <span>{error}</span>
          <button onClick={() => setError(null)} className='close-btn'>
            ×
          </button>
        </div>
      )}

      {/* Statistics Dashboard */}
      {dsrStats && (
        <div className='stats-dashboard'>
          <div className='stat-card'>
            <h3>Total DSR Requests</h3>
            <div className='stat-value'>{dsrStats.total_requests}</div>
          </div>
          <div className='stat-card'>
            <h3>Pending</h3>
            <div className='stat-value warning'>
              {dsrStats.pending_requests}
            </div>
          </div>
          <div className='stat-card'>
            <h3>Blocked by Legal Holds</h3>
            <div className='stat-value danger'>
              {dsrStats.blocked_by_legal_holds}
            </div>
          </div>
          <div className='stat-card'>
            <h3>Completed (30d)</h3>
            <div className='stat-value success'>
              {dsrStats.completed_last_30_days}
            </div>
          </div>
          {dsrStats.average_processing_time_hours && (
            <div className='stat-card'>
              <h3>Avg Processing Time</h3>
              <div className='stat-value'>
                {dsrStats.average_processing_time_hours.toFixed(1)}h
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab Navigation */}
      <div className='tab-navigation'>
        <button
          className={`tab-btn ${activeTab === 'policies' ? 'active' : ''}`}
          onClick={() => setActiveTab('policies')}
        >
          Retention Policies ({policies.length})
        </button>
        <button
          className={`tab-btn ${activeTab === 'dsr' ? 'active' : ''}`}
          onClick={() => setActiveTab('dsr')}
        >
          DSR Requests ({dsrRequests.length})
        </button>
        <button
          className={`tab-btn ${activeTab === 'holds' ? 'active' : ''}`}
          onClick={() => setActiveTab('holds')}
        >
          Legal Holds ({legalHolds.filter(h => h.status === 'active').length})
        </button>
      </div>

      {/* Tab Content */}
      <div className='tab-content'>
        {activeTab === 'policies' && (
          <div className='policies-tab'>
            <div className='section-header'>
              <h2>Data Retention Policies</h2>
              <button
                className='btn btn-primary'
                onClick={() => setShowPolicyModal(true)}
              >
                Create Policy
              </button>
            </div>

            <div className='policies-grid'>
              {policies.map(policy => (
                <div key={policy.id} className='policy-card'>
                  <div className='policy-header'>
                    <h3>{policy.entity_type}</h3>
                    {policy.tenant_id && (
                      <span className='tenant-badge'>{policy.tenant_id}</span>
                    )}
                  </div>
                  <div className='policy-details'>
                    <div className='policy-row'>
                      <span>Retention Period:</span>
                      <strong>{policy.retention_days} days</strong>
                    </div>
                    <div className='policy-row'>
                      <span>Auto Delete:</span>
                      <span
                        className={`status-badge ${policy.auto_delete_enabled ? 'success' : 'warning'}`}
                      >
                        {policy.auto_delete_enabled ? 'Enabled' : 'Disabled'}
                      </span>
                    </div>
                    <div className='policy-row'>
                      <span>Grace Period:</span>
                      <span>{policy.grace_period_days} days</span>
                    </div>
                    {policy.compliance_framework && (
                      <div className='policy-row'>
                        <span>Framework:</span>
                        <span className='framework-badge'>
                          {policy.compliance_framework}
                        </span>
                      </div>
                    )}
                    {policy.description && (
                      <div className='policy-description'>
                        {policy.description}
                      </div>
                    )}
                  </div>
                  <div className='policy-actions'>
                    <button
                      className='btn btn-secondary btn-sm'
                      onClick={() => {
                        setEditingPolicy(policy);
                        setShowPolicyModal(true);
                      }}
                    >
                      Edit
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {policies.length === 0 && (
              <div className='empty-state'>
                <p>No retention policies configured</p>
                <button
                  className='btn btn-primary'
                  onClick={() => setShowPolicyModal(true)}
                >
                  Create Your First Policy
                </button>
              </div>
            )}
          </div>
        )}

        {activeTab === 'dsr' && (
          <div className='dsr-tab'>
            <div className='section-header'>
              <h2>Data Subject Rights Requests</h2>
              <div className='dsr-controls'>
                <select
                  value={dsrFilter}
                  onChange={e => setDsrFilter(e.target.value)}
                  className='filter-select'
                >
                  <option value='all'>All Requests</option>
                  <option value='pending'>Pending</option>
                  <option value='processing'>Processing</option>
                  <option value='completed'>Completed</option>
                  <option value='failed'>Failed</option>
                  <option value='blocked'>Blocked</option>
                </select>
                <button
                  className='btn btn-primary'
                  onClick={() => setShowDSRModal(true)}
                >
                  New DSR Request
                </button>
              </div>
            </div>

            <div className='dsr-table'>
              <table>
                <thead>
                  <tr>
                    <th>Request ID</th>
                    <th>Type</th>
                    <th>Subject</th>
                    <th>Requester</th>
                    <th>Status</th>
                    <th>Progress</th>
                    <th>Requested</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredDSRRequests.map(request => (
                    <tr key={request.id}>
                      <td>
                        <code className='request-id'>
                          {request.id.substring(0, 8)}...
                        </code>
                      </td>
                      <td>
                        <span className={`type-badge ${request.dsr_type}`}>
                          {request.dsr_type.toUpperCase()}
                        </span>
                      </td>
                      <td>
                        <div>
                          <div>{request.subject_id}</div>
                          <small className='subject-type'>
                            {request.subject_type}
                          </small>
                        </div>
                      </td>
                      <td>
                        <div>
                          <div>{request.requester_name || 'N/A'}</div>
                          <small>{request.requester_email}</small>
                        </div>
                      </td>
                      <td>
                        <span
                          className={`status-badge ${getStatusColor(request.status)}`}
                        >
                          {request.status}
                        </span>
                      </td>
                      <td>
                        <div className='progress-bar'>
                          <div
                            className='progress-fill'
                            style={{ width: `${request.progress_percentage}%` }}
                          ></div>
                        </div>
                        <small>{request.progress_percentage}%</small>
                      </td>
                      <td>{formatDateTime(request.requested_at)}</td>
                      <td>
                        <div className='action-buttons'>
                          {request.status === 'completed' &&
                            request.dsr_type === 'export' && (
                              <button
                                className='btn btn-sm btn-primary'
                                onClick={() => handleDownloadExport(request)}
                              >
                                Download
                              </button>
                            )}
                          {request.error_details && (
                            <button
                              className='btn btn-sm btn-secondary'
                              onClick={() => alert(request.error_details)}
                            >
                              View Error
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {filteredDSRRequests.length === 0 && (
                <div className='empty-state'>
                  <p>No DSR requests found</p>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'holds' && (
          <div className='holds-tab'>
            <div className='section-header'>
              <h2>Legal Holds</h2>
              <button
                className='btn btn-primary'
                onClick={() => setShowHoldModal(true)}
              >
                Create Legal Hold
              </button>
            </div>

            <div className='holds-grid'>
              {legalHolds.map(hold => (
                <div key={hold.id} className='hold-card'>
                  <div className='hold-header'>
                    <h3>{hold.name}</h3>
                    <span
                      className={`status-badge ${getStatusColor(hold.status)}`}
                    >
                      {hold.status}
                    </span>
                  </div>
                  <div className='hold-details'>
                    {hold.case_number && (
                      <div className='hold-row'>
                        <span>Case Number:</span>
                        <strong>{hold.case_number}</strong>
                      </div>
                    )}
                    <div className='hold-row'>
                      <span>Entity Types:</span>
                      <div className='entity-types'>
                        {hold.entity_types.map(type => (
                          <span key={type} className='entity-badge'>
                            {type}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div className='hold-row'>
                      <span>Custodian:</span>
                      <div>
                        <div>{hold.custodian_name}</div>
                        <small>{hold.custodian_email}</small>
                      </div>
                    </div>
                    <div className='hold-row'>
                      <span>Effective:</span>
                      <span>{formatDateTime(hold.effective_date)}</span>
                    </div>
                    {hold.expiry_date && (
                      <div className='hold-row'>
                        <span>Expires:</span>
                        <span>{formatDateTime(hold.expiry_date)}</span>
                      </div>
                    )}
                    {hold.subject_ids && hold.subject_ids.length > 0 && (
                      <div className='hold-row'>
                        <span>Subjects:</span>
                        <span>{hold.subject_ids.length} specific subjects</span>
                      </div>
                    )}
                    {hold.description && (
                      <div className='hold-description'>{hold.description}</div>
                    )}
                  </div>
                  <div className='hold-actions'>
                    {hold.status === 'active' && (
                      <button
                        className='btn btn-danger btn-sm'
                        onClick={() => handleReleaseLegalHold(hold.id)}
                      >
                        Release Hold
                      </button>
                    )}
                    <button
                      className='btn btn-secondary btn-sm'
                      onClick={() => {
                        setEditingHold(hold);
                        setShowHoldModal(true);
                      }}
                    >
                      Edit
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {legalHolds.length === 0 && (
              <div className='empty-state'>
                <p>No legal holds configured</p>
                <button
                  className='btn btn-primary'
                  onClick={() => setShowHoldModal(true)}
                >
                  Create Your First Legal Hold
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Modals */}
      {showPolicyModal && (
        <PolicyModal
          policy={editingPolicy}
          onSave={handleCreatePolicy}
          onClose={() => {
            setShowPolicyModal(false);
            setEditingPolicy(null);
          }}
        />
      )}

      {showDSRModal && (
        <DSRModal
          onSave={handleCreateDSRRequest}
          onClose={() => setShowDSRModal(false)}
        />
      )}

      {showHoldModal && (
        <LegalHoldModal
          hold={editingHold}
          onSave={handleCreateLegalHold}
          onClose={() => {
            setShowHoldModal(false);
            setEditingHold(null);
          }}
        />
      )}
    </div>
  );
};

// Policy Modal Component
const PolicyModal: React.FC<{
  policy?: RetentionPolicy | null;
  onSave: (data: Record<string, unknown>) => void;
  onClose: () => void;
}> = ({ policy, onSave, onClose }) => {
  const [formData, setFormData] = useState({
    entity_type: policy?.entity_type || 'user',
    tenant_id: policy?.tenant_id || '',
    retention_days: policy?.retention_days || 365,
    auto_delete_enabled: policy?.auto_delete_enabled ?? true,
    grace_period_days: policy?.grace_period_days || 30,
    legal_basis: policy?.legal_basis || '',
    compliance_framework: policy?.compliance_framework || '',
    description: policy?.description || '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave({
      ...formData,
      tenant_id: formData.tenant_id || undefined,
    });
  };

  return (
    <div className='modal-overlay'>
      <div className='modal'>
        <div className='modal-header'>
          <h2>{policy ? 'Edit' : 'Create'} Retention Policy</h2>
          <button onClick={onClose} className='close-btn'>
            ×
          </button>
        </div>
        <form onSubmit={handleSubmit} className='modal-body'>
          <div className='form-group'>
            <label>Entity Type</label>
            <select
              value={formData.entity_type}
              onChange={e =>
                setFormData({ ...formData, entity_type: e.target.value })
              }
              required
            >
              <option value='user'>User</option>
              <option value='student'>Student</option>
              <option value='employee'>Employee</option>
              <option value='customer'>Customer</option>
              <option value='tenant'>Tenant</option>
              <option value='session'>Session</option>
              <option value='log'>Log</option>
              <option value='document'>Document</option>
              <option value='message'>Message</option>
              <option value='transaction'>Transaction</option>
            </select>
          </div>

          <div className='form-group'>
            <label>Tenant ID (optional)</label>
            <input
              type='text'
              value={formData.tenant_id}
              onChange={e =>
                setFormData({ ...formData, tenant_id: e.target.value })
              }
              placeholder='Leave empty for global policy'
            />
          </div>

          <div className='form-group'>
            <label>Retention Period (days)</label>
            <input
              type='number'
              min='1'
              max='9999'
              value={formData.retention_days}
              onChange={e =>
                setFormData({
                  ...formData,
                  retention_days: parseInt(e.target.value),
                })
              }
              required
            />
          </div>

          <div className='form-group'>
            <label>Grace Period (days)</label>
            <input
              type='number'
              min='0'
              max='365'
              value={formData.grace_period_days}
              onChange={e =>
                setFormData({
                  ...formData,
                  grace_period_days: parseInt(e.target.value),
                })
              }
              required
            />
          </div>

          <div className='form-group checkbox-group'>
            <label>
              <input
                type='checkbox'
                checked={formData.auto_delete_enabled}
                onChange={e =>
                  setFormData({
                    ...formData,
                    auto_delete_enabled: e.target.checked,
                  })
                }
              />
              Enable automatic deletion
            </label>
          </div>

          <div className='form-group'>
            <label>Compliance Framework</label>
            <select
              value={formData.compliance_framework}
              onChange={e =>
                setFormData({
                  ...formData,
                  compliance_framework: e.target.value,
                })
              }
            >
              <option value=''>Select framework</option>
              <option value='FERPA'>FERPA</option>
              <option value='COPPA'>COPPA</option>
              <option value='GDPR'>GDPR</option>
              <option value='CCPA'>CCPA</option>
              <option value='HIPAA'>HIPAA</option>
            </select>
          </div>

          <div className='form-group'>
            <label>Legal Basis</label>
            <input
              type='text'
              value={formData.legal_basis}
              onChange={e =>
                setFormData({ ...formData, legal_basis: e.target.value })
              }
              placeholder='e.g., Legitimate interest, Contract performance'
            />
          </div>

          <div className='form-group'>
            <label>Description</label>
            <textarea
              value={formData.description}
              onChange={e =>
                setFormData({ ...formData, description: e.target.value })
              }
              placeholder='Describe the purpose and scope of this retention policy'
              rows={3}
            />
          </div>

          <div className='modal-actions'>
            <button
              type='button'
              onClick={onClose}
              className='btn btn-secondary'
            >
              Cancel
            </button>
            <button type='submit' className='btn btn-primary'>
              {policy ? 'Update' : 'Create'} Policy
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// DSR Modal Component
const DSRModal: React.FC<{
  onSave: (data: Record<string, unknown>) => void;
  onClose: () => void;
}> = ({ onSave, onClose }) => {
  const [formData, setFormData] = useState({
    dsr_type: 'export' as 'export' | 'delete',
    subject_id: '',
    subject_type: 'user',
    tenant_id: '',
    requester_email: '',
    requester_name: '',
    legal_basis: '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave({
      ...formData,
      tenant_id: formData.tenant_id || undefined,
    });
  };

  return (
    <div className='modal-overlay'>
      <div className='modal'>
        <div className='modal-header'>
          <h2>Create DSR Request</h2>
          <button onClick={onClose} className='close-btn'>
            ×
          </button>
        </div>
        <form onSubmit={handleSubmit} className='modal-body'>
          <div className='form-group'>
            <label>Request Type</label>
            <select
              value={formData.dsr_type}
              onChange={e =>
                setFormData({
                  ...formData,
                  dsr_type: e.target.value as 'export' | 'delete',
                })
              }
              required
            >
              <option value='export'>Data Export</option>
              <option value='delete'>Data Deletion</option>
            </select>
          </div>

          <div className='form-group'>
            <label>Subject ID</label>
            <input
              type='text'
              value={formData.subject_id}
              onChange={e =>
                setFormData({ ...formData, subject_id: e.target.value })
              }
              placeholder='Enter subject identifier'
              required
            />
          </div>

          <div className='form-group'>
            <label>Subject Type</label>
            <select
              value={formData.subject_type}
              onChange={e =>
                setFormData({ ...formData, subject_type: e.target.value })
              }
              required
            >
              <option value='user'>User</option>
              <option value='student'>Student</option>
              <option value='employee'>Employee</option>
              <option value='customer'>Customer</option>
            </select>
          </div>

          <div className='form-group'>
            <label>Tenant ID (optional)</label>
            <input
              type='text'
              value={formData.tenant_id}
              onChange={e =>
                setFormData({ ...formData, tenant_id: e.target.value })
              }
              placeholder='Leave empty for global request'
            />
          </div>

          <div className='form-group'>
            <label>Requester Email</label>
            <input
              type='email'
              value={formData.requester_email}
              onChange={e =>
                setFormData({ ...formData, requester_email: e.target.value })
              }
              required
            />
          </div>

          <div className='form-group'>
            <label>Requester Name</label>
            <input
              type='text'
              value={formData.requester_name}
              onChange={e =>
                setFormData({ ...formData, requester_name: e.target.value })
              }
              placeholder='Full name of person making request'
            />
          </div>

          <div className='form-group'>
            <label>Legal Basis</label>
            <input
              type='text'
              value={formData.legal_basis}
              onChange={e =>
                setFormData({ ...formData, legal_basis: e.target.value })
              }
              placeholder='Legal basis for this request'
            />
          </div>

          <div className='modal-actions'>
            <button
              type='button'
              onClick={onClose}
              className='btn btn-secondary'
            >
              Cancel
            </button>
            <button type='submit' className='btn btn-primary'>
              Create Request
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Legal Hold Modal Component
const LegalHoldModal: React.FC<{
  hold?: LegalHold | null;
  onSave: (data: Record<string, unknown>) => void;
  onClose: () => void;
}> = ({ hold, onSave, onClose }) => {
  const [formData, setFormData] = useState({
    name: hold?.name || '',
    description: hold?.description || '',
    case_number: hold?.case_number || '',
    entity_types: hold?.entity_types || ['user'],
    subject_ids: hold?.subject_ids?.join(', ') || '',
    tenant_id: hold?.tenant_id || '',
    expiry_date: hold?.expiry_date ? hold.expiry_date.substring(0, 16) : '',
    legal_authority: '',
    custodian_name: hold?.custodian_name || '',
    custodian_email: hold?.custodian_email || '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave({
      ...formData,
      entity_types: formData.entity_types,
      subject_ids: formData.subject_ids
        .split(',')
        .map(s => s.trim())
        .filter(Boolean),
      tenant_id: formData.tenant_id || undefined,
      expiry_date: formData.expiry_date || undefined,
    });
  };

  const handleEntityTypeChange = (type: string, checked: boolean) => {
    if (checked) {
      setFormData({
        ...formData,
        entity_types: [...formData.entity_types, type],
      });
    } else {
      setFormData({
        ...formData,
        entity_types: formData.entity_types.filter(t => t !== type),
      });
    }
  };

  const entityTypes = [
    'user',
    'student',
    'employee',
    'customer',
    'tenant',
    'session',
    'log',
    'document',
    'message',
    'transaction',
  ];

  return (
    <div className='modal-overlay'>
      <div className='modal large-modal'>
        <div className='modal-header'>
          <h2>{hold ? 'Edit' : 'Create'} Legal Hold</h2>
          <button onClick={onClose} className='close-btn'>
            ×
          </button>
        </div>
        <form onSubmit={handleSubmit} className='modal-body'>
          <div className='form-row'>
            <div className='form-group'>
              <label>Hold Name</label>
              <input
                type='text'
                value={formData.name}
                onChange={e =>
                  setFormData({ ...formData, name: e.target.value })
                }
                required
              />
            </div>

            <div className='form-group'>
              <label>Case Number</label>
              <input
                type='text'
                value={formData.case_number}
                onChange={e =>
                  setFormData({ ...formData, case_number: e.target.value })
                }
              />
            </div>
          </div>

          <div className='form-group'>
            <label>Description</label>
            <textarea
              value={formData.description}
              onChange={e =>
                setFormData({ ...formData, description: e.target.value })
              }
              rows={3}
            />
          </div>

          <div className='form-group'>
            <label>Entity Types</label>
            <div className='checkbox-grid'>
              {entityTypes.map(type => (
                <label key={type} className='checkbox-item'>
                  <input
                    type='checkbox'
                    checked={formData.entity_types.includes(type)}
                    onChange={e =>
                      handleEntityTypeChange(type, e.target.checked)
                    }
                  />
                  {type}
                </label>
              ))}
            </div>
          </div>

          <div className='form-group'>
            <label>Specific Subject IDs (optional)</label>
            <input
              type='text'
              value={formData.subject_ids}
              onChange={e =>
                setFormData({ ...formData, subject_ids: e.target.value })
              }
              placeholder='Comma-separated list of subject IDs'
            />
            <small>
              Leave empty to apply to all subjects of the selected entity types
            </small>
          </div>

          <div className='form-row'>
            <div className='form-group'>
              <label>Tenant ID (optional)</label>
              <input
                type='text'
                value={formData.tenant_id}
                onChange={e =>
                  setFormData({ ...formData, tenant_id: e.target.value })
                }
              />
            </div>

            <div className='form-group'>
              <label>Expiry Date (optional)</label>
              <input
                type='datetime-local'
                value={formData.expiry_date}
                onChange={e =>
                  setFormData({ ...formData, expiry_date: e.target.value })
                }
              />
            </div>
          </div>

          <div className='form-row'>
            <div className='form-group'>
              <label>Custodian Name</label>
              <input
                type='text'
                value={formData.custodian_name}
                onChange={e =>
                  setFormData({ ...formData, custodian_name: e.target.value })
                }
                required
              />
            </div>

            <div className='form-group'>
              <label>Custodian Email</label>
              <input
                type='email'
                value={formData.custodian_email}
                onChange={e =>
                  setFormData({ ...formData, custodian_email: e.target.value })
                }
                required
              />
            </div>
          </div>

          <div className='modal-actions'>
            <button
              type='button'
              onClick={onClose}
              className='btn btn-secondary'
            >
              Cancel
            </button>
            <button type='submit' className='btn btn-primary'>
              {hold ? 'Update' : 'Create'} Legal Hold
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default DataGovernance;
