import React, { useState, useEffect, useCallback } from 'react';

interface Secret {
  id: string;
  name: string;
  secret_type: string;
  description: string;
  namespace_id: string;
  access_level: string;
  is_active: boolean;
  expires_at: string | null;
  auto_rotate: boolean;
  created_at: string;
  updated_at: string;
  created_by: string;
  last_accessed_at: string | null;
  access_count: number;
  version: number;
}

interface Namespace {
  id: string;
  name: string;
  description: string;
  is_active: boolean;
  created_at: string;
}

interface SecretStats {
  total_secrets: number;
  active_secrets: number;
  expired_secrets: number;
  namespaces_count: number;
  total_accesses: number;
}

const SECRETS_API_BASE = 'http://localhost:8400';

const Secrets: React.FC = () => {
  const [secrets, setSecrets] = useState<Secret[]>([]);
  const [namespaces, setNamespaces] = useState<Namespace[]>([]);
  const [stats, setStats] = useState<SecretStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Dialog states
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [selectedSecret, setSelectedSecret] = useState<Secret | null>(null);
  const [selectedNamespace, setSelectedNamespace] = useState<string>('');

  // Form data
  const [formData, setFormData] = useState({
    name: '',
    secret_type: 'password',
    value: '',
    description: '',
    namespace_id: '',
    access_level: 'restricted',
    expires_at: '',
    auto_rotate: false,
  });

  // View states
  const [expandedSecrets, setExpandedSecrets] = useState<Set<string>>(
    new Set()
  );
  const [showSecretValue, setShowSecretValue] = useState(false);
  const [secretValue, setSecretValue] = useState<string>('');

  // Load data
  const loadSecrets = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (selectedNamespace) {
        params.append('namespace_id', selectedNamespace);
      }

      const response = await fetch(`${SECRETS_API_BASE}/secrets?${params}`);
      if (!response.ok) throw new Error('Failed to load secrets');
      const data = await response.json();
      setSecrets(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load secrets');
    }
  }, [selectedNamespace]);

  const loadNamespaces = useCallback(async () => {
    try {
      const response = await fetch(`${SECRETS_API_BASE}/namespaces`);
      if (!response.ok) throw new Error('Failed to load namespaces');
      const data = await response.json();
      setNamespaces(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to load namespaces'
      );
    }
  }, []);

  const loadStats = useCallback(async () => {
    try {
      const response = await fetch(`${SECRETS_API_BASE}/secrets/stats`);
      if (!response.ok) throw new Error('Failed to load stats');
      const data = await response.json();
      setStats(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load stats');
    }
  }, []);

  useEffect(() => {
    const initData = async () => {
      setLoading(true);
      await Promise.all([loadSecrets(), loadNamespaces(), loadStats()]);
      setLoading(false);
    };
    initData();
  }, [selectedNamespace, loadSecrets, loadNamespaces, loadStats]);

  // Actions
  const handleCreateSecret = async () => {
    try {
      const payload = {
        ...formData,
        expires_at: formData.expires_at || null,
      };

      const response = await fetch(`${SECRETS_API_BASE}/secrets`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) throw new Error('Failed to create secret');

      setCreateDialogOpen(false);
      setFormData({
        name: '',
        secret_type: 'password',
        value: '',
        description: '',
        namespace_id: '',
        access_level: 'restricted',
        expires_at: '',
        auto_rotate: false,
      });
      await loadSecrets();
      await loadStats();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create secret');
    }
  };

  const handleViewSecret = async (secret: Secret) => {
    try {
      const response = await fetch(
        `${SECRETS_API_BASE}/secrets/${secret.id}/value`
      );
      if (!response.ok) throw new Error('Failed to retrieve secret value');
      const data = await response.json();
      setSecretValue(data.value);
      setSelectedSecret(secret);
      setViewDialogOpen(true);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to retrieve secret'
      );
    }
  };

  const handleDeleteSecret = async (secretId: string) => {
    if (!confirm('Are you sure you want to delete this secret?')) return;

    try {
      const response = await fetch(`${SECRETS_API_BASE}/secrets/${secretId}`, {
        method: 'DELETE',
      });
      if (!response.ok) throw new Error('Failed to delete secret');
      await loadSecrets();
      await loadStats();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete secret');
    }
  };

  const toggleSecretExpansion = (secretId: string) => {
    const newExpanded = new Set(expandedSecrets);
    if (newExpanded.has(secretId)) {
      newExpanded.delete(secretId);
    } else {
      newExpanded.add(secretId);
    }
    setExpandedSecrets(newExpanded);
  };

  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      password: 'bg-blue-100 text-blue-800',
      api_key: 'bg-green-100 text-green-800',
      token: 'bg-purple-100 text-purple-800',
      certificate: 'bg-yellow-100 text-yellow-800',
      database_password: 'bg-red-100 text-red-800',
      ssh_key: 'bg-gray-100 text-gray-800',
      other: 'bg-gray-100 text-gray-800',
    };
    return colors[type] || colors.other;
  };

  const getAccessLevelColor = (level: string) => {
    const colors: Record<string, string> = {
      public: 'bg-green-100 text-green-800',
      internal: 'bg-yellow-100 text-yellow-800',
      restricted: 'bg-orange-100 text-orange-800',
      confidential: 'bg-red-100 text-red-800',
    };
    return colors[level] || colors.restricted;
  };

  if (loading) {
    return (
      <div className='flex items-center justify-center min-h-96'>
        <div className='animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600'></div>
      </div>
    );
  }

  return (
    <div className='p-6 max-w-7xl mx-auto'>
      <div className='mb-6'>
        <h1 className='text-3xl font-bold text-gray-900 mb-2'>
          Secrets & Keys Vault
        </h1>
        <p className='text-gray-600'>
          Manage encrypted secrets and API keys securely
        </p>
      </div>

      {error && (
        <div className='mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded'>
          {error}
        </div>
      )}

      {/* Stats Cards */}
      {stats && (
        <div className='grid grid-cols-1 md:grid-cols-5 gap-4 mb-6'>
          <div className='bg-white p-4 rounded-lg shadow border'>
            <div className='flex items-center'>
              <div className='text-2xl font-bold text-blue-600'>
                {stats.total_secrets}
              </div>
              <div className='ml-2 text-blue-600'>🔐</div>
            </div>
            <div className='text-sm text-gray-600'>Total Secrets</div>
          </div>
          <div className='bg-white p-4 rounded-lg shadow border'>
            <div className='flex items-center'>
              <div className='text-2xl font-bold text-green-600'>
                {stats.active_secrets}
              </div>
              <div className='ml-2 text-green-600'>✅</div>
            </div>
            <div className='text-sm text-gray-600'>Active Secrets</div>
          </div>
          <div className='bg-white p-4 rounded-lg shadow border'>
            <div className='flex items-center'>
              <div className='text-2xl font-bold text-red-600'>
                {stats.expired_secrets}
              </div>
              <div className='ml-2 text-red-600'>⚠️</div>
            </div>
            <div className='text-sm text-gray-600'>Expired Secrets</div>
          </div>
          <div className='bg-white p-4 rounded-lg shadow border'>
            <div className='flex items-center'>
              <div className='text-2xl font-bold text-purple-600'>
                {stats.namespaces_count}
              </div>
              <div className='ml-2 text-purple-600'>📁</div>
            </div>
            <div className='text-sm text-gray-600'>Namespaces</div>
          </div>
          <div className='bg-white p-4 rounded-lg shadow border'>
            <div className='flex items-center'>
              <div className='text-2xl font-bold text-gray-600'>
                {stats.total_accesses}
              </div>
              <div className='ml-2 text-gray-600'>👁️</div>
            </div>
            <div className='text-sm text-gray-600'>Total Accesses</div>
          </div>
        </div>
      )}

      {/* Controls */}
      <div className='mb-6 flex flex-wrap gap-4 items-center'>
        <button
          onClick={() => setCreateDialogOpen(true)}
          className='bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center gap-2'
        >
          <span>➕</span> Add Secret
        </button>

        <button
          onClick={() => {
            loadSecrets();
            loadStats();
          }}
          className='bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg flex items-center gap-2'
        >
          <span>🔄</span> Refresh
        </button>

        <div className='flex items-center gap-2'>
          <label className='text-sm font-medium text-gray-700'>
            Namespace:
          </label>
          <select
            value={selectedNamespace}
            onChange={e => setSelectedNamespace(e.target.value)}
            className='border border-gray-300 rounded-md px-3 py-2 text-sm'
          >
            <option value=''>All Namespaces</option>
            {namespaces.map(ns => (
              <option key={ns.id} value={ns.id}>
                {ns.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Secrets Table */}
      <div className='bg-white rounded-lg shadow overflow-hidden'>
        <table className='min-w-full divide-y divide-gray-200'>
          <thead className='bg-gray-50'>
            <tr>
              <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>
                Name
              </th>
              <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>
                Type
              </th>
              <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>
                Access Level
              </th>
              <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>
                Status
              </th>
              <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>
                Last Accessed
              </th>
              <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>
                Actions
              </th>
            </tr>
          </thead>
          <tbody className='bg-white divide-y divide-gray-200'>
            {secrets.map(secret => (
              <React.Fragment key={secret.id}>
                <tr className='hover:bg-gray-50'>
                  <td className='px-6 py-4 whitespace-nowrap'>
                    <div className='flex items-center'>
                      <button
                        onClick={() => toggleSecretExpansion(secret.id)}
                        className='mr-2 text-gray-400 hover:text-gray-600'
                      >
                        {expandedSecrets.has(secret.id) ? '⯆' : '⯈'}
                      </button>
                      <div>
                        <div className='text-sm font-medium text-gray-900'>
                          {secret.name}
                        </div>
                        <div className='text-sm text-gray-500'>
                          v{secret.version}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className='px-6 py-4 whitespace-nowrap'>
                    <span
                      className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getTypeColor(secret.secret_type)}`}
                    >
                      {secret.secret_type}
                    </span>
                  </td>
                  <td className='px-6 py-4 whitespace-nowrap'>
                    <span
                      className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getAccessLevelColor(secret.access_level)}`}
                    >
                      {secret.access_level}
                    </span>
                  </td>
                  <td className='px-6 py-4 whitespace-nowrap'>
                    <div className='flex items-center'>
                      <span
                        className={`w-2 h-2 rounded-full mr-2 ${secret.is_active ? 'bg-green-400' : 'bg-red-400'}`}
                      ></span>
                      <span className='text-sm text-gray-900'>
                        {secret.is_active ? 'Active' : 'Inactive'}
                      </span>
                      {secret.expires_at &&
                        new Date(secret.expires_at) < new Date() && (
                          <span className='ml-2 text-red-600'>⚠️</span>
                        )}
                    </div>
                  </td>
                  <td className='px-6 py-4 whitespace-nowrap text-sm text-gray-500'>
                    {secret.last_accessed_at
                      ? new Date(secret.last_accessed_at).toLocaleDateString()
                      : 'Never'}
                  </td>
                  <td className='px-6 py-4 whitespace-nowrap text-sm font-medium'>
                    <button
                      onClick={() => handleViewSecret(secret)}
                      className='text-blue-600 hover:text-blue-900 mr-3'
                      title='View Secret'
                    >
                      👁️
                    </button>
                    <button
                      onClick={() => handleDeleteSecret(secret.id)}
                      className='text-red-600 hover:text-red-900'
                      title='Delete Secret'
                    >
                      🗑️
                    </button>
                  </td>
                </tr>

                {expandedSecrets.has(secret.id) && (
                  <tr>
                    <td colSpan={6} className='px-6 py-4 bg-gray-50'>
                      <div className='grid grid-cols-1 md:grid-cols-2 gap-4 text-sm'>
                        <div>
                          <strong>Description:</strong>{' '}
                          {secret.description || 'No description'}
                        </div>
                        <div>
                          <strong>Created:</strong>{' '}
                          {new Date(secret.created_at).toLocaleString()}
                        </div>
                        <div>
                          <strong>Created By:</strong> {secret.created_by}
                        </div>
                        <div>
                          <strong>Access Count:</strong> {secret.access_count}
                        </div>
                        {secret.expires_at && (
                          <div>
                            <strong>Expires:</strong>{' '}
                            {new Date(secret.expires_at).toLocaleString()}
                          </div>
                        )}
                        <div>
                          <strong>Auto Rotate:</strong>{' '}
                          {secret.auto_rotate ? 'Yes' : 'No'}
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>

        {secrets.length === 0 && (
          <div className='text-center py-12'>
            <div className='text-gray-500 text-lg'>No secrets found</div>
            <p className='text-gray-400 mt-2'>
              Create your first secret to get started
            </p>
          </div>
        )}
      </div>

      {/* Create Secret Dialog */}
      {createDialogOpen && (
        <div className='fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50'>
          <div className='relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white'>
            <div className='mt-3'>
              <h3 className='text-lg font-medium text-gray-900 mb-4'>
                Create New Secret
              </h3>

              <div className='space-y-4'>
                <div>
                  <label className='block text-sm font-medium text-gray-700 mb-1'>
                    Name
                  </label>
                  <input
                    type='text'
                    value={formData.name}
                    onChange={e =>
                      setFormData({ ...formData, name: e.target.value })
                    }
                    className='w-full border border-gray-300 rounded-md px-3 py-2'
                    placeholder='Secret name'
                  />
                </div>

                <div>
                  <label className='block text-sm font-medium text-gray-700 mb-1'>
                    Type
                  </label>
                  <select
                    value={formData.secret_type}
                    onChange={e =>
                      setFormData({ ...formData, secret_type: e.target.value })
                    }
                    className='w-full border border-gray-300 rounded-md px-3 py-2'
                  >
                    <option value='password'>Password</option>
                    <option value='api_key'>API Key</option>
                    <option value='token'>Token</option>
                    <option value='certificate'>Certificate</option>
                    <option value='database_password'>Database Password</option>
                    <option value='ssh_key'>SSH Key</option>
                    <option value='other'>Other</option>
                  </select>
                </div>

                <div>
                  <label className='block text-sm font-medium text-gray-700 mb-1'>
                    Secret Value
                  </label>
                  <textarea
                    value={formData.value}
                    onChange={e =>
                      setFormData({ ...formData, value: e.target.value })
                    }
                    className='w-full border border-gray-300 rounded-md px-3 py-2'
                    rows={3}
                    placeholder='Enter secret value'
                  />
                </div>

                <div>
                  <label className='block text-sm font-medium text-gray-700 mb-1'>
                    Description
                  </label>
                  <input
                    type='text'
                    value={formData.description}
                    onChange={e =>
                      setFormData({ ...formData, description: e.target.value })
                    }
                    className='w-full border border-gray-300 rounded-md px-3 py-2'
                    placeholder='Optional description'
                  />
                </div>

                <div>
                  <label className='block text-sm font-medium text-gray-700 mb-1'>
                    Namespace
                  </label>
                  <select
                    value={formData.namespace_id}
                    onChange={e =>
                      setFormData({ ...formData, namespace_id: e.target.value })
                    }
                    className='w-full border border-gray-300 rounded-md px-3 py-2'
                  >
                    <option value=''>Select namespace</option>
                    {namespaces.map(ns => (
                      <option key={ns.id} value={ns.id}>
                        {ns.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className='block text-sm font-medium text-gray-700 mb-1'>
                    Access Level
                  </label>
                  <select
                    value={formData.access_level}
                    onChange={e =>
                      setFormData({ ...formData, access_level: e.target.value })
                    }
                    className='w-full border border-gray-300 rounded-md px-3 py-2'
                  >
                    <option value='public'>Public</option>
                    <option value='internal'>Internal</option>
                    <option value='restricted'>Restricted</option>
                    <option value='confidential'>Confidential</option>
                  </select>
                </div>

                <div>
                  <label className='block text-sm font-medium text-gray-700 mb-1'>
                    Expires At (Optional)
                  </label>
                  <input
                    type='datetime-local'
                    value={formData.expires_at}
                    onChange={e =>
                      setFormData({ ...formData, expires_at: e.target.value })
                    }
                    className='w-full border border-gray-300 rounded-md px-3 py-2'
                  />
                </div>

                <div className='flex items-center'>
                  <input
                    type='checkbox'
                    checked={formData.auto_rotate}
                    onChange={e =>
                      setFormData({
                        ...formData,
                        auto_rotate: e.target.checked,
                      })
                    }
                    className='h-4 w-4 text-blue-600 border-gray-300 rounded'
                  />
                  <label className='ml-2 text-sm text-gray-700'>
                    Auto-rotate secret
                  </label>
                </div>
              </div>

              <div className='flex justify-end space-x-3 mt-6'>
                <button
                  onClick={() => setCreateDialogOpen(false)}
                  className='px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400'
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateSecret}
                  className='px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700'
                >
                  Create Secret
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* View Secret Dialog */}
      {viewDialogOpen && selectedSecret && (
        <div className='fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50'>
          <div className='relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white'>
            <div className='mt-3'>
              <h3 className='text-lg font-medium text-gray-900 mb-4'>
                View Secret: {selectedSecret.name}
              </h3>

              <div className='space-y-4'>
                <div className='bg-yellow-50 border border-yellow-200 rounded-md p-3'>
                  <div className='flex items-center text-yellow-800'>
                    <span className='mr-2'>⚠️</span>
                    <span className='text-sm font-medium'>
                      Security Warning
                    </span>
                  </div>
                  <p className='text-yellow-700 text-sm mt-1'>
                    This action will be logged for security auditing purposes.
                  </p>
                </div>

                <div>
                  <label className='block text-sm font-medium text-gray-700 mb-1'>
                    Secret Value
                  </label>
                  <div className='relative'>
                    <textarea
                      value={showSecretValue ? secretValue : '••••••••••••••••'}
                      readOnly
                      className='w-full border border-gray-300 rounded-md px-3 py-2 bg-gray-50'
                      rows={4}
                    />
                    <button
                      onClick={() => setShowSecretValue(!showSecretValue)}
                      className='absolute right-2 top-2 text-gray-500 hover:text-gray-700'
                    >
                      {showSecretValue ? '🙈' : '👁️'}
                    </button>
                  </div>
                </div>

                <div className='grid grid-cols-2 gap-4 text-sm'>
                  <div>
                    <strong>Type:</strong> {selectedSecret.secret_type}
                  </div>
                  <div>
                    <strong>Access Level:</strong> {selectedSecret.access_level}
                  </div>
                  <div>
                    <strong>Version:</strong> {selectedSecret.version}
                  </div>
                  <div>
                    <strong>Status:</strong>{' '}
                    {selectedSecret.is_active ? 'Active' : 'Inactive'}
                  </div>
                </div>

                {selectedSecret.description && (
                  <div>
                    <strong>Description:</strong>
                    <p className='text-gray-600 mt-1'>
                      {selectedSecret.description}
                    </p>
                  </div>
                )}
              </div>

              <div className='flex justify-end space-x-3 mt-6'>
                <button
                  onClick={() => {
                    setViewDialogOpen(false);
                    setShowSecretValue(false);
                    setSecretValue('');
                    setSelectedSecret(null);
                  }}
                  className='px-4 py-2 bg-gray-300 text-gray-700 rounded-md hover:bg-gray-400'
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Secrets;
