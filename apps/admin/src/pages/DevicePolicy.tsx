import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Plus,
  Search,
  Settings,
  Users,
  Shield,
  Wifi,
  Globe,
  Clock,
  Edit,
  Trash2,
  Copy,
  RefreshCw,
} from 'lucide-react';
import { useState } from 'react';

import { DeviceAPI } from '@/api/device';
import { PolicyAPI, type Policy, type CreatePolicyRequest } from '@/api/policy';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

export function DevicePolicy() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedType, setSelectedType] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingPolicy, setEditingPolicy] = useState<Policy | null>(null);
  const [showAssignments, setShowAssignments] = useState(false);
  const [selectedPolicyId, setSelectedPolicyId] = useState<string | null>(null);

  const queryClient = useQueryClient();

  const { data: policiesData, isLoading } = useQuery({
    queryKey: ['policies', selectedType],
    queryFn: () =>
      PolicyAPI.getPolicies({
        page: 1,
        limit: 100,
        policy_type: selectedType || undefined,
      }),
  });

  const { data: devicesData } = useQuery({
    queryKey: ['devices-for-policy'],
    queryFn: () => DeviceAPI.getDevices({ limit: 100 }),
  });

  const createPolicyMutation = useMutation({
    mutationFn: PolicyAPI.createPolicy,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['policies'] });
      setShowCreateForm(false);
    },
  });

  const updatePolicyMutation = useMutation({
    mutationFn: ({
      id,
      updates,
    }: {
      id: string;
      updates: Partial<CreatePolicyRequest>;
    }) => PolicyAPI.updatePolicy(id, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['policies'] });
      setEditingPolicy(null);
    },
  });

  const deletePolicyMutation = useMutation({
    mutationFn: PolicyAPI.deletePolicy,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['policies'] });
    },
  });

  const bulkAssignMutation = useMutation({
    mutationFn: ({
      policyId,
      deviceIds,
    }: {
      policyId: string;
      deviceIds: string[];
    }) => PolicyAPI.bulkAssignPolicy(policyId, deviceIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['device-policies'] });
      setShowAssignments(false);
    },
  });

  const handleCreatePolicy = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);

    let config;
    try {
      config = JSON.parse(formData.get('config') as string);
    } catch {
      alert('Invalid JSON configuration');
      return;
    }

    const policy: CreatePolicyRequest = {
      name: formData.get('name') as string,
      description: formData.get('description') as string,
      policy_type: formData.get(
        'policy_type'
      ) as CreatePolicyRequest['policy_type'],
      config,
    };

    createPolicyMutation.mutate(policy);
  };

  const handleUpdatePolicy = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!editingPolicy) return;

    const formData = new FormData(event.currentTarget);

    let config;
    try {
      config = JSON.parse(formData.get('config') as string);
    } catch {
      alert('Invalid JSON configuration');
      return;
    }

    const updates: Partial<CreatePolicyRequest> = {
      name: formData.get('name') as string,
      description: formData.get('description') as string,
      policy_type: formData.get(
        'policy_type'
      ) as CreatePolicyRequest['policy_type'],
      config,
    };

    updatePolicyMutation.mutate({ id: editingPolicy.id, updates });
  };

  const handleDeletePolicy = (policyId: string) => {
    if (
      window.confirm(
        'Are you sure you want to delete this policy? This action cannot be undone.'
      )
    ) {
      deletePolicyMutation.mutate(policyId);
    }
  };

  const handleBulkAssign = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedPolicyId) return;

    const formData = new FormData(event.currentTarget);
    const selectedDeviceIds = Array.from(
      formData.getAll('device_ids')
    ) as string[];

    if (selectedDeviceIds.length === 0) {
      alert('Please select at least one device');
      return;
    }

    bulkAssignMutation.mutate({
      policyId: selectedPolicyId,
      deviceIds: selectedDeviceIds,
    });
  };

  const getPolicyIcon = (type: Policy['policy_type']) => {
    switch (type) {
      case 'kiosk':
        return <Shield className='h-4 w-4' />;
      case 'network':
        return <Wifi className='h-4 w-4' />;
      case 'dns':
        return <Globe className='h-4 w-4' />;
      case 'study_window':
        return <Clock className='h-4 w-4' />;
      default:
        return <Settings className='h-4 w-4' />;
    }
  };

  const getPolicyTypeColor = (type: Policy['policy_type']) => {
    const colors = {
      kiosk: 'bg-blue-100 text-blue-800',
      network: 'bg-green-100 text-green-800',
      dns: 'bg-purple-100 text-purple-800',
      study_window: 'bg-orange-100 text-orange-800',
    };
    return colors[type] || 'bg-gray-100 text-gray-800';
  };

  const getDefaultConfig = (type: Policy['policy_type']) => {
    const configs = {
      kiosk: {
        allowed_apps: ['com.example.app'],
        exit_code: '1234',
        lockdown_level: 'strict',
      },
      network: {
        wifi_enabled: true,
        mobile_data_enabled: false,
        allowed_networks: ['SchoolWiFi'],
      },
      dns: {
        primary_dns: '1.1.1.1',
        secondary_dns: '1.0.0.1',
        blocked_domains: ['facebook.com', 'youtube.com'],
        allowed_domains: ['educational-site.com'],
      },
      study_window: {
        windows: [
          {
            start_time: '09:00',
            end_time: '15:00',
            days: ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
          },
        ],
      },
    };
    return JSON.stringify(configs[type], null, 2);
  };

  return (
    <div className='space-y-6'>
      {/* Header */}
      <div className='flex items-center justify-between'>
        <div>
          <h1 className='text-3xl font-bold tracking-tight'>Device Policies</h1>
          <p className='text-muted-foreground'>
            Create and manage device policies for different use cases
          </p>
        </div>
        <div className='flex items-center gap-4'>
          <Button
            variant='outline'
            onClick={() =>
              queryClient.invalidateQueries({ queryKey: ['policies'] })
            }
          >
            <RefreshCw className='h-4 w-4 mr-2' />
            Refresh
          </Button>
          <Button onClick={() => setShowCreateForm(true)}>
            <Plus className='h-4 w-4 mr-2' />
            Create Policy
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className='grid grid-cols-1 md:grid-cols-4 gap-4'>
        <Card className='p-4'>
          <div className='flex items-center gap-3'>
            <Shield className='h-8 w-8 text-blue-500' />
            <div>
              <p className='text-sm text-muted-foreground'>Kiosk Policies</p>
              <p className='text-2xl font-bold'>
                {policiesData?.policies.filter(p => p.policy_type === 'kiosk')
                  .length || 0}
              </p>
            </div>
          </div>
        </Card>
        <Card className='p-4'>
          <div className='flex items-center gap-3'>
            <Wifi className='h-8 w-8 text-green-500' />
            <div>
              <p className='text-sm text-muted-foreground'>Network Policies</p>
              <p className='text-2xl font-bold'>
                {policiesData?.policies.filter(p => p.policy_type === 'network')
                  .length || 0}
              </p>
            </div>
          </div>
        </Card>
        <Card className='p-4'>
          <div className='flex items-center gap-3'>
            <Globe className='h-8 w-8 text-purple-500' />
            <div>
              <p className='text-sm text-muted-foreground'>DNS Policies</p>
              <p className='text-2xl font-bold'>
                {policiesData?.policies.filter(p => p.policy_type === 'dns')
                  .length || 0}
              </p>
            </div>
          </div>
        </Card>
        <Card className='p-4'>
          <div className='flex items-center gap-3'>
            <Clock className='h-8 w-8 text-orange-500' />
            <div>
              <p className='text-sm text-muted-foreground'>Study Window</p>
              <p className='text-2xl font-bold'>
                {policiesData?.policies.filter(
                  p => p.policy_type === 'study_window'
                ).length || 0}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Filters */}
      <Card className='p-4'>
        <div className='flex items-center gap-4'>
          <div className='flex-1'>
            <div className='relative'>
              <Search className='h-4 w-4 absolute left-3 top-3 text-muted-foreground' />
              <Input
                placeholder='Search policies...'
                className='pl-10'
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
              />
            </div>
          </div>
          <Select
            value={selectedType}
            onChange={e => setSelectedType(e.target.value)}
          >
            <option value=''>All Types</option>
            <option value='kiosk'>Kiosk</option>
            <option value='network'>Network</option>
            <option value='dns'>DNS</option>
            <option value='study_window'>Study Window</option>
          </Select>
        </div>
      </Card>

      {/* Policies Table */}
      <Card>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Policy</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Created</TableHead>
              <TableHead>Updated</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={6} className='text-center py-8'>
                  <RefreshCw className='h-6 w-6 animate-spin mx-auto mb-2' />
                  Loading policies...
                </TableCell>
              </TableRow>
            ) : policiesData?.policies.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className='text-center py-8'>
                  <Settings className='h-12 w-12 text-muted-foreground mx-auto mb-4' />
                  <p className='text-lg font-medium'>No policies found</p>
                  <p className='text-muted-foreground'>
                    Create your first device policy to get started
                  </p>
                </TableCell>
              </TableRow>
            ) : (
              policiesData?.policies
                .filter(
                  policy =>
                    searchTerm === '' ||
                    policy.name
                      .toLowerCase()
                      .includes(searchTerm.toLowerCase()) ||
                    policy.description
                      .toLowerCase()
                      .includes(searchTerm.toLowerCase())
                )
                .map(policy => (
                  <TableRow key={policy.id}>
                    <TableCell>
                      <div className='flex items-center gap-3'>
                        {getPolicyIcon(policy.policy_type)}
                        <div>
                          <p className='font-medium'>{policy.name}</p>
                          <p className='text-sm text-muted-foreground'>
                            {policy.description}
                          </p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${getPolicyTypeColor(policy.policy_type)}`}
                      >
                        {policy.policy_type}
                      </span>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={policy.is_active ? 'default' : 'secondary'}
                      >
                        {policy.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {new Date(policy.created_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell>
                      {new Date(policy.updated_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell>
                      <div className='flex items-center gap-2'>
                        <Button
                          size='sm'
                          variant='outline'
                          onClick={() => {
                            setSelectedPolicyId(policy.id);
                            setShowAssignments(true);
                          }}
                        >
                          <Users className='h-4 w-4 mr-1' />
                          Assign
                        </Button>
                        <Button
                          size='sm'
                          variant='outline'
                          onClick={() => setEditingPolicy(policy)}
                        >
                          <Edit className='h-4 w-4' />
                        </Button>
                        <Button
                          size='sm'
                          variant='outline'
                          onClick={() => {
                            navigator.clipboard.writeText(
                              JSON.stringify(policy.config, null, 2)
                            );
                          }}
                        >
                          <Copy className='h-4 w-4' />
                        </Button>
                        <Button
                          size='sm'
                          variant='destructive'
                          onClick={() => handleDeletePolicy(policy.id)}
                          disabled={deletePolicyMutation.isPending}
                        >
                          <Trash2 className='h-4 w-4' />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
            )}
          </TableBody>
        </Table>
      </Card>

      {/* Create Policy Modal */}
      {showCreateForm && (
        <div className='fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50'>
          <Card className='w-full max-w-2xl p-6 max-h-[90vh] overflow-y-auto'>
            <h2 className='text-lg font-semibold mb-4'>Create New Policy</h2>
            <form onSubmit={handleCreatePolicy} className='space-y-4'>
              <div>
                <label className='block text-sm font-medium mb-2'>
                  Policy Name
                </label>
                <Input name='name' required placeholder='Enter policy name' />
              </div>
              <div>
                <label className='block text-sm font-medium mb-2'>
                  Description
                </label>
                <Input
                  name='description'
                  required
                  placeholder='Enter policy description'
                />
              </div>
              <div>
                <label className='block text-sm font-medium mb-2'>
                  Policy Type
                </label>
                <Select
                  name='policy_type'
                  required
                  onChange={e => {
                    const textarea = document.querySelector(
                      'textarea[name="config"]'
                    ) as HTMLTextAreaElement;
                    if (textarea) {
                      textarea.value = getDefaultConfig(
                        e.target.value as Policy['policy_type']
                      );
                    }
                  }}
                >
                  <option value=''>Select type</option>
                  <option value='kiosk'>Kiosk Mode</option>
                  <option value='network'>Network Policy</option>
                  <option value='dns'>DNS Policy</option>
                  <option value='study_window'>Study Window</option>
                </Select>
              </div>
              <div>
                <label className='block text-sm font-medium mb-2'>
                  Configuration (JSON)
                </label>
                <textarea
                  name='config'
                  required
                  rows={12}
                  className='w-full p-3 border rounded-md font-mono text-sm'
                  placeholder='Enter JSON configuration'
                />
              </div>
              <div className='flex justify-end gap-2'>
                <Button
                  type='button'
                  variant='outline'
                  onClick={() => setShowCreateForm(false)}
                >
                  Cancel
                </Button>
                <Button type='submit' disabled={createPolicyMutation.isPending}>
                  {createPolicyMutation.isPending
                    ? 'Creating...'
                    : 'Create Policy'}
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}

      {/* Edit Policy Modal */}
      {editingPolicy && (
        <div className='fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50'>
          <Card className='w-full max-w-2xl p-6 max-h-[90vh] overflow-y-auto'>
            <h2 className='text-lg font-semibold mb-4'>Edit Policy</h2>
            <form onSubmit={handleUpdatePolicy} className='space-y-4'>
              <div>
                <label className='block text-sm font-medium mb-2'>
                  Policy Name
                </label>
                <Input name='name' required defaultValue={editingPolicy.name} />
              </div>
              <div>
                <label className='block text-sm font-medium mb-2'>
                  Description
                </label>
                <Input
                  name='description'
                  required
                  defaultValue={editingPolicy.description}
                />
              </div>
              <div>
                <label className='block text-sm font-medium mb-2'>
                  Policy Type
                </label>
                <Select
                  name='policy_type'
                  required
                  defaultValue={editingPolicy.policy_type}
                >
                  <option value='kiosk'>Kiosk Mode</option>
                  <option value='network'>Network Policy</option>
                  <option value='dns'>DNS Policy</option>
                  <option value='study_window'>Study Window</option>
                </Select>
              </div>
              <div>
                <label className='block text-sm font-medium mb-2'>
                  Configuration (JSON)
                </label>
                <textarea
                  name='config'
                  required
                  rows={12}
                  className='w-full p-3 border rounded-md font-mono text-sm'
                  defaultValue={JSON.stringify(editingPolicy.config, null, 2)}
                />
              </div>
              <div className='flex justify-end gap-2'>
                <Button
                  type='button'
                  variant='outline'
                  onClick={() => setEditingPolicy(null)}
                >
                  Cancel
                </Button>
                <Button type='submit' disabled={updatePolicyMutation.isPending}>
                  {updatePolicyMutation.isPending
                    ? 'Updating...'
                    : 'Update Policy'}
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}

      {/* Bulk Assignment Modal */}
      {showAssignments && selectedPolicyId && (
        <div className='fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50'>
          <Card className='w-full max-w-lg p-6'>
            <h2 className='text-lg font-semibold mb-4'>
              Assign Policy to Devices
            </h2>
            <form onSubmit={handleBulkAssign} className='space-y-4'>
              <div>
                <label className='block text-sm font-medium mb-2'>
                  Select Devices
                </label>
                <div className='max-h-64 overflow-y-auto border rounded-md p-3 space-y-2'>
                  {devicesData?.devices
                    .filter(device => device.enrollment_status === 'approved')
                    .map(device => (
                      <label
                        key={device.id}
                        className='flex items-center gap-2'
                      >
                        <input
                          type='checkbox'
                          name='device_ids'
                          value={device.id}
                        />
                        <span className='text-sm'>
                          {device.serial_number} ({device.device_type})
                        </span>
                      </label>
                    ))}
                </div>
              </div>
              <div className='flex justify-end gap-2'>
                <Button
                  type='button'
                  variant='outline'
                  onClick={() => setShowAssignments(false)}
                >
                  Cancel
                </Button>
                <Button type='submit' disabled={bulkAssignMutation.isPending}>
                  {bulkAssignMutation.isPending
                    ? 'Assigning...'
                    : 'Assign Policy'}
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  );
}
