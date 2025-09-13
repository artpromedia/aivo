import {
  Zap,
  TrendingUp,
  Clock,
  AlertTriangle,
  Settings,
  BarChart3,
} from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';


/**
 * API Usage & Rate Limits Page
 * Provides monitoring and management of API consumption and rate limiting
 */
export default function APIUsagePage() {
  const handleViewMetrics = () => {
    // TODO: Implement API metrics viewing with API call
    alert('View API Metrics - API call needed');
  };

  const handleConfigureLimits = () => {
    // TODO: Implement rate limit configuration with API call
    alert('Configure Rate Limits - API call needed');
  };

  const handleManageQuotas = () => {
    // TODO: Implement quota management with API call
    alert('Manage API Quotas - API call needed');
  };

  const handleAnalyzeUsage = () => {
    // TODO: Implement usage analysis with API call
    alert('Analyze Usage Patterns - API call needed');
  };

  return (
    <div className='p-6 space-y-6'>
      <div className='flex items-center justify-between'>
        <div>
          <h1 className='text-3xl font-bold tracking-tight'>
            API Usage & Rate Limits
          </h1>
          <p className='text-muted-foreground'>
            Monitor API consumption, configure rate limits, and manage quotas
          </p>
        </div>
        <Button
          onClick={handleConfigureLimits}
          className='flex items-center gap-2'
        >
          <Settings className='h-4 w-4' />
          Configure Limits
        </Button>
      </div>

      {/* Quick Stats */}
      <div className='grid gap-4 md:grid-cols-2 lg:grid-cols-4'>
        <Card>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>
              Requests Today
            </CardTitle>
            <Zap className='h-4 w-4 text-muted-foreground' />
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold'>1.2M</div>
            <p className='text-xs text-muted-foreground'>+15% from yesterday</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>
              Rate Limit Hits
            </CardTitle>
            <AlertTriangle className='h-4 w-4 text-yellow-500' />
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold'>234</div>
            <p className='text-xs text-muted-foreground'>Last 24 hours</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>
              Avg Response Time
            </CardTitle>
            <Clock className='h-4 w-4 text-muted-foreground' />
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold'>142ms</div>
            <p className='text-xs text-muted-foreground'>-8ms from last hour</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>
              Quota Utilization
            </CardTitle>
            <TrendingUp className='h-4 w-4 text-muted-foreground' />
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold'>67%</div>
            <p className='text-xs text-muted-foreground'>Monthly quota used</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Actions */}
      <div className='grid gap-6 md:grid-cols-2'>
        <Card>
          <CardHeader>
            <CardTitle className='flex items-center gap-2'>
              <BarChart3 className='h-5 w-5' />
              Usage Analytics
            </CardTitle>
          </CardHeader>
          <CardContent className='space-y-4'>
            <p className='text-sm text-muted-foreground'>
              View detailed API usage metrics and performance analytics
            </p>
            <div className='flex gap-2'>
              <Button onClick={handleViewMetrics} size='sm'>
                View Metrics
              </Button>
              <Button variant='outline' size='sm'>
                Export Report
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className='flex items-center gap-2'>
              <Settings className='h-5 w-5' />
              Rate Limit Configuration
            </CardTitle>
          </CardHeader>
          <CardContent className='space-y-4'>
            <p className='text-sm text-muted-foreground'>
              Configure rate limits per endpoint, user, or API key
            </p>
            <div className='flex gap-2'>
              <Button onClick={handleConfigureLimits} size='sm'>
                Configure Limits
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
              <TrendingUp className='h-5 w-5' />
              Quota Management
            </CardTitle>
          </CardHeader>
          <CardContent className='space-y-4'>
            <p className='text-sm text-muted-foreground'>
              Manage API quotas and usage limits for different tiers
            </p>
            <div className='flex gap-2'>
              <Button onClick={handleManageQuotas} size='sm'>
                Manage Quotas
              </Button>
              <Button variant='outline' size='sm'>
                Usage Alerts
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className='flex items-center gap-2'>
              <Zap className='h-5 w-5' />
              Usage Analysis
            </CardTitle>
          </CardHeader>
          <CardContent className='space-y-4'>
            <p className='text-sm text-muted-foreground'>
              Analyze usage patterns and identify optimization opportunities
            </p>
            <div className='flex gap-2'>
              <Button onClick={handleAnalyzeUsage} size='sm'>
                Analyze Usage
              </Button>
              <Button variant='outline' size='sm'>
                Recommendations
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* API Endpoints Performance */}
      <Card>
        <CardHeader>
          <CardTitle>Top API Endpoints</CardTitle>
        </CardHeader>
        <CardContent>
          <div className='space-y-4'>
            <div className='flex items-center justify-between p-3 border rounded-lg'>
              <div className='flex items-center gap-3'>
                <div>
                  <span className='text-sm font-medium'>GET /api/devices</span>
                  <p className='text-xs text-muted-foreground'>
                    Device listing endpoint
                  </p>
                </div>
                <Badge variant='outline'>345K requests</Badge>
                <Badge variant='secondary'>150ms avg</Badge>
              </div>
              <div className='flex items-center gap-2'>
                <span className='text-sm text-green-600'>98.9% success</span>
                <Button variant='outline' size='sm'>
                  Configure
                </Button>
              </div>
            </div>
            <div className='flex items-center justify-between p-3 border rounded-lg'>
              <div className='flex items-center gap-3'>
                <div>
                  <span className='text-sm font-medium'>
                    POST /api/auth/login
                  </span>
                  <p className='text-xs text-muted-foreground'>
                    Authentication endpoint
                  </p>
                </div>
                <Badge variant='outline'>89K requests</Badge>
                <Badge variant='secondary'>45ms avg</Badge>
              </div>
              <div className='flex items-center gap-2'>
                <span className='text-sm text-green-600'>99.7% success</span>
                <Button variant='outline' size='sm'>
                  Configure
                </Button>
              </div>
            </div>
            <div className='flex items-center justify-between p-3 border rounded-lg'>
              <div className='flex items-center gap-3'>
                <div>
                  <span className='text-sm font-medium'>
                    PUT /api/devices/&#123;id&#125;
                  </span>
                  <p className='text-xs text-muted-foreground'>
                    Device update endpoint
                  </p>
                </div>
                <Badge variant='outline'>67K requests</Badge>
                <Badge variant='destructive'>890ms avg</Badge>
              </div>
              <div className='flex items-center gap-2'>
                <span className='text-sm text-red-600'>94.2% success</span>
                <Button variant='outline' size='sm'>
                  Optimize
                </Button>
              </div>
            </div>
            <div className='flex items-center justify-between p-3 border rounded-lg'>
              <div className='flex items-center gap-3'>
                <div>
                  <span className='text-sm font-medium'>
                    GET /api/users/&#123;id&#125;/profile
                  </span>
                  <p className='text-xs text-muted-foreground'>
                    User profile endpoint
                  </p>
                </div>
                <Badge variant='outline'>23K requests</Badge>
                <Badge variant='secondary'>67ms avg</Badge>
              </div>
              <div className='flex items-center gap-2'>
                <span className='text-sm text-green-600'>99.1% success</span>
                <Button variant='outline' size='sm'>
                  Configure
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
