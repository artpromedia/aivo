import {
  TrendingUp,
  Users,
  CreditCard,
  CheckCircle,
  Server,
  HelpCircle,
  Download,
  Eye,
  UserPlus,
  Settings,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  CardFooter,
} from '@/components/ui/card';
import { useDashboardSummary } from '@/hooks/useApi';
import { formatCurrency } from '@/lib/utils';

// Mock data for demonstration
const usageData = [
  { month: 'Jan', usage: 120, predictions: 89 },
  { month: 'Feb', usage: 190, predictions: 145 },
  { month: 'Mar', usage: 300, predictions: 234 },
  { month: 'Apr', usage: 500, predictions: 432 },
  { month: 'May', usage: 450, predictions: 398 },
  { month: 'Jun', usage: 620, predictions: 567 },
];

const namespaceData = [
  { name: 'Production', value: 45, color: '#8b5cf6' },
  { name: 'Staging', value: 25, color: '#a78bfa' },
  { name: 'Development', value: 20, color: '#c4b5fd' },
  { name: 'Testing', value: 10, color: '#ddd6fe' },
];

const analyticsData = [
  { period: 'Week 1', users: 245, sessions: 1200 },
  { period: 'Week 2', users: 289, sessions: 1456 },
  { period: 'Week 3', users: 320, sessions: 1678 },
  { period: 'Week 4', users: 378, sessions: 1890 },
];

