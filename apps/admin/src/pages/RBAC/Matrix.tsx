import {
  Shield,
  Users,
  Settings,
  CheckCircle,
  X,
  Filter,
  Download,
  RefreshCw,
  AlertCircle,
} from 'lucide-react';
import { useState } from 'react';

import {
  usePermissionMatrix,
  useUpdateRolePermissions,
} from '../../hooks/useRBAC';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';

// Note: Interfaces are included in the component for now due to import resolution issues

interface PermissionMatrixProps {
  tenantId?: string;
}

interface Role {
  id: string;
  display_name: string;
  is_system: boolean;
  permissions: string[];
}

interface Permission {
  id: string;
  display_name: string;
  action?: string;
  scope?: string;
}

interface PermissionGroup {
  resource: string;
  permissions: Permission[];
}

interface MatrixData {
  roles: Role[];
  permission_groups: PermissionGroup[];
  matrix: Record<string, string[]>;
  summary: {
    total_roles: number;
    total_permissions: number;
    system_roles: number;
    custom_roles: number;
  };
}

export default function Matrix({ tenantId }: PermissionMatrixProps) {
  const [selectedResource, setSelectedResource] = useState<string>('all');
  const [showSystemRoles, setShowSystemRoles] = useState(true);
  const [pendingChanges, setPendingChanges] = useState<
    Record<string, Set<string>>
  >({});

  const {
    data: matrixData,
    isLoading,
    isError,
    refetch,
  } = usePermissionMatrix(tenantId) as {
    data: MatrixData | undefined;
    isLoading: boolean;
    isError: boolean;
    refetch: () => void;
  };

  const updateRolePermissions = useUpdateRolePermissions();

  const handlePermissionToggle = (roleId: string, permissionId: string) => {
    if (!matrixData) return;

    const role = matrixData.roles.find((r: Role) => r.id === roleId);
    if (!role || role.is_system) return;

    setPendingChanges(prev => {
      const roleChanges = prev[roleId] || new Set(role.permissions);
      const newChanges = new Set(roleChanges);

      if (newChanges.has(permissionId)) {
        newChanges.delete(permissionId);
      } else {
        newChanges.add(permissionId);
      }

      return { ...prev, [roleId]: newChanges };
    });
  };

  const handleSaveChanges = async (roleId: string) => {
    const changes = pendingChanges[roleId];
    if (!changes) return;

    try {
      await updateRolePermissions.mutateAsync({
        roleId,
        permissionIds: Array.from(changes),
        tenantId,
      });

      setPendingChanges(prev => {
        // Remove the roleId from pending changes
        const newChanges = { ...prev };
        delete newChanges[roleId];
        return newChanges;
      });
    } catch {
      // Silent error handling for demo
    }
  };

  const handleCancelChanges = (roleId: string) => {
    setPendingChanges(prev => {
      // Remove the roleId from pending changes
      const newChanges = { ...prev };
      delete newChanges[roleId];
      return newChanges;
    });
  };

  const getFilteredRoles = (): Role[] => {
    if (!matrixData) return [];

    return matrixData.roles.filter((role: Role) => {
      if (!showSystemRoles && role.is_system) return false;
      return true;
    });
  };

  const getFilteredPermissions = (): PermissionGroup[] => {
    if (!matrixData) return [];

    if (selectedResource === 'all') {
      return matrixData.permission_groups;
    }

    return matrixData.permission_groups.filter(
      (group: PermissionGroup) => group.resource === selectedResource
    );
  };

  const hasPermission = (roleId: string, permissionId: string) => {
    if (pendingChanges[roleId]) {
      return pendingChanges[roleId].has(permissionId);
    }
    return matrixData?.matrix[roleId]?.includes(permissionId) || false;
  };

  const exportMatrix = () => {
    if (!matrixData) return;

    const csvContent = generateCSVContent();
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `rbac_matrix_${tenantId || 'global'}_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const generateCSVContent = (): string => {
    const roles = getFilteredRoles();
    const permissionGroups = getFilteredPermissions();

    let csv = 'Resource,Permission,';
    csv += roles.map((role: Role) => role.display_name).join(',') + '\n';

    permissionGroups.forEach((group: PermissionGroup) => {
      group.permissions.forEach((permission: Permission) => {
        csv += `${group.resource},${permission.display_name},`;
        csv +=
          roles
            .map((role: Role) =>
              hasPermission(role.id, permission.id) ? 'Yes' : 'No'
            )
            .join(',') + '\n';
      });
    });

    return csv;
  };

  if (isLoading) {
    return (
      <div className='flex items-center justify-center min-h-[400px]'>
        <RefreshCw className='h-8 w-8 animate-spin text-blue-600' />
        <span className='ml-2 text-gray-600'>Loading permission matrix...</span>
      </div>
    );
  }

  if (isError || !matrixData) {
    return (
      <Card className='border-red-200'>
        <CardContent className='pt-6'>
          <div className='flex items-center justify-center text-red-600'>
            <AlertCircle className='h-8 w-8 mr-2' />
            <span>Failed to load permission matrix</span>
          </div>
          <div className='flex justify-center mt-4'>
            <Button onClick={() => refetch()} variant='outline'>
              <RefreshCw className='h-4 w-4 mr-2' />
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  const filteredRoles = getFilteredRoles();
  const filteredPermissions = getFilteredPermissions();

  return (
    <div className='space-y-6'>
      {/* Header */}
      <div className='flex items-center justify-between'>
        <div>
          <h1 className='text-3xl font-bold text-gray-900 flex items-center'>
            <Shield className='h-8 w-8 mr-3 text-blue-600' />
            Permission Matrix
          </h1>
          <p className='text-gray-600 mt-1'>
            Manage role permissions and access control
          </p>
        </div>

        <div className='flex items-center space-x-3'>
          <Button onClick={() => refetch()} variant='outline' size='sm'>
            <RefreshCw className='h-4 w-4 mr-2' />
            Refresh
          </Button>
          <Button onClick={exportMatrix} variant='outline' size='sm'>
            <Download className='h-4 w-4 mr-2' />
            Export CSV
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className='grid grid-cols-1 md:grid-cols-4 gap-4'>
        <Card>
          <CardContent className='pt-6'>
            <div className='flex items-center'>
              <Users className='h-8 w-8 text-blue-600' />
              <div className='ml-4'>
                <p className='text-sm font-medium text-gray-600'>Total Roles</p>
                <p className='text-2xl font-bold'>
                  {matrixData.summary.total_roles}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className='pt-6'>
            <div className='flex items-center'>
              <Shield className='h-8 w-8 text-green-600' />
              <div className='ml-4'>
                <p className='text-sm font-medium text-gray-600'>
                  Total Permissions
                </p>
                <p className='text-2xl font-bold'>
                  {matrixData.summary.total_permissions}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className='pt-6'>
            <div className='flex items-center'>
              <Settings className='h-8 w-8 text-gray-600' />
              <div className='ml-4'>
                <p className='text-sm font-medium text-gray-600'>
                  System Roles
                </p>
                <p className='text-2xl font-bold'>
                  {matrixData.summary.system_roles}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className='pt-6'>
            <div className='flex items-center'>
              <Users className='h-8 w-8 text-purple-600' />
              <div className='ml-4'>
                <p className='text-sm font-medium text-gray-600'>
                  Custom Roles
                </p>
                <p className='text-2xl font-bold'>
                  {matrixData.summary.custom_roles}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className='flex items-center'>
            <Filter className='h-5 w-5 mr-2' />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className='flex items-center space-x-4'>
            <div className='flex items-center space-x-2'>
              <label htmlFor='resource-filter' className='text-sm font-medium'>
                Resource:
              </label>
              <select
                id='resource-filter'
                className='flex h-10 w-[200px] rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500'
                value={selectedResource}
                onChange={e => setSelectedResource(e.target.value)}
              >
                <option value='all'>All Resources</option>
                {matrixData.permission_groups.map((group: PermissionGroup) => (
                  <option key={group.resource} value={group.resource}>
                    {group.resource}
                  </option>
                ))}
              </select>
            </div>

            <div className='flex items-center space-x-2'>
              <Checkbox
                id='show-system-roles'
                checked={showSystemRoles}
                onCheckedChange={setShowSystemRoles}
              />
              <label
                htmlFor='show-system-roles'
                className='text-sm font-medium'
              >
                Show system roles
              </label>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Permission Matrix */}
      <Card>
        <CardHeader>
          <CardTitle>Permission Matrix</CardTitle>
          <CardDescription>
            Click checkboxes to modify permissions for custom roles
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className='overflow-x-auto'>
            <table className='w-full border-collapse border border-gray-300'>
              <thead>
                <tr className='bg-gray-50'>
                  <th className='border border-gray-300 px-4 py-2 text-left font-medium'>
                    Resource
                  </th>
                  <th className='border border-gray-300 px-4 py-2 text-left font-medium'>
                    Permission
                  </th>
                  {filteredRoles.map((role: Role) => (
                    <th
                      key={role.id}
                      className='border border-gray-300 px-2 py-2 text-center font-medium min-w-[120px]'
                    >
                      <div className='flex flex-col items-center space-y-1'>
                        <span className='text-sm'>{role.display_name}</span>
                        {role.is_system && (
                          <Badge variant='secondary' className='text-xs'>
                            System
                          </Badge>
                        )}
                        {pendingChanges[role.id] && (
                          <div className='flex space-x-1'>
                            <Button
                              size='sm'
                              variant='outline'
                              className='h-6 px-2 text-xs'
                              onClick={() => handleSaveChanges(role.id)}
                              disabled={updateRolePermissions.isPending}
                            >
                              <CheckCircle className='h-3 w-3' />
                            </Button>
                            <Button
                              size='sm'
                              variant='outline'
                              className='h-6 px-2 text-xs'
                              onClick={() => handleCancelChanges(role.id)}
                              disabled={updateRolePermissions.isPending}
                            >
                              <X className='h-3 w-3' />
                            </Button>
                          </div>
                        )}
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filteredPermissions.map((group: PermissionGroup) =>
                  group.permissions.map(
                    (permission: Permission, index: number) => (
                      <tr key={permission.id} className='hover:bg-gray-50'>
                        {index === 0 && (
                          <td
                            className='border border-gray-300 px-4 py-2 font-medium bg-gray-50'
                            rowSpan={group.permissions.length}
                          >
                            {group.resource}
                          </td>
                        )}
                        <td className='border border-gray-300 px-4 py-2'>
                          <div>
                            <span className='font-medium'>
                              {permission.display_name}
                            </span>
                            {permission.action && (
                              <div className='text-xs text-gray-500'>
                                {permission.action} • {permission.scope}
                              </div>
                            )}
                          </div>
                        </td>
                        {filteredRoles.map((role: Role) => (
                          <td
                            key={`${role.id}-${permission.id}`}
                            className='border border-gray-300 px-2 py-2 text-center'
                          >
                            <Checkbox
                              checked={hasPermission(role.id, permission.id)}
                              onCheckedChange={() =>
                                handlePermissionToggle(role.id, permission.id)
                              }
                              disabled={
                                role.is_system ||
                                updateRolePermissions.isPending
                              }
                              className={
                                pendingChanges[role.id]
                                  ? 'border-orange-400'
                                  : ''
                              }
                            />
                          </td>
                        ))}
                      </tr>
                    )
                  )
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Legend */}
      <Card>
        <CardContent className='pt-6'>
          <div className='flex items-center space-x-6 text-sm text-gray-600'>
            <div className='flex items-center space-x-2'>
              <Checkbox checked disabled />
              <span>Permission granted</span>
            </div>
            <div className='flex items-center space-x-2'>
              <Checkbox disabled />
              <span>Permission not granted</span>
            </div>
            <div className='flex items-center space-x-2'>
              <Badge variant='secondary'>System</Badge>
              <span>System roles (read-only)</span>
            </div>
            <div className='flex items-center space-x-2'>
              <Checkbox className='border-orange-400' disabled />
              <span>Pending changes</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
