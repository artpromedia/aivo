import {
  Database,
  Key,
  Shield,
  Plus,
  Eye,
  EyeOff,
  AlertTriangle,
} from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';


/**
 * Secrets & Keys Vault Page
 * Provides secure storage and management of API keys, certificates, and secrets
 */
export default function SecretsPage() {
  const handleCreateSecret = () => {
    // TODO: Implement secret creation with API call
    alert('Create Secret - API call needed');
  };

  const handleRotateKeys = () => {
    // TODO: Implement key rotation with API call
    alert('Rotate Keys - API call needed');
  };

  const handleManageAccess = () => {
    // TODO: Implement access control with API call
    alert('Manage Secret Access - API call needed');
  };

  const handleAuditSecrets = () => {
    // TODO: Implement secrets audit with API call
    alert('Audit Secrets Usage - API call needed');
  };

  return (
    <div className='p-6 space-y-6'>
      <div className='flex items-center justify-between'>
        <div>
          <h1 className='text-3xl font-bold tracking-tight'>
            Secrets & Keys Vault
          </h1>
          <p className='text-muted-foreground'>
            Secure storage and management of API keys, certificates, and secrets
          </p>
        </div>
        <Button
          onClick={handleCreateSecret}
          className='flex items-center gap-2'
        >
          <Plus className='h-4 w-4' />
          Add Secret
        </Button>
      </div>

      {/* Quick Stats */}
      <div className='grid gap-4 md:grid-cols-2 lg:grid-cols-4'>
        <Card>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>
              Stored Secrets
            </CardTitle>
            <Database className='h-4 w-4 text-muted-foreground' />
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold'>89</div>
            <p className='text-xs text-muted-foreground'>Active secrets</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>API Keys</CardTitle>
            <Key className='h-4 w-4 text-muted-foreground' />
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold'>34</div>
            <p className='text-xs text-muted-foreground'>Integration keys</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>Certificates</CardTitle>
            <Shield className='h-4 w-4 text-muted-foreground' />
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold'>12</div>
            <p className='text-xs text-muted-foreground'>SSL/TLS certs</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>Expiring Soon</CardTitle>
            <AlertTriangle className='h-4 w-4 text-yellow-500' />
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold'>3</div>
            <p className='text-xs text-muted-foreground'>Next 30 days</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Actions */}
      <div className='grid gap-6 md:grid-cols-2'>
        <Card>
          <CardHeader>
            <CardTitle className='flex items-center gap-2'>
              <Database className='h-5 w-5' />
              Secret Management
            </CardTitle>
          </CardHeader>
          <CardContent className='space-y-4'>
            <p className='text-sm text-muted-foreground'>
              Create, store, and manage encrypted secrets securely
            </p>
            <div className='flex gap-2'>
              <Button onClick={handleCreateSecret} size='sm'>
                Add Secret
              </Button>
              <Button variant='outline' size='sm'>
                Import Secrets
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className='flex items-center gap-2'>
              <Key className='h-5 w-5' />
              Key Rotation
            </CardTitle>
          </CardHeader>
          <CardContent className='space-y-4'>
            <p className='text-sm text-muted-foreground'>
              Automated and manual key rotation with rollback capabilities
            </p>
            <div className='flex gap-2'>
              <Button onClick={handleRotateKeys} size='sm'>
                Rotate Keys
              </Button>
              <Button variant='outline' size='sm'>
                Schedule Rotation
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className='flex items-center gap-2'>
              <Shield className='h-5 w-5' />
              Access Control
            </CardTitle>
          </CardHeader>
          <CardContent className='space-y-4'>
            <p className='text-sm text-muted-foreground'>
              Manage who can access, view, and modify secrets
            </p>
            <div className='flex gap-2'>
              <Button onClick={handleManageAccess} size='sm'>
                Manage Access
              </Button>
              <Button variant='outline' size='sm'>
                Access Policies
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className='flex items-center gap-2'>
              <Eye className='h-5 w-5' />
              Audit & Monitoring
            </CardTitle>
          </CardHeader>
          <CardContent className='space-y-4'>
            <p className='text-sm text-muted-foreground'>
              Track secret usage and monitor for unauthorized access
            </p>
            <div className='flex gap-2'>
              <Button onClick={handleAuditSecrets} size='sm'>
                View Audit Log
              </Button>
              <Button variant='outline' size='sm'>
                Usage Report
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Secrets List */}
      <Card>
        <CardHeader>
          <CardTitle>Secret Vault</CardTitle>
        </CardHeader>
        <CardContent>
          <div className='space-y-4'>
            <div className='flex items-center justify-between p-3 border rounded-lg'>
              <div className='flex items-center gap-3'>
                <Database className='h-4 w-4 text-muted-foreground' />
                <div>
                  <span className='text-sm font-medium'>
                    PostgreSQL Production
                  </span>
                  <p className='text-xs text-muted-foreground'>
                    Database connection string
                  </p>
                </div>
                <Badge variant='outline'>Database</Badge>
              </div>
              <div className='flex items-center gap-2'>
                <Button variant='ghost' size='sm'>
                  <EyeOff className='h-4 w-4' />
                </Button>
                <Button variant='outline' size='sm'>
                  Edit
                </Button>
              </div>
            </div>
            <div className='flex items-center justify-between p-3 border rounded-lg'>
              <div className='flex items-center gap-3'>
                <Key className='h-4 w-4 text-muted-foreground' />
                <div>
                  <span className='text-sm font-medium'>Stripe API Key</span>
                  <p className='text-xs text-muted-foreground'>
                    Payment processing key
                  </p>
                </div>
                <Badge variant='outline'>API Key</Badge>
              </div>
              <div className='flex items-center gap-2'>
                <Button variant='ghost' size='sm'>
                  <EyeOff className='h-4 w-4' />
                </Button>
                <Button variant='outline' size='sm'>
                  Edit
                </Button>
              </div>
            </div>
            <div className='flex items-center justify-between p-3 border rounded-lg'>
              <div className='flex items-center gap-3'>
                <Shield className='h-4 w-4 text-muted-foreground' />
                <div>
                  <span className='text-sm font-medium'>SSL Certificate</span>
                  <p className='text-xs text-muted-foreground'>
                    *.example.com wildcard cert
                  </p>
                </div>
                <Badge variant='destructive'>Expiring</Badge>
              </div>
              <div className='flex items-center gap-2'>
                <Button variant='ghost' size='sm'>
                  <EyeOff className='h-4 w-4' />
                </Button>
                <Button variant='outline' size='sm'>
                  Renew
                </Button>
              </div>
            </div>
            <div className='flex items-center justify-between p-3 border rounded-lg'>
              <div className='flex items-center gap-3'>
                <Key className='h-4 w-4 text-muted-foreground' />
                <div>
                  <span className='text-sm font-medium'>JWT Signing Key</span>
                  <p className='text-xs text-muted-foreground'>
                    Token signing secret
                  </p>
                </div>
                <Badge variant='outline'>JWT</Badge>
              </div>
              <div className='flex items-center gap-2'>
                <Button variant='ghost' size='sm'>
                  <EyeOff className='h-4 w-4' />
                </Button>
                <Button variant='outline' size='sm'>
                  Rotate
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
