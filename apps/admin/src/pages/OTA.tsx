import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Plus,
  Upload,
  Play,
  Pause,
  RotateCcw,
  Eye,
  CheckCircle,
  XCircle,
  Clock,
  RefreshCw,
} from 'lucide-react';
import { useState } from 'react';

import {
  OTAAPI,
  type FirmwareUpdate,
  type CreateFirmwareUpdateRequest,
} from '@/api/ota';
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

export function OTA() {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [selectedUpdate, setSelectedUpdate] = useState<FirmwareUpdate | null>(
    null
  );
  const [showProgress, setShowProgress] = useState(false);

  const queryClient = useQueryClient();

  const { data: updatesData, isLoading } = useQuery({
    queryKey: ['firmware-updates'],
    queryFn: () => OTAAPI.getFirmwareUpdates({ limit: 50 }),
  });

  const createUpdateMutation = useMutation({
    mutationFn: OTAAPI.createFirmwareUpdate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['firmware-updates'] });
      setShowCreateForm(false);
    },
  });

  const deployUpdateMutation = useMutation({
    mutationFn: OTAAPI.deployUpdate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['firmware-updates'] });
    },
  });

  const rollbackUpdateMutation = useMutation({
    mutationFn: ({ updateId, ring }: { updateId: string; ring?: string }) =>
      OTAAPI.rollbackUpdate(updateId, ring),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['firmware-updates'] });
    },
  });

  const pauseUpdateMutation = useMutation({
    mutationFn: OTAAPI.pauseUpdate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['firmware-updates'] });
    },
  });

  const resumeUpdateMutation = useMutation({
    mutationFn: OTAAPI.resumeUpdate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['firmware-updates'] });
    },
  });

  const handleCreateUpdate = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);

    const update: CreateFirmwareUpdateRequest = {
      version: formData.get('version') as string,
      description: formData.get('description') as string,
      release_notes: formData.get('release_notes') as string,
      file_url: formData.get('file_url') as string,
      file_size: parseInt(formData.get('file_size') as string),
      checksum: formData.get('checksum') as string,
      target_device_types: (formData.get('target_device_types') as string)
        .split(',')
        .map(s => s.trim()),
      deployment_config: {
        canary_percentage: parseInt(
          formData.get('canary_percentage') as string
        ),
        early_percentage: parseInt(formData.get('early_percentage') as string),
        broad_percentage: parseInt(formData.get('broad_percentage') as string),
        production_percentage: parseInt(
          formData.get('production_percentage') as string
        ),
      },
    };

    createUpdateMutation.mutate(update);
  };

  const handleDeploy = (
    updateId: string,
    ring: 'canary' | 'early' | 'broad' | 'production'
  ) => {
    if (window.confirm(`Deploy this update to ${ring} ring?`)) {
      deployUpdateMutation.mutate({ update_id: updateId, ring });
    }
  };

  const handleRollback = (updateId: string, ring?: string) => {
    const confirmMessage = ring
      ? `Rollback this update from ${ring} ring?`
      : 'Rollback this update from all rings?';

    if (window.confirm(confirmMessage)) {
      rollbackUpdateMutation.mutate({ updateId, ring });
    }
  };

  const getRingStatus = (
    update: FirmwareUpdate,
    ring: keyof FirmwareUpdate['rollout_status']
  ) => {
    const status = update.rollout_status[ring];
    const total = status.deployed;
    const successful = status.successful;
    const failed = status.failed;

    if (total === 0) return { color: 'gray', text: 'Not deployed' };
    if (failed > 0) return { color: 'red', text: `${failed} failed` };
    if (successful === total) return { color: 'green', text: 'Complete' };
    return { color: 'blue', text: `${successful}/${total}` };
  };

  const formatFileSize = (bytes: number) => {
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 Bytes';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round((bytes / Math.pow(1024, i)) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className='space-y-6'>
      {/* Header */}
      <div className='flex items-center justify-between'>
        <div>
          <h1 className='text-3xl font-bold tracking-tight'>
            Over-the-Air Updates
          </h1>
          <p className='text-muted-foreground'>
            Manage firmware updates and deployment rollouts
          </p>
        </div>
        <div className='flex items-center gap-4'>
          <Button
            variant='outline'
            onClick={() =>
              queryClient.invalidateQueries({ queryKey: ['firmware-updates'] })
            }
          >
            <RefreshCw className='h-4 w-4 mr-2' />
            Refresh
          </Button>
          <Button onClick={() => setShowCreateForm(true)}>
            <Plus className='h-4 w-4 mr-2' />
            Create Update
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className='grid grid-cols-1 md:grid-cols-4 gap-4'>
        <Card className='p-4'>
          <div className='flex items-center gap-3'>
            <Upload className='h-8 w-8 text-blue-500' />
            <div>
              <p className='text-sm text-muted-foreground'>Active Updates</p>
              <p className='text-2xl font-bold'>
                {updatesData?.updates.filter(u => u.is_active).length || 0}
              </p>
            </div>
          </div>
        </Card>
        <Card className='p-4'>
          <div className='flex items-center gap-3'>
            <CheckCircle className='h-8 w-8 text-green-500' />
            <div>
              <p className='text-sm text-muted-foreground'>Successful</p>
              <p className='text-2xl font-bold'>
                {updatesData?.updates.reduce(
                  (sum, u) =>
                    sum +
                    Object.values(u.rollout_status).reduce(
                      (ringSum, ring) => ringSum + ring.successful,
                      0
                    ),
                  0
                ) || 0}
              </p>
            </div>
          </div>
        </Card>
        <Card className='p-4'>
          <div className='flex items-center gap-3'>
            <XCircle className='h-8 w-8 text-red-500' />
            <div>
              <p className='text-sm text-muted-foreground'>Failed</p>
              <p className='text-2xl font-bold'>
                {updatesData?.updates.reduce(
                  (sum, u) =>
                    sum +
                    Object.values(u.rollout_status).reduce(
                      (ringSum, ring) => ringSum + ring.failed,
                      0
                    ),
                  0
                ) || 0}
              </p>
            </div>
          </div>
        </Card>
        <Card className='p-4'>
          <div className='flex items-center gap-3'>
            <Clock className='h-8 w-8 text-yellow-500' />
            <div>
              <p className='text-sm text-muted-foreground'>In Progress</p>
              <p className='text-2xl font-bold'>
                {updatesData?.updates.reduce(
                  (sum, u) =>
                    sum +
                    Object.values(u.rollout_status).reduce(
                      (ringSum, ring) =>
                        ringSum +
                        (ring.deployed - ring.successful - ring.failed),
                      0
                    ),
                  0
                ) || 0}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Updates Table */}
      <Card>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Update</TableHead>
              <TableHead>Target Devices</TableHead>
              <TableHead>File Size</TableHead>
              <TableHead>Deployment Status</TableHead>
              <TableHead>Created</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={6} className='text-center py-8'>
                  <RefreshCw className='h-6 w-6 animate-spin mx-auto mb-2' />
                  Loading updates...
                </TableCell>
              </TableRow>
            ) : updatesData?.updates.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className='text-center py-8'>
                  <Upload className='h-12 w-12 text-muted-foreground mx-auto mb-4' />
                  <p className='text-lg font-medium'>
                    No firmware updates found
                  </p>
                  <p className='text-muted-foreground'>
                    Create your first firmware update to get started
                  </p>
                </TableCell>
              </TableRow>
            ) : (
              updatesData?.updates.map(update => (
                <TableRow key={update.id}>
                  <TableCell>
                    <div>
                      <p className='font-medium'>v{update.version}</p>
                      <p className='text-sm text-muted-foreground'>
                        {update.description}
                      </p>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className='flex flex-wrap gap-1'>
                      {update.target_device_types.map(type => (
                        <Badge key={type} variant='outline'>
                          {type}
                        </Badge>
                      ))}
                    </div>
                  </TableCell>
                  <TableCell>{formatFileSize(update.file_size)}</TableCell>
                  <TableCell>
                    <div className='space-y-1'>
                      {Object.entries(update.rollout_status).map(([ring]) => {
                        const ringStatus = getRingStatus(
                          update,
                          ring as keyof FirmwareUpdate['rollout_status']
                        );
                        return (
                          <div
                            key={ring}
                            className='flex items-center gap-2 text-xs'
                          >
                            <span className='w-16 capitalize'>{ring}:</span>
                            <span className={`text-${ringStatus.color}-600`}>
                              {ringStatus.text}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </TableCell>
                  <TableCell>
                    {new Date(update.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    <div className='flex items-center gap-1'>
                      <Button
                        size='sm'
                        variant='outline'
                        onClick={() => {
                          setSelectedUpdate(update);
                          setShowProgress(true);
                        }}
                      >
                        <Eye className='h-3 w-3' />
                      </Button>

                      {/* Deploy buttons for each ring */}
                      <Select
                        onChange={e => {
                          const value = e.target.value as
                            | 'canary'
                            | 'early'
                            | 'broad'
                            | 'production'
                            | '';
                          if (value) {
                            handleDeploy(update.id, value);
                            e.target.value = '';
                          }
                        }}
                      >
                        <option value=''>Deploy</option>
                        <option value='canary'>Canary</option>
                        <option value='early'>Early</option>
                        <option value='broad'>Broad</option>
                        <option value='production'>Production</option>
                      </Select>

                      <Button
                        size='sm'
                        variant='outline'
                        onClick={() => pauseUpdateMutation.mutate(update.id)}
                        disabled={pauseUpdateMutation.isPending}
                      >
                        <Pause className='h-3 w-3' />
                      </Button>

                      <Button
                        size='sm'
                        variant='outline'
                        onClick={() => resumeUpdateMutation.mutate(update.id)}
                        disabled={resumeUpdateMutation.isPending}
                      >
                        <Play className='h-3 w-3' />
                      </Button>

                      <Button
                        size='sm'
                        variant='destructive'
                        onClick={() => handleRollback(update.id)}
                        disabled={rollbackUpdateMutation.isPending}
                      >
                        <RotateCcw className='h-3 w-3' />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </Card>

      {/* Create Update Modal */}
      {showCreateForm && (
        <div className='fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50'>
          <Card className='w-full max-w-2xl p-6 max-h-[90vh] overflow-y-auto'>
            <h2 className='text-lg font-semibold mb-4'>
              Create Firmware Update
            </h2>
            <form onSubmit={handleCreateUpdate} className='space-y-4'>
              <div className='grid grid-cols-2 gap-4'>
                <div>
                  <label className='block text-sm font-medium mb-2'>
                    Version
                  </label>
                  <Input name='version' required placeholder='e.g., 2.1.0' />
                </div>
                <div>
                  <label className='block text-sm font-medium mb-2'>
                    File Size (bytes)
                  </label>
                  <Input
                    name='file_size'
                    type='number'
                    required
                    placeholder='File size in bytes'
                  />
                </div>
              </div>

              <div>
                <label className='block text-sm font-medium mb-2'>
                  Description
                </label>
                <Input
                  name='description'
                  required
                  placeholder='Brief description of the update'
                />
              </div>

              <div>
                <label className='block text-sm font-medium mb-2'>
                  Release Notes
                </label>
                <textarea
                  name='release_notes'
                  required
                  rows={4}
                  className='w-full p-3 border rounded-md'
                  placeholder='Detailed release notes'
                />
              </div>

              <div className='grid grid-cols-2 gap-4'>
                <div>
                  <label className='block text-sm font-medium mb-2'>
                    File URL
                  </label>
                  <Input
                    name='file_url'
                    type='url'
                    required
                    placeholder='https://cdn.example.com/firmware.bin'
                  />
                </div>
                <div>
                  <label className='block text-sm font-medium mb-2'>
                    Checksum
                  </label>
                  <Input
                    name='checksum'
                    required
                    placeholder='SHA256 checksum'
                  />
                </div>
              </div>

              <div>
                <label className='block text-sm font-medium mb-2'>
                  Target Device Types
                </label>
                <Input
                  name='target_device_types'
                  required
                  placeholder='tablet, chromebook, phone (comma separated)'
                />
              </div>

              <div className='grid grid-cols-4 gap-4'>
                <div>
                  <label className='block text-sm font-medium mb-2'>
                    Canary %
                  </label>
                  <Input
                    name='canary_percentage'
                    type='number'
                    min='0'
                    max='100'
                    defaultValue='5'
                    required
                  />
                </div>
                <div>
                  <label className='block text-sm font-medium mb-2'>
                    Early %
                  </label>
                  <Input
                    name='early_percentage'
                    type='number'
                    min='0'
                    max='100'
                    defaultValue='25'
                    required
                  />
                </div>
                <div>
                  <label className='block text-sm font-medium mb-2'>
                    Broad %
                  </label>
                  <Input
                    name='broad_percentage'
                    type='number'
                    min='0'
                    max='100'
                    defaultValue='75'
                    required
                  />
                </div>
                <div>
                  <label className='block text-sm font-medium mb-2'>
                    Production %
                  </label>
                  <Input
                    name='production_percentage'
                    type='number'
                    min='0'
                    max='100'
                    defaultValue='100'
                    required
                  />
                </div>
              </div>

              <div className='flex justify-end gap-2'>
                <Button
                  type='button'
                  variant='outline'
                  onClick={() => setShowCreateForm(false)}
                >
                  Cancel
                </Button>
                <Button type='submit' disabled={createUpdateMutation.isPending}>
                  {createUpdateMutation.isPending
                    ? 'Creating...'
                    : 'Create Update'}
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}

      {/* Progress Modal */}
      {showProgress && selectedUpdate && (
        <div className='fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50'>
          <Card className='w-full max-w-4xl p-6'>
            <div className='flex items-center justify-between mb-4'>
              <h2 className='text-lg font-semibold'>
                Update Progress: v{selectedUpdate.version}
              </h2>
              <Button variant='outline' onClick={() => setShowProgress(false)}>
                Close
              </Button>
            </div>

            <div className='grid grid-cols-2 md:grid-cols-4 gap-4'>
              {Object.entries(selectedUpdate.rollout_status).map(
                ([ring, status]) => (
                  <Card key={ring} className='p-4'>
                    <div className='text-center'>
                      <h3 className='font-medium capitalize mb-2'>{ring}</h3>
                      <div className='space-y-2'>
                        <div className='flex items-center justify-between text-sm'>
                          <span>Deployed:</span>
                          <span className='font-medium'>{status.deployed}</span>
                        </div>
                        <div className='flex items-center justify-between text-sm'>
                          <span>Successful:</span>
                          <span className='font-medium text-green-600'>
                            {status.successful}
                          </span>
                        </div>
                        <div className='flex items-center justify-between text-sm'>
                          <span>Failed:</span>
                          <span className='font-medium text-red-600'>
                            {status.failed}
                          </span>
                        </div>
                        <div className='w-full bg-gray-200 rounded-full h-2'>
                          <div
                            className='bg-blue-600 h-2 rounded-full'
                            style={{
                              width:
                                status.deployed > 0
                                  ? `${(status.successful / status.deployed) * 100}%`
                                  : '0%',
                            }}
                          />
                        </div>
                      </div>
                    </div>
                  </Card>
                )
              )}
            </div>

            <div className='mt-6'>
              <h3 className='font-medium mb-3'>Release Notes</h3>
              <div className='bg-gray-50 p-4 rounded-md'>
                <pre className='whitespace-pre-wrap text-sm'>
                  {selectedUpdate.release_notes}
                </pre>
              </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
