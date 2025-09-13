import React, { useState, useEffect } from 'react';
import './Moderation.css';

// Types
interface QueueItem {
  id: string;
  content_id: string;
  content_type:
    | 'ocr_upload'
    | 'chat_message'
    | 'ink_image'
    | 'audio_recording'
    | 'video_submission'
    | 'text_submission';
  content_url?: string;
  content_preview?: string;
  content_metadata?: Record<string, unknown>;
  user_id: string;
  tenant_id?: string;
  session_id?: string;
  flag_reason:
    | 'inappropriate_language'
    | 'violence'
    | 'hate_speech'
    | 'harassment'
    | 'spam'
    | 'copyright_violation'
    | 'personal_info'
    | 'academic_dishonesty'
    | 'safety_concern'
    | 'other';
  flag_details?: string;
  severity_level: 'low' | 'medium' | 'high' | 'critical';
  confidence_score?: number;
  status:
    | 'pending'
    | 'in_review'
    | 'approved'
    | 'soft_blocked'
    | 'hard_blocked'
    | 'appealed'
    | 'expired';
  flagged_at: string;
  reviewed_at?: string;
  expires_at?: string;
  flagged_by_system: boolean;
  flagged_by_user_id?: string;
  latest_decision?: ModerationDecision;
}

interface ModerationDecision {
  id: string;
  queue_item_id: string;
  decision_type:
    | 'approve'
    | 'soft_block'
    | 'hard_block'
    | 'escalate'
    | 'appeal_approved'
    | 'appeal_denied';
  reason: string;
  notes?: string;
  moderator_id: string;
  moderator_name?: string;
  decided_at: string;
  expires_at?: string;
  confidence_level?: number;
  escalation_required: boolean;
  appeal_deadline?: string;
}

interface QueueStats {
  total_pending: number;
  total_in_review: number;
  total_resolved_today: number;
  total_resolved_week: number;
  by_content_type: Record<string, number>;
  by_severity: Record<string, number>;
  by_status: Record<string, number>;
  by_flag_reason: Record<string, number>;
  average_resolution_time_hours?: number;
  median_resolution_time_hours?: number;
  escalation_rate: number;
  appeal_rate: number;
  overturn_rate: number;
  top_moderators: Array<{
    moderator_id: string;
    name: string;
    decisions_count: number;
  }>;
}

interface AuditLog {
  id: string;
  queue_item_id?: string;
  decision_id?: string;
  action: string;
  description?: string;
  actor_id: string;
  actor_type: string;
  actor_name?: string;
  context?: Record<string, unknown>;
  timestamp: string;
}