export function Dashboard() {
  const { data: summary, isLoading: summaryLoading } = useDashboardSummary();

  const handleViewUsers = () => {
    window.location.href = '/users';
  };

  const handleManageSubscription = () => {
    window.location.href = '/subscriptions';
  };

  const handleViewBilling = () => {
    window.location.href = '/billing';
  };

  const handleManageTeam = () => {
    window.location.href = '/users?tab=team';
  };

  const handleManageNamespaces = () => {
    window.location.href = '/namespaces';
  };

  const handleViewAnalytics = () => {
    window.location.href = '/analytics';
  };

  const handleContactSupport = () => {
    window.location.href = '/support';
  };

  const handleDownloadReport = () => {
    // API call to generate and download usage report
    console.log('Downloading usage report...');
  };

  return (
    <div className='space-y-6'>
      {/* Header */}
      <div>
        <h1 className='text-3xl font-bold tracking-tight'>Dashboard</h1>
        <p className='text-muted-foreground'>
          Welcome back! Here's what's happening with your system.
        </p>
      </div>

      {/* Usage Summary Card */}
      <Card className='card-gradient'>
        <CardHeader>
          <div className='flex items-center justify-between'>
            <div>
              <CardTitle className='flex items-center gap-2'>
                <TrendingUp className='h-6 w-6' />
                Usage Summary
              </CardTitle>
              <CardDescription>
                Monthly platform usage and AI inference trends
              </CardDescription>
            </div>
            <Button onClick={handleDownloadReport} variant='outline' size='sm'>
              <Download className='h-4 w-4 mr-2' />
              Download Report
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className='h-80'>
            <ResponsiveContainer width='100%' height='100%'>
              <AreaChart data={usageData}>
                <CartesianGrid strokeDasharray='3 3' />
                <XAxis dataKey='month' />
                <YAxis />
                <Tooltip />
                <Area
                  type='monotone'
                  dataKey='usage'
                  stackId='1'
                  stroke='#8b5cf6'
                  fill='#8b5cf6'
                  fillOpacity={0.3}
                />
                <Area
                  type='monotone'
                  dataKey='predictions'
                  stackId='1'
                  stroke='#a78bfa'
                  fill='#a78bfa'
                  fillOpacity={0.3}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Stats Grid */}
      <div className='grid gap-4 md:grid-cols-2 lg:grid-cols-4'>
        {/* Current Subscription */}
        <Card>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>
              Current Subscription
            </CardTitle>
            <CreditCard className='h-4 w-4 text-muted-foreground' />
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold'>Pro Plan</div>
            <p className='text-xs text-muted-foreground'>
              {formatCurrency(299)} /month
            </p>
            <div className='mt-2'>
              <Button
                onClick={handleManageSubscription}
                size='sm'
                className='w-full'
              >
                Manage Plan
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Total Users */}
        <Card>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>Total Users</CardTitle>
            <Users className='h-4 w-4 text-muted-foreground' />
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold'>
              {summaryLoading ? '...' : summary?.totalUsers || 1234}
            </div>
            <p className='text-xs text-muted-foreground'>
              +12% from last month
            </p>
            <div className='mt-2'>
              <Button
                onClick={handleViewUsers}
                variant='outline'
                size='sm'
                className='w-full'
              >
                <Eye className='h-4 w-4 mr-2' />
                View All
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Active Licenses */}
        <Card>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>
              Active Licenses
            </CardTitle>
            <CheckCircle className='h-4 w-4 text-muted-foreground' />
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold'>
              {summaryLoading ? '...' : summary?.activeSubscriptions || 89}
            </div>
            <p className='text-xs text-muted-foreground'>78/100 seats used</p>
            <div className='mt-2'>
              <Button
                onClick={handleViewUsers}
                variant='outline'
                size='sm'
                className='w-full'
              >
                <UserPlus className='h-4 w-4 mr-2' />
                Add Users
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Monthly Revenue */}
        <Card>
          <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
            <CardTitle className='text-sm font-medium'>
              Monthly Revenue
            </CardTitle>
            <TrendingUp className='h-4 w-4 text-muted-foreground' />
          </CardHeader>
          <CardContent>
            <div className='text-2xl font-bold'>
              {summaryLoading
                ? '...'
                : formatCurrency(summary?.monthlyRevenue || 23400)}
            </div>
            <p className='text-xs text-muted-foreground'>
              +18% from last month
            </p>
            <div className='mt-2'>
              <Button
                onClick={handleViewBilling}
                variant='outline'
                size='sm'
                className='w-full'
              >
                View Billing
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Bottom Grid */}
      <div className='grid gap-6 md:grid-cols-2 lg:grid-cols-3'>
        {/* Team Management */}
        <Card>
          <CardHeader>
            <CardTitle>Team Management</CardTitle>
            <CardDescription>Quick actions for user roles</CardDescription>
          </CardHeader>
          <CardContent className='space-y-3'>
            <div className='flex justify-between items-center'>
              <span className='text-sm'>Staff Members</span>
              <span className='font-medium'>24</span>
            </div>
            <div className='flex justify-between items-center'>
              <span className='text-sm'>District Admins</span>
              <span className='font-medium'>8</span>
            </div>
            <div className='flex justify-between items-center'>
              <span className='text-sm'>Pending Approvals</span>
              <span className='font-medium text-orange-600'>3</span>
            </div>
          </CardContent>
          <CardFooter>
            <Button onClick={handleManageTeam} className='w-full'>
              <Settings className='h-4 w-4 mr-2' />
              Manage Team
            </Button>
          </CardFooter>
        </Card>

        {/* Namespaces Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Namespaces</CardTitle>
            <CardDescription>Resource distribution overview</CardDescription>
          </CardHeader>
          <CardContent>
            <div className='h-40'>
              <ResponsiveContainer width='100%' height='100%'>
                <PieChart>
                  <Pie
                    data={namespaceData}
                    cx='50%'
                    cy='50%'
                    innerRadius={40}
                    outerRadius={60}
                    dataKey='value'
                  >
                    {namespaceData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className='mt-2 space-y-1'>
              {namespaceData.map(item => (
                <div
                  key={item.name}
                  className='flex items-center gap-2 text-xs'
                >
                  <div
                    className='w-2 h-2 rounded-full'
                    style={{ backgroundColor: item.color }}
                  />
                  <span>
                    {item.name}: {item.value}%
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
          <CardFooter>
            <Button
              onClick={handleManageNamespaces}
              variant='outline'
              className='w-full'
            >
              <Server className='h-4 w-4 mr-2' />
              Manage Namespaces
            </Button>
          </CardFooter>
        </Card>

        {/* Usage Analytics */}
        <Card>
          <CardHeader>
            <CardTitle>Usage Analytics</CardTitle>
            <CardDescription>Weekly user activity trends</CardDescription>
          </CardHeader>
          <CardContent>
            <div className='h-40'>
              <ResponsiveContainer width='100%' height='100%'>
                <BarChart data={analyticsData}>
                  <CartesianGrid strokeDasharray='3 3' />
                  <XAxis dataKey='period' />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey='users' fill='#8b5cf6' />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
          <CardFooter>
            <Button
              onClick={handleViewAnalytics}
              variant='outline'
              className='w-full'
            >
              <TrendingUp className='h-4 w-4 mr-2' />
              View Analytics
            </Button>
          </CardFooter>
        </Card>
      </div>

      {/* Support & Resources */}
      <Card>
        <CardHeader>
          <CardTitle className='flex items-center gap-2'>
            <HelpCircle className='h-5 w-5' />
            Support & Resources
          </CardTitle>
          <CardDescription>
            Get help and access important resources
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className='grid gap-4 md:grid-cols-3'>
            <Button
              onClick={handleContactSupport}
              variant='outline'
              className='h-20 flex-col'
            >
              <HelpCircle className='h-6 w-6 mb-2' />
              <span>Contact Support</span>
            </Button>
            <Button
              onClick={() => window.open('https://docs.aivo.ai', '_blank')}
              variant='outline'
              className='h-20 flex-col'
            >
              <Download className='h-6 w-6 mb-2' />
              <span>Documentation</span>
            </Button>
            <Button
              onClick={() => window.open('https://status.aivo.ai', '_blank')}
              variant='outline'
              className='h-20 flex-col'
            >
              <Server className='h-6 w-6 mb-2' />
              <span>System Status</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
