import {
  Users,
  Key,
  Shield,
  Plus,
  Settings,
  AlertTriangle,
} from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';


/**
 * Identity & Access Management Page
 * Provides centralized IAM controls for enterprise users
 */
export default function IdentityPage() {
  const handleCreateUser = () => {
    // TODO: Implement user creation with API call
    alert('Create User - API call needed');
  };

  const handleManageRoles = () => {
    // TODO: Implement role management with API call
    alert('Manage Roles - API call needed');
  };

  const handleSecuritySettings = () => {
    // TODO: Implement security settings with API call
    alert('Security Settings - API call needed');
  };

  const handleViewAuditLogs = () => {
    // TODO: Implement audit log viewing with API call
    alert('View Audit Logs - API call needed');
  };

  return (
    <div className='p-6 space-y-6'>
      <div className='flex items-center justify-between'>
        <div>
          <h1 className='text-3xl font-bold tracking-tight'>
            Identity & Access Management
          </h1>
          <p className='text-muted-foreground'>
            Manage users, roles, and access controls across your organization
          </p>
        </div>
        <Button onClick={handleCreateUser} className='flex items-center gap-2'>
          <Plus className='h-4 w-4' />
          Create User
        </Button>
      </div>

      {/* Quick Stats */}
      <div className='grid gap-4 md:grid-cols-2 lg:grid-cols-4'>
        <Card>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>Active Users</CardTitle>
            <Users className='h-4 w-4 text-muted-foreground' />
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold'>2,847</div>
            <p className='text-xs text-muted-foreground'>
              +12% from last month
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>Active Roles</CardTitle>
            <Key className='h-4 w-4 text-muted-foreground' />
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold'>23</div>
            <p className='text-xs text-muted-foreground'>
              Custom roles configured
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>
              Security Alerts
            </CardTitle>
            <AlertTriangle className='h-4 w-4 text-yellow-500' />
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold'>3</div>
            <p className='text-xs text-muted-foreground'>
              Require immediate attention
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>SSO Providers</CardTitle>
            <Shield className='h-4 w-4 text-muted-foreground' />
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold'>4</div>
            <p className='text-xs text-muted-foreground'>
              Identity providers active
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Actions */}
      <div className='grid gap-6 md:grid-cols-2'>
        <Card>
          <CardHeader>
            <CardTitle className='flex items-center gap-2'>
              <Users className='h-5 w-5' />
              User Management
            </CardTitle>
          </CardHeader>
          <CardContent className='space-y-4'>
            <p className='text-sm text-muted-foreground'>
              Create, edit, and manage user accounts and their permissions
            </p>
            <div className='flex gap-2'>
              <Button onClick={handleCreateUser} size='sm'>
                Create User
              </Button>
              <Button variant='outline' size='sm'>
                Import Users
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className='flex items-center gap-2'>
              <Key className='h-5 w-5' />
              Role & Permission Management
            </CardTitle>
          </CardHeader>
          <CardContent className='space-y-4'>
            <p className='text-sm text-muted-foreground'>
              Define roles and assign granular permissions to control access
            </p>
            <div className='flex gap-2'>
              <Button onClick={handleManageRoles} size='sm'>
                Manage Roles
              </Button>
              <Button variant='outline' size='sm'>
                Create Role
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className='flex items-center gap-2'>
              <Shield className='h-5 w-5' />
              Security Configuration
            </CardTitle>
          </CardHeader>
          <CardContent className='space-y-4'>
            <p className='text-sm text-muted-foreground'>
              Configure MFA, password policies, and SSO integrations
            </p>
            <div className='flex gap-2'>
              <Button onClick={handleSecuritySettings} size='sm'>
                Security Settings
              </Button>
              <Button variant='outline' size='sm'>
                SSO Setup
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className='flex items-center gap-2'>
              <Settings className='h-5 w-5' />
              Audit & Compliance
            </CardTitle>
          </CardHeader>
          <CardContent className='space-y-4'>
            <p className='text-sm text-muted-foreground'>
              Monitor access logs and ensure compliance requirements
            </p>
            <div className='flex gap-2'>
              <Button onClick={handleViewAuditLogs} size='sm'>
                Audit Logs
              </Button>
              <Button variant='outline' size='sm'>
                Compliance Report
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <div className='space-y-4'>
            <div className='flex items-center justify-between'>
              <div className='flex items-center gap-2'>
                <Badge variant='outline'>User Created</Badge>
                <span className='text-sm'>john.doe@company.com</span>
              </div>
              <span className='text-xs text-muted-foreground'>2 hours ago</span>
            </div>
            <div className='flex items-center justify-between'>
              <div className='flex items-center gap-2'>
                <Badge variant='outline'>Role Updated</Badge>
                <span className='text-sm'>Admin role permissions modified</span>
              </div>
              <span className='text-xs text-muted-foreground'>4 hours ago</span>
            </div>
            <div className='flex items-center justify-between'>
              <div className='flex items-center gap-2'>
                <Badge variant='outline'>Security Alert</Badge>
                <span className='text-sm'>Failed login attempts detected</span>
              </div>
              <span className='text-xs text-muted-foreground'>6 hours ago</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
