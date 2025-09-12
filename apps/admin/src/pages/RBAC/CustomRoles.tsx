import {
  Plus,
  Edit,
  Trash2,
  Shield,
  Users,
  Settings,
  Save,
  X,
  RefreshCw,
  AlertCircle,
  CheckCircle,
} from 'lucide-react';
import { useState } from 'react';

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
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  useRoles,
  usePermissions,
  useCreateCustomRole,
  useUpdateRole,
  useDeleteRole,
  useUpdateRolePermissions,
} from '@/hooks/useRBAC';

interface CustomRolesProps {
  tenantId?: string;
}

interface RoleFormData {
  name: string;
  displayName: string;
  description: string;
}

interface Permission {
  id: string;
  name: string;
  display_name: string;
  resource: string;
  action: string;
  scope: string;
}

interface PermissionGroup {
  resource: string;
  permissions: Permission[];
}

interface Role {
  id: string;
  name: string;
  display_name: string;
  description?: string;
  is_system: boolean;
  is_active?: boolean;
  user_count?: number;
  permission_count?: number;
  can_edit?: boolean;
  can_delete?: boolean;
  permissions?: Permission[];
}

interface RolesData {
  roles: Role[];
}

interface PermissionsData {
  grouped_permissions: PermissionGroup[];
}

