import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Plus,
  Search,
  Filter,
  Download,
  RefreshCw,
  Smartphone,
  CheckCircle,
  XCircle,
  Clock,
  AlertCircle,
} from 'lucide-react';
import { useState } from 'react';

import { DeviceAPI, type Device, type DeviceEnrollment } from '@/api/device';
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

interface DeviceFilters {
  status: string;
  device_type: string;
  search: string;
}

export function Devices() {
  const [currentPage, setCurrentPage] = useState(1);
  const [filters, setFilters] = useState<DeviceFilters>({
    status: '',
    device_type: '',
    search: '',
  });
  const [showEnrollForm, setShowEnrollForm] = useState(false);
  const [selectedDevices, setSelectedDevices] = useState<string[]>([]);

  const queryClient = useQueryClient();

  const {
    data: devicesData,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['devices', currentPage, filters],
    queryFn: () =>
      DeviceAPI.getDevices({
        page: currentPage,
        limit: 20,
        status: filters.status || undefined,
        device_type: filters.device_type || undefined,
      }),
  });

  const approveEnrollmentMutation = useMutation({
    mutationFn: DeviceAPI.approveEnrollment,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['devices'] });
    },
  });

  const rejectEnrollmentMutation = useMutation({
    mutationFn: ({ deviceId, reason }: { deviceId: string; reason?: string }) =>
      DeviceAPI.rejectEnrollment(deviceId, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['devices'] });
    },
  });

  const deactivateDeviceMutation = useMutation({
    mutationFn: DeviceAPI.deactivateDevice,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['devices'] });
    },
  });

  const enrollDeviceMutation = useMutation({
    mutationFn: DeviceAPI.enrollDevice,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['devices'] });
      setShowEnrollForm(false);
    },
  });

  const handleApproveEnrollment = (deviceId: string) => {
    approveEnrollmentMutation.mutate(deviceId);
  };

  const handleRejectEnrollment = (deviceId: string) => {
    const reason = window.prompt('Reason for rejection (optional):');
    rejectEnrollmentMutation.mutate({ deviceId, reason: reason || undefined });
  };

  const handleDeactivateDevice = (deviceId: string) => {
    if (window.confirm('Are you sure you want to deactivate this device?')) {
      deactivateDeviceMutation.mutate(deviceId);
    }
  };

  const handleEnrollDevice = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const enrollment: DeviceEnrollment = {
      serial_number: formData.get('serial_number') as string,
      device_type: formData.get('device_type') as string,
      location: (formData.get('location') as string) || undefined,
    };
    enrollDeviceMutation.mutate(enrollment);
  };

  const getStatusIcon = (status: Device['status']) => {
    switch (status) {
      case 'online':
        return <CheckCircle className='h-4 w-4 text-green-500' />;
      case 'offline':
        return <XCircle className='h-4 w-4 text-red-500' />;
      case 'pending':
        return <Clock className='h-4 w-4 text-yellow-500' />;
      case 'error':
        return <AlertCircle className='h-4 w-4 text-red-500' />;
      default:
        return <Smartphone className='h-4 w-4 text-gray-500' />;
    }
  };

  const getStatusBadge = (status: Device['status']) => {
    const variants = {
      online: 'default',
      offline: 'secondary',
      pending: 'outline',
      error: 'destructive',
    } as const;

    return <Badge variant={variants[status] || 'outline'}>{status}</Badge>;
  };

  const getEnrollmentStatusBadge = (status: Device['enrollment_status']) => {
    const variants = {
      pending: 'outline',
      approved: 'default',
      rejected: 'destructive',
    } as const;

    return <Badge variant={variants[status] || 'outline'}>{status}</Badge>;
  };

  if (error) {
    return (
      <div className='flex items-center justify-center h-64'>
        <div className='text-center'>
          <AlertCircle className='h-12 w-12 text-red-500 mx-auto mb-4' />
          <h3 className='text-lg font-semibold text-gray-900 mb-2'>
            Failed to load devices
          </h3>
          <p className='text-gray-600'>
            {error instanceof Error ? error.message : 'Unknown error occurred'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className='space-y-6'>
      {/* Header */}
      <div className='flex items-center justify-between'>
        <div>
          <h1 className='text-3xl font-bold tracking-tight'>
            Device Management
          </h1>
          <p className='text-muted-foreground'>
            Manage device enrollment, monitoring, and policies
          </p>
        </div>
        <div className='flex items-center gap-4'>
          <Button
            variant='outline'
            onClick={() =>
              queryClient.invalidateQueries({ queryKey: ['devices'] })
            }
          >
            <RefreshCw className='h-4 w-4 mr-2' />
            Refresh
          </Button>
          <Button onClick={() => setShowEnrollForm(true)}>
            <Plus className='h-4 w-4 mr-2' />
            Enroll Device
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className='grid grid-cols-1 md:grid-cols-4 gap-4'>
        <Card className='p-4'>
          <div className='flex items-center gap-3'>
            <CheckCircle className='h-8 w-8 text-green-500' />
            <div>
              <p className='text-sm text-muted-foreground'>Online</p>
              <p className='text-2xl font-bold'>
                {devicesData?.devices.filter(d => d.status === 'online')
                  .length || 0}
              </p>
            </div>
          </div>
        </Card>
        <Card className='p-4'>
          <div className='flex items-center gap-3'>
            <XCircle className='h-8 w-8 text-red-500' />
            <div>
              <p className='text-sm text-muted-foreground'>Offline</p>
              <p className='text-2xl font-bold'>
                {devicesData?.devices.filter(d => d.status === 'offline')
                  .length || 0}
              </p>
            </div>
          </div>
        </Card>
        <Card className='p-4'>
          <div className='flex items-center gap-3'>
            <Clock className='h-8 w-8 text-yellow-500' />
            <div>
              <p className='text-sm text-muted-foreground'>Pending</p>
              <p className='text-2xl font-bold'>
                {devicesData?.devices.filter(
                  d => d.enrollment_status === 'pending'
                ).length || 0}
              </p>
            </div>
          </div>
        </Card>
        <Card className='p-4'>
          <div className='flex items-center gap-3'>
            <Smartphone className='h-8 w-8 text-blue-500' />
            <div>
              <p className='text-sm text-muted-foreground'>Total</p>
              <p className='text-2xl font-bold'>{devicesData?.total || 0}</p>
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
                placeholder='Search devices...'
                className='pl-10'
                value={filters.search}
                onChange={e =>
                  setFilters(prev => ({ ...prev, search: e.target.value }))
                }
              />
            </div>
          </div>
          <Select
            value={filters.status}
            onChange={e =>
              setFilters(prev => ({ ...prev, status: e.target.value }))
            }
          >
            <option value=''>All Status</option>
            <option value='online'>Online</option>
            <option value='offline'>Offline</option>
            <option value='pending'>Pending</option>
            <option value='error'>Error</option>
          </Select>
          <Select
            value={filters.device_type}
            onChange={e =>
              setFilters(prev => ({ ...prev, device_type: e.target.value }))
            }
          >
            <option value=''>All Types</option>
            <option value='tablet'>Tablet</option>
            <option value='chromebook'>Chromebook</option>
            <option value='phone'>Phone</option>
          </Select>
          <Button variant='outline'>
            <Filter className='h-4 w-4 mr-2' />
            Filters
          </Button>
          <Button variant='outline'>
            <Download className='h-4 w-4 mr-2' />
            Export
          </Button>
        </div>
      </Card>

      {/* Device Table */}
      <Card>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className='w-12'>
                <input
                  type='checkbox'
                  onChange={e => {
                    if (e.target.checked) {
                      setSelectedDevices(
                        devicesData?.devices.map(d => d.id) || []
                      );
                    } else {
                      setSelectedDevices([]);
                    }
                  }}
                />
              </TableHead>
              <TableHead>Device</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Enrollment</TableHead>
              <TableHead>Last Seen</TableHead>
              <TableHead>Firmware</TableHead>
              <TableHead>Location</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={9} className='text-center py-8'>
                  <RefreshCw className='h-6 w-6 animate-spin mx-auto mb-2' />
                  Loading devices...
                </TableCell>
              </TableRow>
            ) : devicesData?.devices.length === 0 ? (
              <TableRow>
                <TableCell colSpan={9} className='text-center py-8'>
                  <Smartphone className='h-12 w-12 text-muted-foreground mx-auto mb-4' />
                  <p className='text-lg font-medium'>No devices found</p>
                  <p className='text-muted-foreground'>
                    Start by enrolling your first device
                  </p>
                </TableCell>
              </TableRow>
            ) : (
              devicesData?.devices.map(device => (
                <TableRow key={device.id}>
                  <TableCell>
                    <input
                      type='checkbox'
                      checked={selectedDevices.includes(device.id)}
                      onChange={e => {
                        if (e.target.checked) {
                          setSelectedDevices(prev => [...prev, device.id]);
                        } else {
                          setSelectedDevices(prev =>
                            prev.filter(id => id !== device.id)
                          );
                        }
                      }}
                    />
                  </TableCell>
                  <TableCell>
                    <div className='flex items-center gap-3'>
                      {getStatusIcon(device.status)}
                      <div>
                        <p className='font-medium'>{device.serial_number}</p>
                        <p className='text-sm text-muted-foreground'>
                          {device.id}
                        </p>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant='outline'>{device.device_type}</Badge>
                  </TableCell>
                  <TableCell>{getStatusBadge(device.status)}</TableCell>
                  <TableCell>
                    {getEnrollmentStatusBadge(device.enrollment_status)}
                  </TableCell>
                  <TableCell>
                    {new Date(device.last_seen).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    <code className='text-sm'>{device.firmware_version}</code>
                  </TableCell>
                  <TableCell>{device.location || '-'}</TableCell>
                  <TableCell>
                    <div className='flex items-center gap-2'>
                      {device.enrollment_status === 'pending' && (
                        <>
                          <Button
                            size='sm'
                            onClick={() => handleApproveEnrollment(device.id)}
                            disabled={approveEnrollmentMutation.isPending}
                          >
                            Approve
                          </Button>
                          <Button
                            size='sm'
                            variant='outline'
                            onClick={() => handleRejectEnrollment(device.id)}
                            disabled={rejectEnrollmentMutation.isPending}
                          >
                            Reject
                          </Button>
                        </>
                      )}
                      {device.enrollment_status === 'approved' && (
                        <Button
                          size='sm'
                          variant='destructive'
                          onClick={() => handleDeactivateDevice(device.id)}
                          disabled={deactivateDeviceMutation.isPending}
                        >
                          Deactivate
                        </Button>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </Card>

      {/* Pagination */}
      {devicesData && devicesData.totalPages > 1 && (
        <div className='flex items-center justify-between'>
          <p className='text-sm text-muted-foreground'>
            Showing {(currentPage - 1) * 20 + 1} to{' '}
            {Math.min(currentPage * 20, devicesData.total)} of{' '}
            {devicesData.total} devices
          </p>
          <div className='flex items-center gap-2'>
            <Button
              variant='outline'
              disabled={currentPage === 1}
              onClick={() => setCurrentPage(prev => prev - 1)}
            >
              Previous
            </Button>
            <span className='text-sm'>
              Page {currentPage} of {devicesData.totalPages}
            </span>
            <Button
              variant='outline'
              disabled={currentPage === devicesData.totalPages}
              onClick={() => setCurrentPage(prev => prev + 1)}
            >
              Next
            </Button>
          </div>
        </div>
      )}

      {/* Enrollment Form Modal */}
      {showEnrollForm && (
        <div className='fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50'>
          <Card className='w-full max-w-md p-6'>
            <h2 className='text-lg font-semibold mb-4'>Enroll New Device</h2>
            <form onSubmit={handleEnrollDevice} className='space-y-4'>
              <div>
                <label className='block text-sm font-medium mb-2'>
                  Serial Number
                </label>
                <Input
                  name='serial_number'
                  required
                  placeholder='Enter serial number'
                />
              </div>
              <div>
                <label className='block text-sm font-medium mb-2'>
                  Device Type
                </label>
                <Select name='device_type' required>
                  <option value=''>Select type</option>
                  <option value='tablet'>Tablet</option>
                  <option value='chromebook'>Chromebook</option>
                  <option value='phone'>Phone</option>
                </Select>
              </div>
              <div>
                <label className='block text-sm font-medium mb-2'>
                  Location (Optional)
                </label>
                <Input name='location' placeholder='e.g. Classroom 101' />
              </div>
              <div className='flex justify-end gap-2'>
                <Button
                  type='button'
                  variant='outline'
                  onClick={() => setShowEnrollForm(false)}
                >
                  Cancel
                </Button>
                <Button type='submit' disabled={enrollDeviceMutation.isPending}>
                  {enrollDeviceMutation.isPending
                    ? 'Enrolling...'
                    : 'Enroll Device'}
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  );
}
