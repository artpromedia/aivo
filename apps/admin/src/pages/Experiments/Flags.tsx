import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Flag, Plus, Edit, Trash2, Target, Percent, Save } from 'lucide-react';
import { useState } from 'react';

import {
  FlagsAPI,
  type FeatureFlag,
  type FeatureFlagCreate,
  type FeatureFlagUpdate,
} from '@/api/flags';

// Simple UI components
const Badge = ({
  children,
  variant = 'default',
}: {
  children: React.ReactNode;
  variant?: 'default' | 'secondary' | 'destructive';
}) => {
  const colors = {
    default: 'bg-blue-100 text-blue-800',
    secondary: 'bg-gray-100 text-gray-800',
    destructive: 'bg-red-100 text-red-800',
  };
  return (
    <span
      className={`px-2 py-1 rounded text-xs font-medium ${colors[variant]}`}
    >
      {children}
    </span>
  );
};

const Button = ({
  children,
  onClick,
  variant = 'default',
  size = 'default',
  disabled = false,
}: {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: 'default' | 'outline';
  size?: 'default' | 'sm';
  disabled?: boolean;
}) => {
  const baseClass =
    'inline-flex items-center justify-center rounded-md font-medium transition-colors';
  const sizeClass = size === 'sm' ? 'h-8 px-3 text-sm' : 'h-10 px-4';
  const variantClass =
    variant === 'outline'
      ? 'border border-gray-300 bg-white hover:bg-gray-50'
      : 'bg-blue-600 text-white hover:bg-blue-700';

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`${baseClass} ${sizeClass} ${variantClass} ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
    >
      {children}
    </button>
  );
};

const Card = ({ children }: { children: React.ReactNode }) => (
  <div className='bg-white rounded-lg border shadow-sm'>{children}</div>
);

const CardHeader = ({ children }: { children: React.ReactNode }) => (
  <div className='px-6 py-4 border-b'>{children}</div>
);

const CardTitle = ({ children }: { children: React.ReactNode }) => (
  <h3 className='text-lg font-semibold'>{children}</h3>
);

const CardContent = ({
  children,
  className = '',
}: {
  children: React.ReactNode;
  className?: string;
}) => <div className={`px-6 py-4 ${className}`}>{children}</div>;

const Input = ({
  id,
  value,
  onChange,
  placeholder,
  type = 'text',
  min,
  max,
}: {
  id?: string;
  value: string | number;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  placeholder?: string;
  type?: string;
  min?: string;
  max?: string;
}) => (
  <input
    id={id}
    type={type}
    value={value}
    onChange={onChange}
    placeholder={placeholder}
    min={min}
    max={max}
    className='flex h-10 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500'
  />
);

const Label = ({
  htmlFor,
  children,
}: {
  htmlFor?: string;
  children: React.ReactNode;
}) => (
  <label htmlFor={htmlFor} className='text-sm font-medium leading-none'>
    {children}
  </label>
);

export function Flags() {
  const [selectedTenant, setSelectedTenant] = useState<string>('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingFlag, setEditingFlag] = useState<FeatureFlag | null>(null);
  const [newFlag, setNewFlag] = useState<FeatureFlagCreate>({
    key: '',
    name: '',
    description: '',
    enabled: false,
    rollout_percentage: 0,
    targeting_rules: {
      roles: [],
      regions: [],
      grade_bands: [],
      include_users: [],
      exclude_users: [],
    },
    tenant_id: null,
    is_experiment: false,
    experiment_id: null,
  });

  const queryClient = useQueryClient();

  // Feature flags data
  const {
    data: flags,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['feature-flags', selectedTenant],
    queryFn: () =>
      FlagsAPI.listFlags({
        tenant_id: selectedTenant || undefined,
        limit: 100,
      }),
  });

  // Create flag mutation
  const createFlagMutation = useMutation({
    mutationFn: FlagsAPI.createFlag,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feature-flags'] });
      setShowCreateModal(false);
      resetForm();
    },
  });

  // Update flag mutation
  const updateFlagMutation = useMutation({
    mutationFn: ({ key, data }: { key: string; data: FeatureFlagUpdate }) =>
      FlagsAPI.updateFlag(key, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feature-flags'] });
      setEditingFlag(null);
    },
  });

  // Delete flag mutation
  const deleteFlagMutation = useMutation({
    mutationFn: (flagKey: string) => FlagsAPI.deleteFlag(flagKey),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feature-flags'] });
    },
  });

  // Toggle flag mutation
  const toggleFlagMutation = useMutation({
    mutationFn: (flagKey: string) => FlagsAPI.toggleFlag(flagKey),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feature-flags'] });
    },
  });

  const resetForm = () => {
    setNewFlag({
      key: '',
      name: '',
      description: '',
      enabled: false,
      rollout_percentage: 0,
      targeting_rules: {
        roles: [],
        regions: [],
        grade_bands: [],
        include_users: [],
        exclude_users: [],
      },
      tenant_id: null,
      is_experiment: false,
      experiment_id: null,
    });
  };

  const handleCreateFlag = () => {
    createFlagMutation.mutate(newFlag);
  };

  const handleUpdateFlag = (flag: FeatureFlag) => {
    if (!editingFlag) return;

    const updateData: FeatureFlagUpdate = {
      name: editingFlag.name,
      description: editingFlag.description,
      enabled: editingFlag.enabled,
      rollout_percentage: editingFlag.rollout_percentage,
      targeting_rules: editingFlag.targeting_rules,
    };

    updateFlagMutation.mutate({ key: flag.key, data: updateData });
  };

  const handleDeleteFlag = (flagKey: string) => {
    if (confirm('Are you sure you want to delete this flag?')) {
      deleteFlagMutation.mutate(flagKey);
    }
  };

  const handleToggleFlag = (flagKey: string) => {
    toggleFlagMutation.mutate(flagKey);
  };

  if (isLoading) return <div className='p-6'>Loading flags...</div>;
  if (error) return <div className='p-6 text-red-600'>Error loading flags</div>;

  return (
    <div className='p-6 space-y-6'>
      <div className='flex items-center justify-between'>
        <div>
          <h1 className='text-2xl font-bold flex items-center gap-2'>
            <Flag className='w-6 h-6' />
            Feature Flags
          </h1>
          <p className='text-gray-600 mt-1'>
            Manage feature flags with rollout controls and targeting
          </p>
        </div>

        <Button onClick={() => setShowCreateModal(true)}>
          <Plus className='w-4 h-4 mr-2' />
          Create Flag
        </Button>
      </div>

      {/* Tenant Filter */}
      <Card>
        <CardContent className='pt-4'>
          <div className='flex items-center gap-4'>
            <Label htmlFor='tenant-filter'>Filter by Tenant:</Label>
            <select
              value={selectedTenant}
              onChange={e => setSelectedTenant(e.target.value)}
              className='border rounded px-3 py-2'
            >
              <option value=''>All Tenants</option>
              <option value='tenant-1'>Tenant 1</option>
              <option value='tenant-2'>Tenant 2</option>
              <option value='tenant-3'>Tenant 3</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Flags List */}
      <Card>
        <CardHeader>
          <CardTitle>Flags ({flags?.length || 0})</CardTitle>
        </CardHeader>
        <CardContent>
          <div className='space-y-4'>
            {flags?.map((flag: FeatureFlag) => (
              <div key={flag.id} className='border rounded p-4 space-y-2'>
                <div className='flex items-center justify-between'>
                  <div>
                    <h3 className='font-medium'>{flag.name}</h3>
                    <p className='text-sm text-gray-500'>{flag.key}</p>
                    {flag.description && (
                      <p className='text-xs text-gray-400 mt-1'>
                        {flag.description}
                      </p>
                    )}
                  </div>

                  <div className='flex items-center gap-2'>
                    <Badge variant={flag.enabled ? 'default' : 'secondary'}>
                      {flag.enabled ? 'Enabled' : 'Disabled'}
                    </Badge>

                    {flag.is_experiment && (
                      <Badge variant='destructive'>Experiment</Badge>
                    )}
                  </div>
                </div>

                <div className='flex items-center gap-4 text-sm text-gray-600'>
                  <div className='flex items-center gap-1'>
                    <Percent className='w-3 h-3' />
                    Rollout: {flag.rollout_percentage}%
                  </div>

                  <div className='flex items-center gap-1'>
                    <Target className='w-3 h-3' />
                    {Object.keys(flag.targeting_rules || {}).length > 0
                      ? 'Targeted'
                      : 'All Users'}
                  </div>
                </div>

                <div className='flex items-center gap-2'>
                  <Button
                    variant='outline'
                    size='sm'
                    onClick={() => setEditingFlag(flag)}
                  >
                    <Edit className='w-3 h-3 mr-1' />
                    Edit
                  </Button>

                  <Button
                    variant='outline'
                    size='sm'
                    onClick={() => handleToggleFlag(flag.key)}
                  >
                    Toggle
                  </Button>

                  <Button
                    variant='outline'
                    size='sm'
                    onClick={() => handleDeleteFlag(flag.key)}
                  >
                    <Trash2 className='w-3 h-3 mr-1' />
                    Delete
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Create Flag Modal */}
      {showCreateModal && (
        <div className='fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50'>
          <div className='bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto'>
            <h2 className='text-xl font-bold mb-4'>Create Feature Flag</h2>

            <div className='space-y-4'>
              <div className='grid grid-cols-2 gap-4'>
                <div>
                  <Label htmlFor='flag-key'>Flag Key *</Label>
                  <Input
                    id='flag-key'
                    value={newFlag.key}
                    onChange={e =>
                      setNewFlag((prev: FeatureFlagCreate) => ({
                        ...prev,
                        key: e.target.value,
                      }))
                    }
                    placeholder='feature-key'
                  />
                </div>

                <div>
                  <Label htmlFor='flag-name'>Name *</Label>
                  <Input
                    id='flag-name'
                    value={newFlag.name}
                    onChange={e =>
                      setNewFlag((prev: FeatureFlagCreate) => ({
                        ...prev,
                        name: e.target.value,
                      }))
                    }
                    placeholder='Feature Name'
                  />
                </div>
              </div>

              <div>
                <Label htmlFor='flag-description'>Description</Label>
                <textarea
                  id='flag-description'
                  value={newFlag.description}
                  onChange={e =>
                    setNewFlag((prev: FeatureFlagCreate) => ({
                      ...prev,
                      description: e.target.value,
                    }))
                  }
                  placeholder='Describe what this flag controls...'
                  className='w-full border rounded px-3 py-2'
                  rows={3}
                />
              </div>

              <div className='grid grid-cols-2 gap-4'>
                <div>
                  <Label htmlFor='rollout-percentage'>Rollout Percentage</Label>
                  <Input
                    id='rollout-percentage'
                    type='number'
                    min='0'
                    max='100'
                    value={newFlag.rollout_percentage}
                    onChange={e =>
                      setNewFlag((prev: FeatureFlagCreate) => ({
                        ...prev,
                        rollout_percentage: parseFloat(e.target.value) || 0,
                      }))
                    }
                  />
                </div>

                <div>
                  <Label htmlFor='tenant-id'>Tenant ID</Label>
                  <Input
                    id='tenant-id'
                    value={newFlag.tenant_id || ''}
                    onChange={e =>
                      setNewFlag((prev: FeatureFlagCreate) => ({
                        ...prev,
                        tenant_id: e.target.value || null,
                      }))
                    }
                    placeholder='Leave empty for global'
                  />
                </div>
              </div>

              <div className='flex items-center gap-4'>
                <label className='flex items-center gap-2'>
                  <input
                    type='checkbox'
                    checked={newFlag.enabled}
                    onChange={e =>
                      setNewFlag((prev: FeatureFlagCreate) => ({
                        ...prev,
                        enabled: e.target.checked,
                      }))
                    }
                  />
                  Enabled
                </label>

                <label className='flex items-center gap-2'>
                  <input
                    type='checkbox'
                    checked={newFlag.is_experiment}
                    onChange={e =>
                      setNewFlag((prev: FeatureFlagCreate) => ({
                        ...prev,
                        is_experiment: e.target.checked,
                      }))
                    }
                  />
                  Is Experiment
                </label>
              </div>

              <div className='flex justify-end gap-2'>
                <Button
                  variant='outline'
                  onClick={() => setShowCreateModal(false)}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleCreateFlag}
                  disabled={
                    !newFlag.key ||
                    !newFlag.name ||
                    createFlagMutation.isPending
                  }
                >
                  <Save className='w-4 h-4 mr-2' />
                  Create Flag
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Edit Flag Modal */}
      {editingFlag && (
        <div className='fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50'>
          <div className='bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto'>
            <h2 className='text-xl font-bold mb-4'>
              Edit Feature Flag: {editingFlag.key}
            </h2>

            <div className='space-y-4'>
              <div>
                <Label htmlFor='edit-name'>Name</Label>
                <Input
                  id='edit-name'
                  value={editingFlag.name}
                  onChange={e =>
                    setEditingFlag((prev: FeatureFlag | null) =>
                      prev ? { ...prev, name: e.target.value } : null
                    )
                  }
                />
              </div>

              <div>
                <Label htmlFor='edit-description'>Description</Label>
                <textarea
                  id='edit-description'
                  value={editingFlag.description || ''}
                  onChange={e =>
                    setEditingFlag((prev: FeatureFlag | null) =>
                      prev ? { ...prev, description: e.target.value } : null
                    )
                  }
                  className='w-full border rounded px-3 py-2'
                  rows={3}
                />
              </div>

              <div>
                <Label htmlFor='edit-rollout'>Rollout Percentage</Label>
                <Input
                  id='edit-rollout'
                  type='number'
                  min='0'
                  max='100'
                  value={editingFlag.rollout_percentage}
                  onChange={e =>
                    setEditingFlag((prev: FeatureFlag | null) =>
                      prev
                        ? {
                            ...prev,
                            rollout_percentage: parseFloat(e.target.value) || 0,
                          }
                        : null
                    )
                  }
                />
              </div>

              <div className='flex items-center space-x-2'>
                <label className='flex items-center gap-2'>
                  <input
                    type='checkbox'
                    checked={editingFlag.enabled}
                    onChange={e =>
                      setEditingFlag((prev: FeatureFlag | null) =>
                        prev ? { ...prev, enabled: e.target.checked } : null
                      )
                    }
                  />
                  Enabled
                </label>
              </div>

              <div className='flex justify-end gap-2'>
                <Button variant='outline' onClick={() => setEditingFlag(null)}>
                  Cancel
                </Button>
                <Button
                  onClick={() => handleUpdateFlag(editingFlag)}
                  disabled={updateFlagMutation.isPending}
                >
                  <Save className='w-4 h-4 mr-2' />
                  Save Changes
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