export default function CustomRoles({ tenantId }: CustomRolesProps) {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingRole, setEditingRole] = useState<string | null>(null);
  const [roleFormData, setRoleFormData] = useState<RoleFormData>({
    name: '',
    displayName: '',
    description: '',
  });
  const [selectedPermissions, setSelectedPermissions] = useState<Set<string>>(
    new Set()
  );
  const [errors, setErrors] = useState<Record<string, string>>({});

  // API hooks
  const {
    data: rolesData,
    isLoading: rolesLoading,
    refetch: refetchRoles,
  } = useRoles(tenantId, true) as {
    data: { data: RolesData } | undefined;
    isLoading: boolean;
    refetch: () => void;
  };
  const { data: permissionsData, isLoading: permissionsLoading } =
    usePermissions(tenantId) as {
      data: { data: PermissionsData } | undefined;
      isLoading: boolean;
    };

  const createRoleMutation = useCreateCustomRole();
  const updateRoleMutation = useUpdateRole();
  const deleteRoleMutation = useDeleteRole();
  const updatePermissionsMutation = useUpdateRolePermissions();

  const handleCreateRole = async () => {
    setErrors({});

    // Validation
    if (!roleFormData.name.trim()) {
      setErrors(prev => ({ ...prev, name: 'Role name is required' }));
      return;
    }

    if (!roleFormData.displayName.trim()) {
      setErrors(prev => ({ ...prev, displayName: 'Display name is required' }));
      return;
    }

    try {
      await createRoleMutation.mutateAsync({
        name: roleFormData.name,
        displayName: roleFormData.displayName,
        description: roleFormData.description,
        tenantId,
      });

      // Reset form
      setRoleFormData({ name: '', displayName: '', description: '' });
      setSelectedPermissions(new Set());
      setShowCreateForm(false);

      await refetchRoles();
       
    } catch (error) {
      setErrors({ form: 'Failed to create role. Please try again.' });
    }
  };

  const handleEditRole = (roleId: string) => {
    const role = rolesData?.data.roles.find((r: Role) => r.id === roleId);
    if (!role) return;

    setEditingRole(roleId);
    setRoleFormData({
      name: role.name,
      displayName: role.display_name,
      description: role.description || '',
    });

    // Set current permissions
    const currentPermissions = new Set(
      role.permissions?.map((p: Permission) => p.id) || []
    );
    setSelectedPermissions(currentPermissions);
  };

  const handleSaveRole = async (roleId: string) => {
    setErrors({});

    try {
      // Update role details
      await updateRoleMutation.mutateAsync({
        roleId,
        updates: {
          display_name: roleFormData.displayName,
          description: roleFormData.description,
        },
        tenantId,
      });

      // Update permissions
      await updatePermissionsMutation.mutateAsync({
        roleId,
        permissionIds: Array.from(selectedPermissions),
        tenantId,
      });

      setEditingRole(null);
      await refetchRoles();
       
    } catch (error) {
      setErrors({ form: 'Failed to update role. Please try again.' });
    }
  };

  const handleDeleteRole = async (roleId: string) => {
    if (!window.confirm('Are you sure you want to delete this role?')) {
      return;
    }

    try {
      await deleteRoleMutation.mutateAsync({ roleId, tenantId });
      await refetchRoles();
       
    } catch (error) {
      setErrors({ form: 'Failed to delete role. Please try again.' });
    }
  };

  const handlePermissionToggle = (permissionId: string) => {
    setSelectedPermissions(prev => {
      const newSet = new Set(prev);
      if (newSet.has(permissionId)) {
        newSet.delete(permissionId);
      } else {
        newSet.add(permissionId);
      }
      return newSet;
    });
  };

  const cancelEdit = () => {
    setEditingRole(null);
    setRoleFormData({ name: '', displayName: '', description: '' });
    setSelectedPermissions(new Set());
    setErrors({});
  };

  const cancelCreate = () => {
    setShowCreateForm(false);
    setRoleFormData({ name: '', displayName: '', description: '' });
    setSelectedPermissions(new Set());
    setErrors({});
  };

  if (rolesLoading || permissionsLoading) {
    return (
      <div className='flex items-center justify-center min-h-[400px]'>
        <RefreshCw className='h-8 w-8 animate-spin text-blue-600' />
        <span className='ml-2 text-gray-600'>
          Loading roles and permissions...
        </span>
      </div>
    );
  }

  const roles = rolesData?.data.roles || [];
  const customRoles = roles.filter((role: Role) => !role.is_system);
  const permissionGroups = permissionsData?.data.grouped_permissions || [];

  return (
    <div className='space-y-6'>
      {/* Header */}
      <div className='flex items-center justify-between'>
        <div>
          <h1 className='text-3xl font-bold text-gray-900 flex items-center'>
            <Shield className='h-8 w-8 mr-3 text-blue-600' />
            Custom Roles
          </h1>
          <p className='text-gray-600 mt-1'>
            Create and manage custom roles with specific permissions
          </p>
        </div>

        <Button
          onClick={() => setShowCreateForm(true)}
          disabled={showCreateForm || editingRole !== null}
        >
          <Plus className='h-4 w-4 mr-2' />
          Create Role
        </Button>
      </div>

      {/* Error Alert */}
      {errors.form && (
        <Card className='border-red-200 bg-red-50'>
          <CardContent className='pt-6'>
            <div className='flex items-center text-red-700'>
              <AlertCircle className='h-5 w-5 mr-2' />
              <span>{errors.form}</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Summary Stats */}
      <div className='grid grid-cols-1 md:grid-cols-3 gap-4'>
        <Card>
          <CardContent className='pt-6'>
            <div className='flex items-center'>
              <Users className='h-8 w-8 text-blue-600' />
              <div className='ml-4'>
                <p className='text-sm font-medium text-gray-600'>
                  Custom Roles
                </p>
                <p className='text-2xl font-bold'>{customRoles.length}</p>
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
                  {roles.length - customRoles.length}
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
                  Available Permissions
                </p>
                <p className='text-2xl font-bold'>
                  {permissionGroups.reduce(
                    (sum: number, group: PermissionGroup) =>
                      sum + group.permissions.length,
                    0
                  )}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Create Role Form */}
      {showCreateForm && (
        <Card>
          <CardHeader>
            <CardTitle>Create New Role</CardTitle>
            <CardDescription>
              Define a new custom role with specific permissions
            </CardDescription>
          </CardHeader>
          <CardContent className='space-y-6'>
            <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
              <div className='space-y-2'>
                <Label htmlFor='role-name'>Role Name</Label>
                <Input
                  id='role-name'
                  value={roleFormData.name}
                  onChange={e =>
                    setRoleFormData(prev => ({ ...prev, name: e.target.value }))
                  }
                  placeholder='e.g., content_manager'
                  className={errors.name ? 'border-red-500' : ''}
                />
                {errors.name && (
                  <p className='text-sm text-red-600'>{errors.name}</p>
                )}
              </div>

              <div className='space-y-2'>
                <Label htmlFor='display-name'>Display Name</Label>
                <Input
                  id='display-name'
                  value={roleFormData.displayName}
                  onChange={e =>
                    setRoleFormData(prev => ({
                      ...prev,
                      displayName: e.target.value,
                    }))
                  }
                  placeholder='e.g., Content Manager'
                  className={errors.displayName ? 'border-red-500' : ''}
                />
                {errors.displayName && (
                  <p className='text-sm text-red-600'>{errors.displayName}</p>
                )}
              </div>
            </div>

            <div className='space-y-2'>
              <Label htmlFor='description'>Description (Optional)</Label>
              <Input
                id='description'
                value={roleFormData.description}
                onChange={e =>
                  setRoleFormData(prev => ({
                    ...prev,
                    description: e.target.value,
                  }))
                }
                placeholder='Brief description of the role'
              />
            </div>

            {/* Permissions Selection */}
            <div className='space-y-4'>
              <Label>Permissions</Label>
              <div className='space-y-4 max-h-96 overflow-y-auto border rounded-md p-4'>
                {permissionGroups.map((group: PermissionGroup) => (
                  <div key={group.resource} className='space-y-2'>
                    <h4 className='font-medium text-gray-900 capitalize'>
                      {group.resource}
                    </h4>
                    <div className='grid grid-cols-1 md:grid-cols-2 gap-2 ml-4'>
                      {group.permissions.map((permission: Permission) => (
                        <div
                          key={permission.id}
                          className='flex items-center space-x-2'
                        >
                          <Checkbox
                            id={`create-${permission.id}`}
                            checked={selectedPermissions.has(permission.id)}
                            onCheckedChange={() =>
                              handlePermissionToggle(permission.id)
                            }
                          />
                          <label
                            htmlFor={`create-${permission.id}`}
                            className='text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70'
                          >
                            {permission.display_name}
                          </label>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className='flex justify-end space-x-2'>
              <Button variant='outline' onClick={cancelCreate}>
                <X className='h-4 w-4 mr-2' />
                Cancel
              </Button>
              <Button
                onClick={handleCreateRole}
                disabled={createRoleMutation.isPending}
              >
                <Save className='h-4 w-4 mr-2' />
                {createRoleMutation.isPending ? 'Creating...' : 'Create Role'}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Roles Table */}
      <Card>
        <CardHeader>
          <CardTitle>Existing Roles</CardTitle>
          <CardDescription>
            Manage your custom roles and their permissions
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Role</TableHead>
                <TableHead>Description</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Users</TableHead>
                <TableHead>Permissions</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {roles.map((role: Role) => (
                <TableRow key={role.id}>
                  <TableCell>
                    {editingRole === role.id ? (
                      <div className='space-y-2'>
                        <Input
                          value={roleFormData.displayName}
                          onChange={e =>
                            setRoleFormData(prev => ({
                              ...prev,
                              displayName: e.target.value,
                            }))
                          }
                          className='w-40'
                        />
                        <Input
                          value={roleFormData.description}
                          onChange={e =>
                            setRoleFormData(prev => ({
                              ...prev,
                              description: e.target.value,
                            }))
                          }
                          placeholder='Description'
                          className='w-40'
                        />
                      </div>
                    ) : (
                      <div>
                        <div className='font-medium'>{role.display_name}</div>
                        <div className='text-sm text-gray-500'>
                          {role.description}
                        </div>
                      </div>
                    )}
                  </TableCell>
                  <TableCell>
                    <div className='text-sm text-gray-600'>{role.name}</div>
                  </TableCell>
                  <TableCell>
                    <Badge variant={role.is_system ? 'secondary' : 'default'}>
                      {role.is_system ? 'System' : 'Custom'}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant={role.is_active ? 'default' : 'secondary'}>
                      {role.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <span className='text-sm'>{role.user_count || 0}</span>
                  </TableCell>
                  <TableCell>
                    {editingRole === role.id ? (
                      <div className='max-h-40 overflow-y-auto space-y-2'>
                        {permissionGroups.map((group: PermissionGroup) => (
                          <div key={group.resource} className='space-y-1'>
                            <div className='text-xs font-medium text-gray-600 capitalize'>
                              {group.resource}
                            </div>
                            <div className='space-y-1 ml-2'>
                              {group.permissions.map(
                                (permission: Permission) => (
                                  <div
                                    key={permission.id}
                                    className='flex items-center space-x-1'
                                  >
                                    <Checkbox
                                      id={`edit-${permission.id}`}
                                      checked={selectedPermissions.has(
                                        permission.id
                                      )}
                                      onCheckedChange={() =>
                                        handlePermissionToggle(permission.id)
                                      }
                                    />
                                    <label
                                      htmlFor={`edit-${permission.id}`}
                                      className='text-xs'
                                    >
                                      {permission.display_name}
                                    </label>
                                  </div>
                                )
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <span className='text-sm'>
                        {role.permission_count || 0} permissions
                      </span>
                    )}
                  </TableCell>
                  <TableCell>
                    {editingRole === role.id ? (
                      <div className='flex space-x-1'>
                        <Button
                          size='sm'
                          variant='outline'
                          onClick={() => handleSaveRole(role.id)}
                          disabled={
                            updateRoleMutation.isPending ||
                            updatePermissionsMutation.isPending
                          }
                        >
                          <CheckCircle className='h-4 w-4' />
                        </Button>
                        <Button
                          size='sm'
                          variant='outline'
                          onClick={cancelEdit}
                        >
                          <X className='h-4 w-4' />
                        </Button>
                      </div>
                    ) : (
                      <div className='flex space-x-1'>
                        {role.can_edit && (
                          <Button
                            size='sm'
                            variant='outline'
                            onClick={() => handleEditRole(role.id)}
                            disabled={editingRole !== null || showCreateForm}
                          >
                            <Edit className='h-4 w-4' />
                          </Button>
                        )}
                        {role.can_delete && (
                          <Button
                            size='sm'
                            variant='outline'
                            onClick={() => handleDeleteRole(role.id)}
                            disabled={
                              deleteRoleMutation.isPending ||
                              editingRole !== null ||
                              showCreateForm
                            }
                            className='text-red-600 hover:text-red-700'
                          >
                            <Trash2 className='h-4 w-4' />
                          </Button>
                        )}
                      </div>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