const Moderation: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'queue' | 'stats' | 'audit'>(
    'queue'
  );

  // Queue state
  const [queueItems, setQueueItems] = useState<QueueItem[]>([]);
  const [queueLoading, setQueueLoading] = useState(false);
  const [queueError, setQueueError] = useState<string | null>(null);
  const [totalCount, setTotalCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(0);
  const [pageSize] = useState(20);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [contentTypeFilter, setContentTypeFilter] = useState<string>('');
  const [severityFilter, setSeverityFilter] = useState<string>('');

  // Stats state
  const [stats, setStats] = useState<QueueStats | null>(null);
  const [statsLoading, setStatsLoading] = useState(false);

  // Audit state
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [auditLoading, setAuditLoading] = useState(false);

  // Selected item for decision
  const [selectedItem, setSelectedItem] = useState<QueueItem | null>(null);
  const [showDecisionModal, setShowDecisionModal] = useState(false);
  const [decisionType, setDecisionType] = useState<
    'approve' | 'soft_block' | 'hard_block' | 'escalate'
  >('approve');
  const [decisionReason, setDecisionReason] = useState('');
  const [decisionNotes, setDecisionNotes] = useState('');
  const [decisionLoading, setDecisionLoading] = useState(false);

  // API base URL
  const API_BASE = '/api/moderation';

  useEffect(() => {
    const loadQueueItems = async () => {
      setQueueLoading(true);
      try {
        const params = new URLSearchParams({
          limit: pageSize.toString(),
          offset: (currentPage * pageSize).toString(),
        });

        if (statusFilter) params.append('status_filter', statusFilter);
        if (contentTypeFilter) params.append('content_type', contentTypeFilter);
        if (severityFilter) params.append('severity', severityFilter);

        const response = await fetch(`${API_BASE}/queue?${params}`);
        if (!response.ok) throw new Error('Failed to load queue items');

        const data = await response.json();
        setQueueItems(data.items || []);
        setTotalCount(data.total_count || 0);
        setQueueError(null);
      } catch (err) {
        setQueueError(
          err instanceof Error ? err.message : 'Failed to load queue items'
        );
        setQueueItems([]);
      } finally {
        setQueueLoading(false);
      }
    };

    const loadStats = async () => {
      setStatsLoading(true);
      try {
        const response = await fetch(`${API_BASE}/stats`);
        if (!response.ok) throw new Error('Failed to load statistics');

        const data = await response.json();
        setStats(data);
      } catch (err) {
         
        console.error('Error loading stats:', err);
      } finally {
        setStatsLoading(false);
      }
    };

    const loadAuditLogs = async () => {
      setAuditLoading(true);
      try {
        const response = await fetch(`${API_BASE}/audit?limit=50`);
        if (!response.ok) throw new Error('Failed to load audit logs');

        const data = await response.json();
        setAuditLogs(data || []);
      } catch (err) {
         
        console.error('Error loading audit logs:', err);
      } finally {
        setAuditLoading(false);
      }
    };

    const loadInitialData = async () => {
      if (activeTab === 'queue') {
        await loadQueueItems();
      } else if (activeTab === 'stats') {
        await loadStats();
      } else if (activeTab === 'audit') {
        await loadAuditLogs();
      }
    };

    loadInitialData();
  }, [
    activeTab,
    currentPage,
    statusFilter,
    contentTypeFilter,
    severityFilter,
    pageSize,
    API_BASE,
  ]);

  const refreshQueue = async () => {
    setQueueLoading(true);
    try {
      const params = new URLSearchParams({
        limit: pageSize.toString(),
        offset: (currentPage * pageSize).toString(),
      });

      if (statusFilter) params.append('status_filter', statusFilter);
      if (contentTypeFilter) params.append('content_type', contentTypeFilter);
      if (severityFilter) params.append('severity', severityFilter);

      const response = await fetch(`${API_BASE}/queue?${params}`);
      if (!response.ok) throw new Error('Failed to load queue items');

      const data = await response.json();
      setQueueItems(data.items || []);
      setTotalCount(data.total_count || 0);
      setQueueError(null);
    } catch (err) {
      setQueueError(
        err instanceof Error ? err.message : 'Failed to load queue items'
      );
      setQueueItems([]);
    } finally {
      setQueueLoading(false);
    }
  };

  const handleMakeDecision = async () => {
    if (!selectedItem || !decisionReason.trim()) return;

    setDecisionLoading(true);
    try {
      const response = await fetch(`${API_BASE}/${selectedItem.id}/decision`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          decision_type: decisionType,
          reason: decisionReason.trim(),
          notes: decisionNotes.trim() || undefined,
          moderator_id: 'current_user', // TODO: Get from auth context
        }),
      });

      if (!response.ok) throw new Error('Failed to make decision');

      setShowDecisionModal(false);
      setSelectedItem(null);
      setDecisionReason('');
      setDecisionNotes('');
      await refreshQueue();
    } catch (err) {
       
      console.error('Error making decision:', err);
    } finally {
      setDecisionLoading(false);
    }
  };

  const openDecisionModal = (item: QueueItem) => {
    setSelectedItem(item);
    setDecisionType('approve');
    setDecisionReason('');
    setDecisionNotes('');
    setShowDecisionModal(true);
  };

  const closeDecisionModal = () => {
    setShowDecisionModal(false);
    setSelectedItem(null);
    setDecisionReason('');
    setDecisionNotes('');
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'pending':
        return 'status-pending';
      case 'in_review':
        return 'status-in-review';
      case 'approved':
        return 'status-approved';
      case 'soft_blocked':
        return 'status-soft-blocked';
      case 'hard_blocked':
        return 'status-hard-blocked';
      case 'appealed':
        return 'status-appealed';
      default:
        return 'status-default';
    }
  };

  const getSeverityBadgeClass = (severity: string) => {
    switch (severity) {
      case 'low':
        return 'severity-low';
      case 'medium':
        return 'severity-medium';
      case 'high':
        return 'severity-high';
      case 'critical':
        return 'severity-critical';
      default:
        return 'severity-default';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const formatFlagReason = (reason: string) => {
    return reason.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const formatContentType = (type: string) => {
    return type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const totalPages = Math.ceil(totalCount / pageSize);

  if (queueError) {
    return (
      <div className='moderation-container'>
        <div className='error-state'>
          <h2>Error Loading Moderation Queue</h2>
          <p>{queueError}</p>
          <button onClick={() => refreshQueue()} className='retry-button'>
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className='moderation-container'>
      <div className='moderation-header'>
        <h1>Content Moderation</h1>
        <p>Review flagged content and make moderation decisions</p>
      </div>

      <div className='moderation-tabs'>
        <button
          className={`tab-button ${activeTab === 'queue' ? 'active' : ''}`}
          onClick={() => setActiveTab('queue')}
        >
          Moderation Queue ({stats?.total_pending || 0} pending)
        </button>
        <button
          className={`tab-button ${activeTab === 'stats' ? 'active' : ''}`}
          onClick={() => setActiveTab('stats')}
        >
          Statistics
        </button>
        <button
          className={`tab-button ${activeTab === 'audit' ? 'active' : ''}`}
          onClick={() => setActiveTab('audit')}
        >
          Audit Log
        </button>
      </div>

      <div className='moderation-content'>
        {activeTab === 'queue' && (
          <div className='queue-section'>
            <div className='queue-filters'>
              <div className='filter-group'>
                <label>Status:</label>
                <select
                  value={statusFilter}
                  onChange={e => setStatusFilter(e.target.value)}
                >
                  <option value=''>All Statuses</option>
                  <option value='pending'>Pending</option>
                  <option value='in_review'>In Review</option>
                  <option value='approved'>Approved</option>
                  <option value='soft_blocked'>Soft Blocked</option>
                  <option value='hard_blocked'>Hard Blocked</option>
                  <option value='appealed'>Appealed</option>
                </select>
              </div>

              <div className='filter-group'>
                <label>Content Type:</label>
                <select
                  value={contentTypeFilter}
                  onChange={e => setContentTypeFilter(e.target.value)}
                >
                  <option value=''>All Types</option>
                  <option value='ocr_upload'>OCR Upload</option>
                  <option value='chat_message'>Chat Message</option>
                  <option value='ink_image'>Ink Image</option>
                  <option value='audio_recording'>Audio Recording</option>
                  <option value='video_submission'>Video Submission</option>
                  <option value='text_submission'>Text Submission</option>
                </select>
              </div>

              <div className='filter-group'>
                <label>Severity:</label>
                <select
                  value={severityFilter}
                  onChange={e => setSeverityFilter(e.target.value)}
                >
                  <option value=''>All Severities</option>
                  <option value='low'>Low</option>
                  <option value='medium'>Medium</option>
                  <option value='high'>High</option>
                  <option value='critical'>Critical</option>
                </select>
              </div>

              <button
                onClick={refreshQueue}
                className='refresh-button'
                disabled={queueLoading}
              >
                {queueLoading ? 'Loading...' : 'Refresh'}
              </button>
            </div>

            {queueLoading ? (
              <div className='loading-state'>Loading queue items...</div>
            ) : (
              <>
                <div className='queue-items'>
                  {queueItems.length === 0 ? (
                    <div className='empty-state'>
                      No items in moderation queue
                    </div>
                  ) : (
                    queueItems.map(item => (
                      <div key={item.id} className='queue-item'>
                        <div className='item-header'>
                          <div className='item-info'>
                            <span
                              className={`status-badge ${getStatusBadgeClass(item.status)}`}
                            >
                              {item.status.replace(/_/g, ' ')}
                            </span>
                            <span
                              className={`severity-badge ${getSeverityBadgeClass(item.severity_level)}`}
                            >
                              {item.severity_level}
                            </span>
                            <span className='content-type'>
                              {formatContentType(item.content_type)}
                            </span>
                          </div>
                          <div className='item-actions'>
                            {item.status === 'pending' && (
                              <button
                                onClick={() => openDecisionModal(item)}
                                className='decision-button'
                              >
                                Make Decision
                              </button>
                            )}
                          </div>
                        </div>

                        <div className='item-details'>
                          <div className='detail-row'>
                            <strong>Flag Reason:</strong>{' '}
                            {formatFlagReason(item.flag_reason)}
                          </div>
                          {item.flag_details && (
                            <div className='detail-row'>
                              <strong>Details:</strong> {item.flag_details}
                            </div>
                          )}
                          <div className='detail-row'>
                            <strong>User ID:</strong> {item.user_id}
                            {item.tenant_id && (
                              <span> | Tenant: {item.tenant_id}</span>
                            )}
                          </div>
                          <div className='detail-row'>
                            <strong>Flagged:</strong>{' '}
                            {formatDate(item.flagged_at)}
                            {item.confidence_score && (
                              <span>
                                {' '}
                                | Confidence: {item.confidence_score}%
                              </span>
                            )}
                          </div>
                          {item.content_preview && (
                            <div className='detail-row'>
                              <strong>Preview:</strong>
                              <div className='content-preview'>
                                {item.content_preview}
                              </div>
                            </div>
                          )}
                          {item.content_url && (
                            <div className='detail-row'>
                              <strong>Content URL:</strong>
                              <a
                                href={item.content_url}
                                target='_blank'
                                rel='noopener noreferrer'
                              >
                                View Content
                              </a>
                            </div>
                          )}
                          {item.latest_decision && (
                            <div className='latest-decision'>
                              <strong>Latest Decision:</strong>{' '}
                              {item.latest_decision.decision_type}
                              by {item.latest_decision.moderator_id} -{' '}
                              {item.latest_decision.reason}
                            </div>
                          )}
                        </div>
                      </div>
                    ))
                  )}
                </div>

                {totalPages > 1 && (
                  <div className='pagination'>
                    <button
                      onClick={() =>
                        setCurrentPage(Math.max(0, currentPage - 1))
                      }
                      disabled={currentPage === 0}
                      className='pagination-button'
                    >
                      Previous
                    </button>
                    <span className='pagination-info'>
                      Page {currentPage + 1} of {totalPages} ({totalCount} total
                      items)
                    </span>
                    <button
                      onClick={() =>
                        setCurrentPage(
                          Math.min(totalPages - 1, currentPage + 1)
                        )
                      }
                      disabled={currentPage >= totalPages - 1}
                      className='pagination-button'
                    >
                      Next
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {activeTab === 'stats' && (
          <div className='stats-section'>
            {statsLoading ? (
              <div className='loading-state'>Loading statistics...</div>
            ) : stats ? (
              <div className='stats-grid'>
                <div className='stats-overview'>
                  <h3>Queue Overview</h3>
                  <div className='stats-cards'>
                    <div className='stat-card'>
                      <div className='stat-value'>{stats.total_pending}</div>
                      <div className='stat-label'>Pending Review</div>
                    </div>
                    <div className='stat-card'>
                      <div className='stat-value'>{stats.total_in_review}</div>
                      <div className='stat-label'>In Review</div>
                    </div>
                    <div className='stat-card'>
                      <div className='stat-value'>
                        {stats.total_resolved_today}
                      </div>
                      <div className='stat-label'>Resolved Today</div>
                    </div>
                    <div className='stat-card'>
                      <div className='stat-value'>
                        {stats.total_resolved_week}
                      </div>
                      <div className='stat-label'>Resolved This Week</div>
                    </div>
                  </div>
                </div>

                <div className='stats-breakdown'>
                  <div className='breakdown-section'>
                    <h4>By Content Type</h4>
                    <div className='breakdown-list'>
                      {Object.entries(stats.by_content_type).map(
                        ([type, count]) => (
                          <div key={type} className='breakdown-item'>
                            <span>{formatContentType(type)}</span>
                            <span>{count}</span>
                          </div>
                        )
                      )}
                    </div>
                  </div>

                  <div className='breakdown-section'>
                    <h4>By Severity</h4>
                    <div className='breakdown-list'>
                      {Object.entries(stats.by_severity).map(
                        ([severity, count]) => (
                          <div key={severity} className='breakdown-item'>
                            <span
                              className={`severity-badge ${getSeverityBadgeClass(severity)}`}
                            >
                              {severity}
                            </span>
                            <span>{count}</span>
                          </div>
                        )
                      )}
                    </div>
                  </div>

                  <div className='breakdown-section'>
                    <h4>By Flag Reason</h4>
                    <div className='breakdown-list'>
                      {Object.entries(stats.by_flag_reason).map(
                        ([reason, count]) => (
                          <div key={reason} className='breakdown-item'>
                            <span>{formatFlagReason(reason)}</span>
                            <span>{count}</span>
                          </div>
                        )
                      )}
                    </div>
                  </div>
                </div>

                {stats.top_moderators.length > 0 && (
                  <div className='top-moderators'>
                    <h4>Top Moderators (Last 30 Days)</h4>
                    <div className='moderator-list'>
                      {stats.top_moderators.map((moderator, index) => (
                        <div
                          key={moderator.moderator_id}
                          className='moderator-item'
                        >
                          <span className='moderator-rank'>#{index + 1}</span>
                          <span className='moderator-name'>
                            {moderator.name || moderator.moderator_id}
                          </span>
                          <span className='moderator-decisions'>
                            {moderator.decisions_count} decisions
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className='empty-state'>No statistics available</div>
            )}
          </div>
        )}

        {activeTab === 'audit' && (
          <div className='audit-section'>
            {auditLoading ? (
              <div className='loading-state'>Loading audit logs...</div>
            ) : (
              <div className='audit-logs'>
                {auditLogs.length === 0 ? (
                  <div className='empty-state'>No audit logs found</div>
                ) : (
                  <div className='audit-table'>
                    <div className='audit-header'>
                      <div>Timestamp</div>
                      <div>Action</div>
                      <div>Actor</div>
                      <div>Description</div>
                    </div>
                    {auditLogs.map(log => (
                      <div key={log.id} className='audit-row'>
                        <div className='audit-timestamp'>
                          {formatDate(log.timestamp)}
                        </div>
                        <div className='audit-action'>{log.action}</div>
                        <div className='audit-actor'>
                          {log.actor_name || log.actor_id} ({log.actor_type})
                        </div>
                        <div className='audit-description'>
                          {log.description || 'No description'}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Decision Modal */}
      {showDecisionModal && selectedItem && (
        <div className='modal-overlay' onClick={closeDecisionModal}>
          <div className='modal-content' onClick={e => e.stopPropagation()}>
            <div className='modal-header'>
              <h3>Make Moderation Decision</h3>
              <button onClick={closeDecisionModal} className='modal-close'>
                ×
              </button>
            </div>

            <div className='modal-body'>
              <div className='item-summary'>
                <p>
                  <strong>Content:</strong>{' '}
                  {formatContentType(selectedItem.content_type)}
                </p>
                <p>
                  <strong>Flag Reason:</strong>{' '}
                  {formatFlagReason(selectedItem.flag_reason)}
                </p>
                <p>
                  <strong>Severity:</strong> {selectedItem.severity_level}
                </p>
                {selectedItem.content_preview && (
                  <div>
                    <strong>Preview:</strong>
                    <div className='content-preview'>
                      {selectedItem.content_preview}
                    </div>
                  </div>
                )}
              </div>

              <div className='decision-form'>
                <div className='form-group'>
                  <label>Decision Type:</label>
                  <select
                    value={decisionType}
                    onChange={e =>
                      setDecisionType(e.target.value as typeof decisionType)
                    }
                  >
                    <option value='approve'>Approve</option>
                    <option value='soft_block'>Soft Block</option>
                    <option value='hard_block'>Hard Block</option>
                    <option value='escalate'>Escalate</option>
                  </select>
                </div>

                <div className='form-group'>
                  <label>Reason (required):</label>
                  <textarea
                    value={decisionReason}
                    onChange={e => setDecisionReason(e.target.value)}
                    placeholder='Enter the reason for this decision...'
                    rows={3}
                    required
                  />
                </div>

                <div className='form-group'>
                  <label>Additional Notes:</label>
                  <textarea
                    value={decisionNotes}
                    onChange={e => setDecisionNotes(e.target.value)}
                    placeholder='Optional additional notes...'
                    rows={2}
                  />
                </div>
              </div>
            </div>

            <div className='modal-footer'>
              <button onClick={closeDecisionModal} className='cancel-button'>
                Cancel
              </button>
              <button
                onClick={handleMakeDecision}
                disabled={!decisionReason.trim() || decisionLoading}
                className='submit-button'
              >
                {decisionLoading ? 'Processing...' : 'Make Decision'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Moderation;
