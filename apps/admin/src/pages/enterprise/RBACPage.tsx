import { Key, Shield, Users, Plus, Settings, AlertCircle } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';


/**
 * RBAC & Permissions Management Page
 * Provides role-based access control and permission management
 */
export default function RBACPage() {
  const handleCreateRole = () => {
    // TODO: Implement role creation with API call
    alert('Create Role - API call needed');
  };

  const handleAssignPermissions = () => {
    // TODO: Implement permission assignment with API call
    alert('Assign Permissions - API call needed');
  };

  const handleManageMatrix = () => {
    // TODO: Implement permission matrix management with API call
    alert('Manage Permission Matrix - API call needed');
  };

  const handleAuditAccess = () => {
    // TODO: Implement access audit with API call
    alert('Audit Access Rights - API call needed');
  };

  return (
    <div className='p-6 space-y-6'>
      <div className='flex items-center justify-between'>
        <div>
          <h1 className='text-3xl font-bold tracking-tight'>
            RBAC & Permissions
          </h1>
          <p className='text-muted-foreground'>
            Manage role-based access control and granular permissions
          </p>
        </div>
        <Button onClick={handleCreateRole} className='flex items-center gap-2'>
          <Plus className='h-4 w-4' />
          Create Role
        </Button>
      </div>

      {/* Quick Stats */}
      <div className='grid gap-4 md:grid-cols-2 lg:grid-cols-4'>
        <Card>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>Active Roles</CardTitle>
            <Key className='h-4 w-4 text-muted-foreground' />
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold'>23</div>
            <p className='text-xs text-muted-foreground'>+2 new this month</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>Permissions</CardTitle>
            <Shield className='h-4 w-4 text-muted-foreground' />
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold'>156</div>
            <p className='text-xs text-muted-foreground'>
              Granular permissions
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>
              Users Assigned
            </CardTitle>
            <Users className='h-4 w-4 text-muted-foreground' />
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold'>2,847</div>
            <p className='text-xs text-muted-foreground'>Across all roles</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>
              Access Violations
            </CardTitle>
            <AlertCircle className='h-4 w-4 text-red-500' />
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold'>7</div>
            <p className='text-xs text-muted-foreground'>This week</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Actions */}
      <div className='grid gap-6 md:grid-cols-2'>
        <Card>
          <CardHeader>
            <CardTitle className='flex items-center gap-2'>
              <Key className='h-5 w-5' />
              Role Management
            </CardTitle>
          </CardHeader>
          <CardContent className='space-y-4'>
            <p className='text-sm text-muted-foreground'>
              Create and manage custom roles with specific permission sets
            </p>
            <div className='flex gap-2'>
              <Button onClick={handleCreateRole} size='sm'>
                Create Role
              </Button>
              <Button variant='outline' size='sm'>
                Import Roles
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className='flex items-center gap-2'>
              <Shield className='h-5 w-5' />
              Permission Assignment
            </CardTitle>
          </CardHeader>
          <CardContent className='space-y-4'>
            <p className='text-sm text-muted-foreground'>
              Assign granular permissions to roles and manage access levels
            </p>
            <div className='flex gap-2'>
              <Button onClick={handleAssignPermissions} size='sm'>
                Assign Permissions
              </Button>
              <Button variant='outline' size='sm'>
                Bulk Update
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className='flex items-center gap-2'>
              <Settings className='h-5 w-5' />
              Permission Matrix
            </CardTitle>
          </CardHeader>
          <CardContent className='space-y-4'>
            <p className='text-sm text-muted-foreground'>
              View and manage the complete role-permission matrix
            </p>
            <div className='flex gap-2'>
              <Button onClick={handleManageMatrix} size='sm'>
                View Matrix
              </Button>
              <Button variant='outline' size='sm'>
                Export Matrix
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className='flex items-center gap-2'>
              <AlertCircle className='h-5 w-5' />
              Access Audit
            </CardTitle>
          </CardHeader>
          <CardContent className='space-y-4'>
            <p className='text-sm text-muted-foreground'>
              Monitor access patterns and identify potential security issues
            </p>
            <div className='flex gap-2'>
              <Button onClick={handleAuditAccess} size='sm'>
                Audit Access
              </Button>
              <Button variant='outline' size='sm'>
                Security Report
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Active Roles Table */}
      <Card>
        <CardHeader>
          <CardTitle>Active Roles</CardTitle>
        </CardHeader>
        <CardContent>
          <div className='space-y-4'>
            <div className='flex items-center justify-between p-3 border rounded-lg'>
              <div className='flex items-center gap-3'>
                <Badge variant='default'>Administrator</Badge>
                <span className='text-sm font-medium'>Full system access</span>
                <span className='text-xs text-muted-foreground'>12 users</span>
              </div>
              <Button variant='outline' size='sm'>
                Edit
              </Button>
            </div>
            <div className='flex items-center justify-between p-3 border rounded-lg'>
              <div className='flex items-center gap-3'>
                <Badge variant='secondary'>Fleet Manager</Badge>
                <span className='text-sm font-medium'>
                  Device and fleet management
                </span>
                <span className='text-xs text-muted-foreground'>45 users</span>
              </div>
              <Button variant='outline' size='sm'>
                Edit
              </Button>
            </div>
            <div className='flex items-center justify-between p-3 border rounded-lg'>
              <div className='flex items-center gap-3'>
                <Badge variant='outline'>Support Agent</Badge>
                <span className='text-sm font-medium'>
                  Read-only access with limited actions
                </span>
                <span className='text-xs text-muted-foreground'>23 users</span>
              </div>
              <Button variant='outline' size='sm'>
                Edit
              </Button>
            </div>
            <div className='flex items-center justify-between p-3 border rounded-lg'>
              <div className='flex items-center gap-3'>
                <Badge variant='outline'>Viewer</Badge>
                <span className='text-sm font-medium'>
                  Read-only dashboard access
                </span>
                <span className='text-xs text-muted-foreground'>156 users</span>
              </div>
              <Button variant='outline' size='sm'>
                Edit
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
